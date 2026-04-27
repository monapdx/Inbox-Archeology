# Inbox Archeology

Explore your exported message data like a personal time machine.

---

## Preview

### Dashboard
![Dashboard](./dashboard.png)

### Relationship Graph
![Relationship Graph](./relationship_graph.png)

### Analytics
![Analytics](./analytics.png)

---

## What this is

Inbox Archeology transforms your Google Takeout data into a searchable, visual archive.

- Fully local
- Privacy-first
- Designed for exploration, not just storage

---

<table border="1" cellpadding="8" cellspacing="0">
  <thead>
    <tr>
      <th>Step</th>
      <th>File</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>extract_headers.py</td>
      <td>Parses a Gmail .mbox file and extracts basic email metadata (date, sender, recipient, subject, etc.) into a CSV file.</td>
    </tr>
    <tr>
      <td>2</td>
      <td>extract_relationships.py</td>
      <td>Processes the metadata CSV to build a dataset of human relationships, counting messages sent/received and tracking first/last contact.</td>
    </tr>
    <tr>
      <td>3</td>
      <td>filter_relationships.py</td>
      <td>Filters out weak or insignificant relationships based on message count or activity duration thresholds.</td>
    </tr>
    <tr>
      <td>4</td>
      <td>clean_relationships.py</td>
      <td>Cleans and merges duplicate or variant email addresses, removes system accounts, and produces a normalized relationships dataset.</td>
    </tr>
    <tr>
      <td>5</td>
      <td>reanalyze_clean_relationships.py</td>
      <td>Recomputes relationship metrics (tiers, reciprocity, rankings) using the cleaned dataset for more accurate insights.</td>
    </tr>
    <tr>
      <td>6</td>
      <td>build_core_timeline.py</td>
      <td>Extracts only high-volume (“CORE”) relationships and builds a timeline dataset showing when each relationship started and ended.</td>
    </tr>
    <tr>
      <td>7</td>
      <td>plot_core_timeline.py</td>
      <td>Generates a visual timeline (chart) of core relationships over time, optionally saving it as an image.</td>
    </tr>
    <tr>
      <td>8</td>
      <td>preview_core_timeline.py</td>
      <td>Analyzes overlap between core relationships by year, showing how many were active at the same time.</td>
    </tr>
    <tr>
      <td>9</td>
      <td>analyze_relationships.py</td>
      <td>Provides final summary statistics and rankings for filtered relationships, including tiers and reciprocity analysis.</td>
    </tr>
  </tbody>
</table>

## Quick Start

### What you need

- **Python 3.10+** (3.11+ recommended on Windows)
- **pip** and a virtual environment (see below)
- A **Gmail Google Takeout** export as an `.mbox` file (often named like `All Mail.mbox` or `All mail Including Spam and Trash.mbox`)

**Optional — desktop shell:** [Node.js](https://nodejs.org/) (LTS is fine) if you want to run the Electron wrapper in `electron/`, which starts Streamlit and lets you pick the `.mbox` from a file dialog.

### 1. Download the project

```bash
git clone https://github.com/monapdx/Inbox-Archeology.git
cd Inbox-Archeology
```

### 2. Install Python dependencies

```bash
python -m venv .venv
```

Activate the venv:

- **macOS / Linux:** `source .venv/bin/activate`
- **Windows (cmd):** `.venv\Scripts\activate.bat`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

Then:

```bash
pip install -r requirements.txt
```

On Windows you can alternatively double-click `launch_inbox_archeology.bat` from the repo folder; it creates the venv, installs requirements, and starts Streamlit (you still need to point the app at your `.mbox`; see **Streamlit only** below).

### 3. Run the app (choose one)

#### A. Desktop app (recommended)

From the repo root:

```bash
cd electron
npm install
npm start
```

The window loads the local Streamlit UI. Use **File → Choose MBOX File** (or **Ctrl+O** / **Cmd+O**), select your Takeout `.mbox`, then in the browser view click **Run Inbox Archeology**. When the run finishes, use **Open Dashboard** to view charts and graphs.

#### B. Streamlit only

```bash
streamlit run app.py
```

The UI does **not** include a built-in file picker. The app expects the path to your `.mbox` in the **`mbox` query parameter** (the Electron app sets this for you after you choose a file).

1. Start Streamlit as above.
2. Open `http://127.0.0.1:8501/?mbox=` followed by the **URL-encoded full absolute path** to your `.mbox` (your browser’s address bar or “Open URL” can help after you paste the path and let the browser encode it).
   - Use the **full absolute path** to the file.
   - Encode spaces and special characters (e.g. spaces as `%20`). On Windows, forward slashes in the path (e.g. `C:/Users/You/Takeout/Mail/All Mail.mbox`) are usually easier than escaping backslashes.

If no `mbox` parameter is set, the home screen prompts you to choose a file from the desktop app, or you can add `?mbox=...` and refresh.

### 4. First-time analysis settings

Before your first run (or when charts look wrong), add a **`.env`** file in the project root and set at least **`SELF_EMAILS`**. See [Environment variables (.env)](#environment-variables-env) for how to list your own addresses and extra senders or domains to treat as automated noise.

### Where outputs go

Workspaces are stored under the **app data directory** from `config.py`, not inside the git repo by default (that folder also holds `input` and `logs` directories for the app):

- **Windows:** `%LOCALAPPDATA%\InboxArcheology\workspaces\<run-name>\output\`
- Other platforms use the same layout relative to the resolved local app data path in `config.py`.

`<run-name>` is derived from your `.mbox` filename (see `slugify` in `app.py`). CSVs and images from the pipeline are written under that folder’s `output/` directory.

### Expected result

After the pipeline finishes, open **Open Dashboard** in the UI to explore the archive. Large mailboxes can take a long time on the first run; the progress bar updates when individual steps report progress.

---

## Environment variables (.env)

The relationship pipeline (`steps/extract_relationships.py`) loads environment variables from a **`.env`** file in the **repository root** (next to `app.py`), using [python-dotenv](https://github.com/theskumar/python-dotenv). Use a plain text file named exactly `.env` (leading dot; on Windows, save as `.env` in your editor so it is not saved as `.env.txt` by mistake).

### Your own addresses — `SELF_EMAILS`

Set **`SELF_EMAILS`** to every email address that represents **you** in this export (Gmail aliases, workspace addresses, etc.). Use a **comma-separated** list; matching is **case-insensitive**.

```env
SELF_EMAILS=you@gmail.com,alias@gmail.com,you@yourcompany.com
```

If `SELF_EMAILS` is missing or empty, the step falls back to generic placeholder defaults that will **not** match most people’s mail—set this variable for correct “you vs. everyone else” stats and graphs.

### Ignoring automated and bulk senders

Senders that look like bots, newsletters, or system mail can drown out real people. You can tune two optional lists (comma-separated, compared in lowercase). If you omit them, built-in defaults apply; see `steps/extract_relationships.py` for the default lists.

**`AUTOMATED_DOMAINS`** — Domains to treat as automated. List only the domain part (no `@`). Any sender address that ends with `@` plus that domain is filtered as automated.

```env
AUTOMATED_DOMAINS=facebookmail.com,linkedin.com,github.com,substack.com
```

**`AUTOMATED_PREFIXES`** — Local-part prefixes for addresses to treat as automated. If an address **starts with** one of these strings (after lowercasing), it is filtered. Handy for common no-reply patterns.

```env
AUTOMATED_PREFIXES=no-reply@,noreply@,donotreply@,mailer-daemon@
```

Together, these rules reduce noise from mass senders; they do not replace `SELF_EMAILS`, which still tells the pipeline which addresses are yours.

### After you change `.env`

Turn on **Re-run completed steps** in the app before running again, or delete the generated CSVs under your workspace `output/` folder, so **`extract_relationships`** and later steps re-read your updated variables.

---

## Get Involved

👉 Check out the Issues tab and CONTRIBUTING.md to get started

---

## Philosophy

This project is part of a broader movement toward:

- Data portability  
- Digital sovereignty  
- Personal archives  

Your data should belong to you.
