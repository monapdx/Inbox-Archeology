# Inbox Archeology

Explore your exported message data like a personal time machine.

Inbox Archeology transforms your Google Takeout `.mbox` into a local, visual archive so you can explore relationship patterns over time.

[Instructions](https://docs.google.com/presentation/d/1NASuuZgwQFKslOs8mLnQRCpEpoVjxuEHiXlUIcfJurw/edit?usp=sharing)
---

## What it does

- Parses Gmail Takeout mailbox exports
- Builds relationship-level tables through a multi-step pipeline
- Renders a Streamlit dashboard with:
  - relationship graph
  - timeline views
  - reciprocity analysis
  - lifecycle metrics
  - CORE relationship density by year

Everything runs on your machine.

---

## Requirements

- Python 3.10+
- A Gmail Takeout `.mbox` file (for real analysis)

Install dependencies:

```bash
python -m venv .venv
```

Activate:

- macOS / Linux: `source .venv/bin/activate`
- Windows (cmd): `.venv\Scripts\activate.bat`
- Windows (PowerShell): `.venv\Scripts\Activate.ps1`

Then:

```bash
pip install -r requirements.txt
```

---

## Run

```bash
streamlit run app.py
```

The app creates/uses local folders in this repo:

- `input/` for source `.mbox` files
- `workspaces/` for per-run outputs

---

## Current app flow

### 1) Add Gmail Takeout

Recommended path (for real exports):

1. Download your Gmail Takeout export
2. Locate the mailbox file (often `All Mail.mbox`)
3. Copy the `.mbox` into `input/`
4. Click **Refresh list** in the app

Optional path:

- Upload a small test `.mbox` directly in the app
- Intended for small files only (about 200 MB browser upload limit)

### 2) Choose workspace

- Pick the detected `.mbox`
- Set a run name (used for `workspaces/<run-name>/`)
- Reopen previous completed runs from **Open Existing Workspace**

### 3) Run analysis

- Click **Run Inbox Archeology**
- Progress is shown live as pipeline steps complete
- Open dashboard automatically (toggle in sidebar) or manually after run

---

## Output location

For each run:

- Workspace: `workspaces/<run-name>/`
- Output files: `workspaces/<run-name>/output/`

Typical generated artifacts:

- `inbox_metadata.csv`
- `relationships_raw.csv`
- `relationships_filtered.csv`
- `relationships_clean.csv`
- `core_timeline.csv`
- `core_timeline.png`

---

## Environment variables (`.env`)

Create a `.env` file in the project root to customize relationship extraction.

### Identify your own addresses

```env
SELF_EMAILS=you@gmail.com,alias@gmail.com,you@company.com
```

This is important for accurate sent/received attribution.

### Ignore automated/bulk senders

```env
AUTOMATED_DOMAINS=facebookmail.com,google.com,linkedin.com,substack.com
AUTOMATED_PREFIXES=no-reply@,noreply@,notifications@,donotreply@
```

- `AUTOMATED_DOMAINS`: filters addresses ending in `@domain`
- `AUTOMATED_PREFIXES`: filters addresses starting with those prefixes

After changing `.env`, rerun analysis for affected workspaces.

---

## Privacy

Inbox Archeology is local-first:

- no cloud processing in this app flow
- no external API requirement for analysis
- no mailbox upload to third-party services by default

Your archive stays on your machine unless you move it.

---

## Project structure

- `app.py` - Streamlit UI and run workflow
- `pipeline.py` - orchestrates step scripts
- `steps/` - modular processing steps
- `dashboard.py` - dashboard rendering
- `input/` - source mailbox files
- `workspaces/` - saved run outputs

---

## Contributing

See `CONTRIBUTING.md`.

---

## License

MIT
