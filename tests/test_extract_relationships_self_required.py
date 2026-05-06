import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module", autouse=True)
def _steps_on_path() -> None:
    p = str(ROOT / "steps")
    if p not in sys.path:
        sys.path.insert(0, p)


def test_extract_requires_non_empty_self(tmp_path: Path) -> None:
    from extract_relationships import extract_relationships

    inp = tmp_path / "inbox_metadata.csv"
    inp.write_text(
        "index,date,from,to,subject,message_id,thread_id\n"
        "0,2020-01-01T00:00:00+00:00,a@example.com,b@example.com,,,\n",
        encoding="utf-8",
    )
    outp = tmp_path / "relationships.csv"
    with pytest.raises(ValueError, match="SELF_EMAILS"):
        extract_relationships(str(inp), str(outp), self_addresses=[])


def test_extract_runs_with_explicit_self(tmp_path: Path) -> None:
    from extract_relationships import extract_relationships

    inp = tmp_path / "inbox_metadata.csv"
    inp.write_text(
        "index,date,from,to,subject,message_id,thread_id\n"
        "0,2020-01-01T00:00:00+00:00,a@example.com,b@example.com,,,\n",
        encoding="utf-8",
    )
    outp = tmp_path / "relationships.csv"
    extract_relationships(str(inp), str(outp), self_addresses=["a@example.com"])
    assert outp.is_file()
    body = outp.read_text(encoding="utf-8")
    assert "b@example.com" in body
