# pipelines/gmail/scripts/extract_headers.py
"""
Extract basic headers from a Gmail MBOX into a CSV.

Example:
python extract_headers.py --mbox "All mail Including Spam and Trash.mbox" --out output/inbox_metadata.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import mailbox
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional


def _write_progress_json(path: Path | None, processed: int, *, done: bool) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"step": "extract_headers", "processed_messages": processed, "done": done}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _to_iso(date_value: Optional[str]) -> str:
    if not date_value:
        return ""
    try:
        dt = parsedate_to_datetime(date_value)
        if dt is None:
            return ""
        # Keep timezone info if present; otherwise write naive ISO
        return dt.isoformat()
    except Exception:
        return ""


def extract_headers(
    mbox_path: str,
    output_csv: str,
    progress_every: int = 10000,
    progress_json: str | None = None,
) -> int:
    mbox = mailbox.mbox(mbox_path)

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pj = Path(progress_json) if progress_json else None
    _write_progress_json(pj, 0, done=False)

    count = 0
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index", "date", "from", "to", "subject", "message_id", "thread_id"])

        for i, msg in enumerate(mbox):
            w.writerow([
                i,
                _to_iso(msg.get("Date", "")),
                msg.get("From", ""),
                msg.get("To", ""),
                msg.get("Subject", ""),
                msg.get("Message-ID", ""),
                msg.get("X-GM-THRID", ""),
            ])

            count += 1
            if progress_every and count % progress_every == 0:
                print(f"[extract_headers] processed {count:,} messages...")
                _write_progress_json(pj, count, done=False)

    print(f"[extract_headers] wrote {count:,} rows to {out_path}")
    _write_progress_json(pj, count, done=True)
    return count


def main() -> None:
    p = argparse.ArgumentParser(description="Extract basic headers from a Gmail MBOX into a CSV.")
    p.add_argument("--mbox", required=True, help="Path to Gmail .mbox file (Google Takeout).")
    p.add_argument("--out", default=str(Path("output") / "inbox_metadata.csv"),
                   help="Output CSV (default: output/inbox_metadata.csv)")
    p.add_argument("--progress-every", type=int, default=10000,
                   help="Print progress every N messages (0 disables).")
    p.add_argument(
        "--progress-json",
        default="",
        help="Optional path to write JSON progress ({processed_messages, done}) for UIs.",
    )
    args = p.parse_args()
    pj = args.progress_json.strip() or None
    extract_headers(args.mbox, args.out, args.progress_every, progress_json=pj)


if __name__ == "__main__":
    main()
