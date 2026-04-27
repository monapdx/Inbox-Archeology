"""
Extract basic headers from a Gmail MBOX into a CSV.

Example:
python extract_headers.py --mbox "All mail Including Spam and Trash.mbox" --out output/inbox_metadata.csv
"""

from __future__ import annotations

import argparse
import csv
import mailbox
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional


def _to_iso(date_value: Optional[str]) -> str:
    if not date_value:
        return ""
    try:
        dt = parsedate_to_datetime(date_value)
        if dt is None:
            return ""
        return dt.isoformat()
    except Exception:
        return ""


def emit_progress(message: str) -> None:
    print(f"PROGRESS: {message}", flush=True)


def extract_headers(mbox_path: str, output_csv: str, progress_every: int = 10000) -> int:
    mbox = mailbox.mbox(mbox_path)

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index", "date", "from", "to", "subject", "message_id", "thread_id"])

        for i, msg in enumerate(mbox):
            w.writerow(
                [
                    i,
                    _to_iso(msg.get("Date", "")),
                    msg.get("From", ""),
                    msg.get("To", ""),
                    msg.get("Subject", ""),
                    msg.get("Message-ID", ""),
                    msg.get("X-GM-THRID", ""),
                ]
            )

            count += 1
            if progress_every and count % progress_every == 0:
                emit_progress(f"Processed {count:,} messages")

    emit_progress(f"Finished extracting {count:,} messages")
    print(f"[extract_headers] wrote {count:,} rows to {out_path}", flush=True)
    return count


def main() -> None:
    p = argparse.ArgumentParser(description="Extract basic headers from a Gmail MBOX into a CSV.")
    p.add_argument("--mbox", required=True, help="Path to Gmail .mbox file (Google Takeout).")
    p.add_argument(
        "--out",
        default=str(Path("output") / "inbox_metadata.csv"),
        help="Output CSV (default: output/inbox_metadata.csv)",
    )
    p.add_argument(
        "--progress-every",
        type=int,
        default=10000,
        help="Print progress every N messages (0 disables).",
    )
    args = p.parse_args()
    extract_headers(args.mbox, args.out, args.progress_every)


if __name__ == "__main__":
    main()