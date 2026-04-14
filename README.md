# Inbox Archeology

[![Relationship Graph](https://img.shields.io/badge/%F0%9F%93%89Relationship%20Graph-111111?style=for-the-badge)](#relationship-graph) [![Dashboard](https://img.shields.io/badge/%F0%9F%9A%80Dashboard-111111?style=for-the-badge)](#dashboard) [![Analytics](https://img.shields.io/badge/%E2%9C%85Analytics-111111?style=for-the-badge)](#analytics) 

Explore your exported message data like a personal time machine.

---

## Table of Contents

- [Inbox Archeology](#inbox-archeology)
  - [Preview](#preview)
    - [Dashboard](#dashboard)
    - [Relationship Graph](#relationship-graph)
    - [Analytics](#analytics)
  - [What this is](#what-this-is)
  - [Quick Start](#quick-start)
    - [What you need](#what-you-need)
    - [1. Download the project](#1-download-the-project)
    - [2. Install dependencies](#2-install-dependencies)
    - [3. Start the app](#3-start-the-app)
    - [4. Add your Gmail export](#4-add-your-gmail-export)
    - [Expected result](#expected-result)
  - [Get Involved](#get-involved)
  - [Philosophy](#philosophy)

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

## Quick Start

### What you need

- Python 3.10+
- A Gmail Takeout export containing `All Mail.mbox`

### 1. Download the project

```bash
git clone https://github.com/monapdx/Inbox-Archeology.git
cd Inbox-Archeology
```

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the app

```bash
streamlit run app.py
```

### 4. Add your Gmail export

When the app opens in your browser:

1. Find your Gmail Takeout file named `All Mail.mbox`
2. Copy it into the local `input/` folder shown in the sidebar
3. Click **Refresh list**
4. Select the `.mbox` file
5. Click **Run Inbox Archeology**

### Expected result

After the pipeline finishes, the app saves results in `workspaces/<run-name>/output/` and can open the dashboard automatically.

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
