"""
Plot a CORE relationship timeline PNG from core_timeline.csv.

This renderer intentionally avoids matplotlib so the pipeline can run
reliably on environments where compiled plotting wheels are unavailable.
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _safe_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _write_timeline_png(rows: list[dict], save_path: Path) -> None:
    save_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        img = Image.new("RGB", (1200, 320), "white")
        draw = ImageDraw.Draw(img)
        title_font = _safe_font(24)
        body_font = _safe_font(16)
        draw.text((40, 40), "CORE Relationship Timeline", fill="#111111", font=title_font)
        draw.text(
            (40, 95),
            "No CORE rows found in core_timeline.csv.",
            fill="#444444",
            font=body_font,
        )
        img.save(save_path, format="PNG")
        print(f"Saved plot to: {save_path}")
        return

    start_min = min(r["start"] for r in rows)
    end_max = max(r["end"] for r in rows)
    total_days = max((end_max - start_min).days, 1)

    left = 90
    right = 40
    top = 75
    bottom = 40
    row_h = 24
    row_gap = 8
    height = top + bottom + len(rows) * (row_h + row_gap)
    width = 1400
    plot_w = width - left - right

    img = Image.new("RGB", (width, max(320, height)), "white")
    draw = ImageDraw.Draw(img)
    title_font = _safe_font(22)
    axis_font = _safe_font(14)

    draw.text((left, 24), "CORE Relationship Timeline", fill="#111111", font=title_font)
    draw.text((left, 50), f"{start_min.date()} to {end_max.date()}", fill="#555555", font=axis_font)

    # Vertical year guides.
    for year in range(start_min.year, end_max.year + 1):
        year_dt = datetime(year, 1, 1)
        day_offset = (year_dt - start_min).days
        if day_offset < 0:
            x = left
        elif day_offset > total_days:
            x = left + plot_w
        else:
            x = left + int((day_offset / total_days) * plot_w)
        draw.line((x, top - 5, x, img.height - bottom), fill="#efefef", width=1)
        draw.text((x + 2, top - 24), str(year), fill="#777777", font=axis_font)

    # Relationship bars.
    bar_fill = "#6C63FF"
    bar_outline = "#4e46c8"
    for i, row in enumerate(rows):
        y = top + i * (row_h + row_gap)
        start_x = left + int(((row["start"] - start_min).days / total_days) * plot_w)
        end_x = left + int(((row["end"] - start_min).days / total_days) * plot_w)
        if end_x <= start_x:
            end_x = start_x + 1

        draw.rounded_rectangle(
            (start_x, y, end_x, y + row_h),
            radius=4,
            fill=bar_fill,
            outline=bar_outline,
            width=1,
        )

    draw.text((left, img.height - bottom + 8), "Time", fill="#444444", font=axis_font)
    img.save(save_path, format="PNG")
    print(f"Saved plot to: {save_path}")


def plot_core_timeline(core_timeline_csv: str, save_path: str | None = None):
    rows = []
    with open(core_timeline_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                {
                    "email": r["email"],
                    "start": datetime.fromisoformat(r["start"]),
                    "end": datetime.fromisoformat(r["end"]),
                    "total": int(r["total_messages"]),
                }
            )

    rows.sort(key=lambda r: r["start"])

    if save_path:
        _write_timeline_png(rows, Path(save_path))
    else:
        print("No --save path provided; skipping image output.")


def main():
    parser = argparse.ArgumentParser(description="Plot CORE timeline from core_timeline.csv")
    parser.add_argument("--in", dest="in_csv", default=str(Path("output") / "core_timeline.csv"))
    parser.add_argument("--save", default="", help="Optional path to save PNG (if omitted, shows window).")
    args = parser.parse_args()
    plot_core_timeline(args.in_csv, args.save or None)


if __name__ == "__main__":
    main()
