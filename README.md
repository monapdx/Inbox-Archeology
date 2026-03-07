# Inbox Archeology

**Inbox Archeology** is a local-first tool that analyzes your **Gmail
Takeout export** to reconstruct the social history of your inbox.

It transforms a raw `.mbox` archive into an interactive dashboard
showing:

-   who you communicated with most
-   how relationships evolved over time
-   reciprocity patterns (who wrote whom)
-   long-term communication timelines
-   core vs peripheral relationships

Everything runs **entirely on your computer**. Your email data never
leaves your machine.

------------------------------------------------------------------------

# Features

## Relationship Graph

Visualizes your inbox as an **ego network** centered on you.

-   node size = message volume\
-   color = relationship tier (core / recurring / peripheral)\
-   hover for details

## Timeline Visualization

A **Gantt-style timeline** of when each relationship was active.

Shows: - first contact - last contact - total message volume -
relationship duration

## Reciprocity Analysis

Scatterplot of **sent vs received messages** revealing:

-   balanced relationships
-   one-sided communication
-   broadcast-style contacts

## Lifecycle Analysis

Relationship duration vs message volume highlights:

-   long but quiet connections
-   intense short-term exchanges
-   durable high-volume relationships

## CORE Relationship Density

Tracks how many of your **core relationships** were active each year.

------------------------------------------------------------------------

# Architecture

Gmail Takeout (.mbox) ↓ extract_headers ↓ extract_relationships ↓
filter_relationships ↓ clean_relationships ↓ build_core_timeline ↓
Streamlit Dashboard

Each processing step is modular and lives in the **`steps/` directory**.

------------------------------------------------------------------------

# Project Structure

Inbox-Archeology │ ├── app.py ├── pipeline.py ├── dashboard.py ├──
requirements.txt ├── launch_inbox_archeology.bat │ ├── steps/ │ ├──
extract_headers.py │ ├── extract_relationships.py │ ├──
filter_relationships.py │ ├── clean_relationships.py │ ├──
analyze_relationships.py │ ├── reanalyze_clean_relationships.py │ ├──
build_core_timeline.py │ ├── preview_core_timeline.py │ └──
plot_core_timeline.py │ ├── input/ ├── output/ └── workspaces/

------------------------------------------------------------------------

# Installation

## Requirements

-   Python **3.10+**
-   Gmail Takeout export (`.mbox`)

------------------------------------------------------------------------

## Quick Start (Windows)

Run the launcher:

launch_inbox_archeology.bat

This will: 1. create a virtual environment 2. install dependencies 3.
launch the Streamlit dashboard

------------------------------------------------------------------------

## Manual Installation

python -m venv .venv

Activate:

.venv`\Scripts`{=tex}`\activate`{=tex}

Install dependencies:

pip install -r requirements.txt

Run the app:

streamlit run app.py

------------------------------------------------------------------------

# Using Your Gmail Export

1.  Download your Gmail data via **Google Takeout**
2.  Locate the file:

All Mail.mbox

3.  Copy it into:

input/

4.  Start the app
5.  Select the `.mbox` file and run the pipeline

Large inbox exports (multiple GB) are supported.

------------------------------------------------------------------------

# Privacy

Inbox Archeology is designed for **personal local analysis**.

-   No network calls
-   No cloud services
-   No telemetry
-   No external APIs

Your email archive **never leaves your machine**.

------------------------------------------------------------------------

# Configuration

Optional `.env` file:

SELF_EMAILS=your_email@gmail.com
AUTOMATED_DOMAINS=facebookmail.com,google.com
AUTOMATED_PREFIXES=no-reply@,notifications@

This allows you to filter automated emails and correctly identify your
own addresses.

------------------------------------------------------------------------

# Roadmap

Potential future improvements:

-   force-directed network graph
-   relationship clustering
-   attachment analysis
-   subject/topic modeling
-   email frequency heatmaps
-   multi-account support

------------------------------------------------------------------------

# License

MIT License

------------------------------------------------------------------------

# Author

Created by **Ashly Lorenzana**
