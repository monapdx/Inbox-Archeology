from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ia_constants import tier_from_total


def recip_class(sent: int, recv: int) -> str:
    if recv == 0:
        return "NO_RECEIVE"
    r = sent / recv
    if r > 1.5:
        return "MOSTLY_ME"
    if r < 0.67:
        return "MOSTLY_THEM"
    return "BALANCED"


def normalize_email_label(email: str, hide: bool) -> str:
    if not isinstance(email, str):
        return ""
    if not hide:
        return email
    if "@" in email:
        _, domain = email.split("@", 1)
        return "●●●@" + domain
    return "●●●"


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        st.error(f"Missing file: {path}")
        st.stop()
    return pd.read_csv(path)


def resolve_output_dir(explicit_out_dir: str | os.PathLike[str] | None = None) -> Path:
    this_dir = Path(__file__).resolve().parent
    default_output_dir = this_dir / "output"

    if explicit_out_dir:
        return Path(explicit_out_dir).resolve()

    env_override = os.environ.get("INBOX_ARCH_OUTPUT_DIR")
    if env_override:
        return Path(env_override).resolve()

    return default_output_dir.resolve()


def build_ego_graph_figure(
    relationships_df: pd.DataFrame,
    hide_labels: bool = True,
    top_n: int = 40,
) -> go.Figure:
    """
    Ego network only: current pipeline gives direct you<->contact relationships,
    not contact-to-contact edges.
    """
    df = relationships_df.sort_values("total_messages", ascending=False).head(top_n).copy()

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Relationship Graph",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[dict(text="No graph data for current filters.", showarrow=False)],
            height=650,
        )
        return fig

    tier_colors = {
        "CORE": "#6C63FF",
        "RECURRING": "#00B894",
        "PERIPHERAL": "#B2BEC3",
    }

    center_x, center_y = 0.0, 0.0
    n = len(df)

    max_total = max(int(df["total_messages"].max()), 1)

    node_x = [center_x]
    node_y = [center_y]
    node_text = ["You"]
    node_size = [38]
    node_color = ["#222222"]
    hover_text = ["You"]

    edge_x = []
    edge_y = []

    if n == 1:
        angles = [0.0]
    else:
        angles = [2 * math.pi * i / n for i in range(n)]

    for angle, (_, row) in zip(angles, df.iterrows()):
        total = int(row["total_messages"])
        sent = int(row["sent_by_me"])
        recv = int(row["received_by_me"])
        label = row["label"]

        strength = total / max_total
        radius = 0.38 + (1 - strength) * 0.42

        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

        edge_x.extend([center_x, x, None])
        edge_y.extend([center_y, y, None])

        node_x.append(x)
        node_y.append(y)
        node_text.append(label)
        node_size.append(12 + 22 * math.sqrt(total / max_total))
        node_color.append(tier_colors.get(row["tier"], "#999999"))

        hover_text.append(
            "<br>".join(
                [
                    f"{label}",
                    f"Tier: {row['tier']}",
                    f"Total messages: {total}",
                    f"Sent by me: {sent}",
                    f"Received by me: {recv}",
                    f"Reciprocity: {row['recip_class']}",
                    f"First contact: {row['first_contact']}",
                    f"Last contact: {row['last_contact']}",
                ]
            )
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1.2, color="rgba(120,120,120,0.35)"),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_text,
            textposition="top center",
            hovertext=hover_text,
            hoverinfo="text",
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=1, color="white"),
                opacity=0.95,
            ),
            showlegend=False,
        )
    )

    fig.update_layout(
        height=700,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(visible=False, range=[-1.05, 1.05]),
        yaxis=dict(visible=False, range=[-1.05, 1.05], scaleanchor="x", scaleratio=1),
        title="Relationship Graph (ego network)",
    )

    return fig


def render_dashboard(out_dir: str | os.PathLike[str] | None = None) -> None:
    output_dir = resolve_output_dir(out_dir)

    rel_clean = output_dir / "relationships_clean.csv"
    core_tl_path = output_dir / "core_timeline.csv"
    core_timeline_png = output_dir / "core_timeline.png"
    core_timeline_png_note = output_dir / "core_timeline_png_export_failed.txt"

    st.caption(f"Reading dashboard data from: {output_dir}")

    rel = safe_read_csv(rel_clean)
    rel["total_messages"] = rel["total_messages"].fillna(0).astype(int)
    rel["sent_by_me"] = rel["sent_by_me"].fillna(0).astype(int)
    rel["received_by_me"] = rel["received_by_me"].fillna(0).astype(int)

    rel["first_contact"] = pd.to_datetime(rel["first_contact"], errors="coerce", utc=True)
    rel["last_contact"] = pd.to_datetime(rel["last_contact"], errors="coerce", utc=True)

    rel["tier"] = rel["total_messages"].apply(tier_from_total)
    rel["recip_ratio"] = np.where(
        rel["received_by_me"] == 0,
        np.nan,
        rel["sent_by_me"] / rel["received_by_me"],
    )
    rel["recip_class"] = [
        recip_class(s, r) for s, r in zip(rel["sent_by_me"], rel["received_by_me"])
    ]

    rel["duration_days"] = (rel["last_contact"] - rel["first_contact"]).dt.days
    rel["duration_years"] = rel["duration_days"] / 365.25

    core_tl = safe_read_csv(core_tl_path)
    core_tl["start"] = pd.to_datetime(core_tl["start"], errors="coerce", utc=True)
    core_tl["end"] = pd.to_datetime(core_tl["end"], errors="coerce", utc=True)
    core_tl["total_messages"] = core_tl["total_messages"].fillna(0).astype(int)

    st.sidebar.header("Filters")
    hide_labels = st.sidebar.toggle("Hide labels (anonymize)", value=True)

    tier_opts = ["CORE", "RECURRING", "PERIPHERAL"]
    tiers = st.sidebar.multiselect("Tiers", tier_opts, default=["CORE", "RECURRING"])

    recip_opts = ["MOSTLY_ME", "BALANCED", "MOSTLY_THEM", "NO_RECEIVE"]
    recips = st.sidebar.multiselect("Reciprocity classes", recip_opts, default=recip_opts)

    min_date = pd.to_datetime(rel["first_contact"].min(), utc=True)
    max_date = pd.to_datetime(rel["last_contact"].max(), utc=True)

    if pd.isna(min_date) or pd.isna(max_date):
        st.warning("Could not infer date range. Some dates may be missing.")
        min_date = pd.Timestamp("2000-01-01", tz="UTC")
        max_date = pd.Timestamp.now(tz="UTC")

    start_date, end_date = st.sidebar.slider(
        "Time window (UTC)",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    )

    max_total_messages = int(max(1, rel["total_messages"].max()))
    min_messages = st.sidebar.slider("Min total messages", 1, max_total_messages, 5)

    graph_top_n = st.sidebar.slider("Graph nodes", 10, 100, 40)

    f = rel.copy()
    f = f[f["tier"].isin(tiers)]
    f = f[f["recip_class"].isin(recips)]
    f = f[f["total_messages"] >= min_messages]
    f = f[
        (f["first_contact"] <= pd.to_datetime(end_date, utc=True))
        & (f["last_contact"] >= pd.to_datetime(start_date, utc=True))
    ]
    f["label"] = f["email"].apply(lambda e: normalize_email_label(e, hide_labels))

    st.subheader("Exploratory Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Relationships (filtered)", f"{len(f):,}")
    c2.metric("CORE (filtered)", f"{(f['tier'] == 'CORE').sum():,}")
    c3.metric("Balanced (filtered)", f"{(f['recip_class'] == 'BALANCED').sum():,}")
    c4.metric("Mostly inbound (filtered)", f"{(f['recip_class'] == 'MOSTLY_THEM').sum():,}")

    if core_timeline_png.exists():
        with st.expander("Saved CORE timeline PNG"):
            st.image(str(core_timeline_png), use_container_width=True)
    elif core_timeline_png_note.exists():
        with st.expander("CORE timeline PNG (not generated)"):
            st.info(core_timeline_png_note.read_text(encoding="utf-8"))

    st.divider()

    st.subheader("Relationship Graph")
    st.caption(
        "This is an ego network centered on you. The current pipeline models direct relationships, "
        "not contact-to-contact edges."
    )
    fig_graph = build_ego_graph_figure(f, hide_labels=hide_labels, top_n=graph_top_n)
    st.plotly_chart(fig_graph, use_container_width=True)

    st.divider()

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.subheader("Timeline (Gantt-style)")
        tl = f.dropna(subset=["first_contact", "last_contact"]).copy()
        tl = tl.sort_values(["first_contact", "total_messages"], ascending=[True, False])

        top_n = st.slider("Max bars shown (for readability)", 20, 200, 80)
        tl = tl.head(top_n)

        if tl.empty:
            st.info("No timeline rows match the current filters.")
        else:
            fig_tl = px.timeline(
                tl,
                x_start="first_contact",
                x_end="last_contact",
                y="label",
                color="tier",
                hover_data={
                    "email": False if hide_labels else True,
                    "total_messages": True,
                    "sent_by_me": True,
                    "received_by_me": True,
                    "recip_ratio": ":.2f",
                    "recip_class": True,
                    "duration_days": True,
                    "first_contact": True,
                    "last_contact": True,
                },
            )
            fig_tl.update_yaxes(autorange="reversed", title="")
            fig_tl.update_xaxes(title="")
            fig_tl.update_layout(height=650, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_tl, use_container_width=True)

    with right:
        st.subheader("CORE Density by Year")
        core_for_density = rel[rel["tier"] == "CORE"].dropna(subset=["first_contact", "last_contact"]).copy()
        core_for_density = core_for_density[
            (core_for_density["first_contact"] <= pd.to_datetime(end_date, utc=True))
            & (core_for_density["last_contact"] >= pd.to_datetime(start_date, utc=True))
        ]

        years = range(
            pd.to_datetime(start_date, utc=True).year,
            pd.to_datetime(end_date, utc=True).year + 1,
        )
        density = []
        for y in years:
            y_start = pd.Timestamp(f"{y}-01-01", tz="UTC")
            y_end = pd.Timestamp(f"{y}-12-31", tz="UTC")
            active = (
                (core_for_density["first_contact"] <= y_end)
                & (core_for_density["last_contact"] >= y_start)
            ).sum()
            density.append({"year": y, "active_core": int(active)})

        dens = pd.DataFrame(density)
        if dens.empty:
            st.info("No density data for the current filters.")
        else:
            fig_den = px.line(dens, x="year", y="active_core", markers=True)
            fig_den.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
            fig_den.update_xaxes(dtick=1)
            st.plotly_chart(fig_den, use_container_width=True)

        st.subheader("Reciprocity (Sent vs Received)")

        scat = f.copy()

        if scat.empty:
            st.info("No reciprocity points for the current filters.")
        else:
            recip_scale = st.radio(
                "Reciprocity chart scale",
                options=["Log", "Linear"],
                horizontal=True,
                key="recip_scale",
            )

            if recip_scale == "Log":
                scat["plot_received"] = scat["received_by_me"].clip(lower=1)
                scat["plot_sent"] = scat["sent_by_me"].clip(lower=1)
                x_col = "plot_received"
                y_col = "plot_sent"
                log_x = True
                log_y = True
                x_title = "Received by me (log, zeros shown at 1)"
                y_title = "Sent by me (log, zeros shown at 1)"
                hover_data = {
                    "label": True,
                    "email": False if hide_labels else True,
                    "received_by_me": True,
                    "sent_by_me": True,
                    "total_messages": True,
                    "duration_years": ":.2f",
                    "recip_ratio": ":.2f",
                    "recip_class": True,
                    "plot_received": False,
                    "plot_sent": False,
                }
            else:
                x_col = "received_by_me"
                y_col = "sent_by_me"
                log_x = False
                log_y = False
                x_title = "Received by me"
                y_title = "Sent by me"
                hover_data = {
                    "label": True,
                    "email": False if hide_labels else True,
                    "received_by_me": True,
                    "sent_by_me": True,
                    "total_messages": True,
                    "duration_years": ":.2f",
                    "recip_ratio": ":.2f",
                    "recip_class": True,
                }

            fig_rec = px.scatter(
                scat,
                x=x_col,
                y=y_col,
                color="tier",
                symbol="recip_class",
                size="total_messages",
                hover_data=hover_data,
                log_x=log_x,
                log_y=log_y,
            )
            fig_rec.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
            fig_rec.update_xaxes(title=x_title)
            fig_rec.update_yaxes(title=y_title)
            st.plotly_chart(fig_rec, use_container_width=True)

    st.divider()

    st.subheader("Lifecycle: Duration vs Volume")
    life = f.dropna(subset=["duration_days"]).copy()
    if life.empty:
        st.info("No lifecycle data for the current filters.")
    else:
        fig_life = px.scatter(
            life,
            x="duration_years",
            y="total_messages",
            color="recip_class",
            symbol="tier",
            hover_data={
                "label": True,
                "email": False if hide_labels else True,
                "sent_by_me": True,
                "received_by_me": True,
                "recip_ratio": ":.2f",
                "first_contact": True,
                "last_contact": True,
            },
        )
        fig_life.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10))
        fig_life.update_xaxes(title="Duration (years)")
        fig_life.update_yaxes(title="Total messages")
        st.plotly_chart(fig_life, use_container_width=True)

    with st.expander("Table (filtered relationships)"):
        show_cols = [
            "label",
            "tier",
            "total_messages",
            "sent_by_me",
            "received_by_me",
            "recip_ratio",
            "recip_class",
            "duration_years",
            "first_contact",
            "last_contact",
        ]
        st.dataframe(
            f[show_cols].sort_values("total_messages", ascending=False),
            use_container_width=True,
        )


def main() -> None:
    st.set_page_config(page_title="Inbox Archeology Dashboard", layout="wide")
    render_dashboard()


if __name__ == "__main__":
    main()