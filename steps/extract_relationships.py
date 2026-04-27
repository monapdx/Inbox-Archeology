"""
Build a 'relationships' table from inbox_metadata.csv.

Refactor notes:
- Removed hardcoded paths (now CLI args).
- Kept original logic, only wrapped into functions + main().
- Added .env support for self emails and automated sender filters.
- Added pipeline-friendly progress output.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    return [item.strip().lower() for item in value.split(",") if item.strip()]


DEFAULT_SELF_ADDRESSES = get_env_list(
    "SELF_EMAILS",
    [
        "thegirlnextfloor@gmail.com",
        "ashly@ashlylorenzana.com",
    ],
)

DEFAULT_AUTOMATED_DOMAINS = get_env_list(
    "AUTOMATED_DOMAINS",
    [
        "facebookmail.com",
        "google.com",
        "googlemail.com",
        "craigslist.org",
        "nextdoor.com",
        "poshmark.com",
        "citychiconline.com",
        "havenly.com",
        "treasuremytext.com",
        "simple.life",
        "mail.havenly.com",
    ],
)

DEFAULT_AUTOMATED_PREFIXES = get_env_list(
    "AUTOMATED_PREFIXES",
    [
        "no-reply@",
        "noreply@",
        "notifications@",
        "support@",
        "help@",
    ],
)


def norm_email(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    if "<" in s and ">" in s:
        s = s.split("<")[-1].split(">")[0]
    return s.lower()


def is_automated(email: str, self_addresses, automated_domains, automated_prefixes) -> bool:
    if not email:
        return True
    if email in self_addresses:
        return True
    for p in automated_prefixes:
        if email.startswith(p):
            return True
    for d in automated_domains:
        if email.endswith("@" + d):
            return True
    return False


def parse_date(s: str):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s)
    except Exception:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    else:
        d = d.astimezone(timezone.utc)
    if d.year > datetime.now().year + 1:
        return None
    return d


def emit_progress(message: str) -> None:
    print(f"PROGRESS: {message}", flush=True)


def emit_progress_pct(processed: int, total: int, message: str) -> None:
    if total <= 0:
        emit_progress(message)
        return
    pct = max(0.0, min(1.0, processed / total))
    print(f"PROGRESS_PCT:{pct:.4f}|{message}", flush=True)


def count_data_rows(csv_path: str) -> int:
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        return sum(1 for _ in reader)


def extract_relationships(
    inbox_metadata_csv: str,
    out_csv: str,
    self_addresses=None,
    automated_domains=None,
    automated_prefixes=None,
    progress_every: int = 25000,
):
    self_addresses = {norm_email(x) for x in (self_addresses or DEFAULT_SELF_ADDRESSES)}
    automated_domains = tuple(x.lower() for x in (automated_domains or DEFAULT_AUTOMATED_DOMAINS))
    automated_prefixes = tuple(x.lower() for x in (automated_prefixes or DEFAULT_AUTOMATED_PREFIXES))

    emit_progress("Counting input rows")
    total_rows = count_data_rows(inbox_metadata_csv)
    emit_progress(f"Found {total_rows:,} metadata rows")

    people = defaultdict(
        lambda: {
            "total": 0,
            "sent": 0,
            "received": 0,
            "first": None,
            "last": None,
        }
    )

    processed = 0
    kept = 0

    with open(inbox_metadata_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            processed += 1

            sender = norm_email(row.get("from", ""))
            recipient = norm_email(row.get("to", ""))
            d = parse_date(row.get("date", ""))

            if sender in self_addresses:
                other = recipient
                direction = "sent"
            else:
                other = sender
                direction = "received"

            if not other or is_automated(other, self_addresses, automated_domains, automated_prefixes):
                if progress_every and processed % progress_every == 0:
                    emit_progress_pct(
                        processed,
                        total_rows,
                        f"Processed {processed:,} of {total_rows:,} rows; kept {kept:,} human relationships so far",
                    )
                continue

            rec = people[other]
            rec["total"] += 1
            if direction == "sent":
                rec["sent"] += 1
            else:
                rec["received"] += 1
            kept += 1

            if d:
                if rec["first"] is None or d < rec["first"]:
                    rec["first"] = d
                if rec["last"] is None or d > rec["last"]:
                    rec["last"] = d

            if progress_every and processed % progress_every == 0:
                emit_progress_pct(
                    processed,
                    total_rows,
                    f"Processed {processed:,} of {total_rows:,} rows; kept {kept:,} human relationships so far",
                )

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    emit_progress("Writing relationships CSV")

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "email",
                "total_messages",
                "sent_by_me",
                "received_by_me",
                "first_contact",
                "last_contact",
            ]
        )
        for email, rec in sorted(people.items(), key=lambda x: x[1]["total"], reverse=True):
            writer.writerow(
                [
                    email,
                    rec["total"],
                    rec["sent"],
                    rec["received"],
                    rec["first"].isoformat() if rec["first"] else "",
                    rec["last"].isoformat() if rec["last"] else "",
                ]
            )

    emit_progress_pct(
        total_rows if total_rows > 0 else 1,
        total_rows if total_rows > 0 else 1,
        f"Finished relationship extraction: {len(people):,} unique human relationships written",
    )

    print(f"Done. {len(people)} human relationships written to {out_path}", flush=True)
    print(f"SELF_EMAILS: {', '.join(sorted(self_addresses))}", flush=True)
    print(f"AUTOMATED_DOMAINS: {', '.join(automated_domains)}", flush=True)
    print(f"AUTOMATED_PREFIXES: {', '.join(automated_prefixes)}", flush=True)
    return str(out_path)


def main():
    parser = argparse.ArgumentParser(description="Extract relationship counts from inbox metadata CSV.")
    parser.add_argument(
        "--in",
        dest="in_csv",
        default=str(Path("output") / "inbox_metadata.csv"),
        help="Path to inbox_metadata.csv (default: output/inbox_metadata.csv)",
    )
    parser.add_argument(
        "--out",
        default=str(Path("output") / "relationships_raw.csv"),
        help="Path to output relationships CSV (default: output/relationships_raw.csv)",
    )
    parser.add_argument(
        "--self",
        nargs="*",
        default=None,
        help="Optional override for your own email addresses (space-separated list). "
        "If omitted, values come from .env or built-in defaults.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=25000,
        help="Emit progress every N rows while processing metadata CSV.",
    )
    args = parser.parse_args()

    extract_relationships(
        args.in_csv,
        args.out,
        self_addresses=args.self if args.self else None,
        progress_every=args.progress_every,
    )


if __name__ == "__main__":
    main()