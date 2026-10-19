# 🌾 KulhWise (Digital Kohli)
### Smart Canal Water Rotation & Accountability for Shared Communal Irrigation

> **Software-first irrigation rotation and accountability tool for communities where multiple farmers share one canal or kuhl.**

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-teal.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-sky.svg)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Product Overview

In communal canal irrigation systems (such as the traditional Himalayan **Kulh** or Northern Indian **Warabandi** systems), water flows down a single open channel shared across many village plots. 

### The Problem KulhWise Solves:
1. **Paper-based schedules are difficult to audit** and fail to explain missed or shortened turns.
2. **Head-reach farmers capture more effective water** due to unmonitored overdraw and natural conveyance/seepage losses down the channel.
3. **Disrupted turns are forgotten** once the next weekly schedule starts, compounding water debt for tail-end fields.
4. **Self-reported shortages can be inaccurate or contradictory**; the system must flag conflicting claims for human review rather than blindly trusting every report or accusing farmers.

---

## 💡 Product Principles

- **Fairness-Aware**: Equal minutes do not mean equal effective water or equal crop satisfaction.
- **Transparent & Explainable**: Clearly display inputs, mathematical calculation, status, and rationale for every allocation.
- **Accessible & Farmer-Centric**: Simple labels, mobile-first report flow (extensible to WhatsApp, Telegram, IVR, Hindi, Dogri, Punjabi).
- **Hardware-Light**: Works with entered and simulated data; calibrated flow sensors or telemetry can be added in future pilots without being mandatory for the MVP.
- **Honest Evidence**: Simulated outputs are clearly distinguished from physical field sensor telemetry.

---

## 📐 Core Scheduling Logic & Mathematical Formulation

### 1. Multi-Factor Allocation Formula
$$T_i = [\text{Base Share}_i \times \text{Seepage Boost}_i] + (\beta \times \text{Water Debt}_i) - \text{Overdraw Penalty}_i$$

Where:
- **$\text{Base Share}_i$**: Derived from plot area (in **Kanals**) and crop water duty factor $K_{\text{crop}}$:
  - *Basmati Paddy*: $1.30$
  - *Vegetables*: $1.15$
  - *Wheat*: $1.00$
  - *Mustard*: $0.75$
- **$\text{Seepage Boost}_i$**: Adjustable compensation multiplier offsetting conveyance losses based on channel distance ($0.2\text{ km}$ up to $5.8\text{ km}$) and seepage percentage ($2.0\%$ to $28.0\%$).
- **$\text{Water Debt}_i$**: Accumulated verified shortage minutes carried forward from prior rounds.
- **$\beta$ (Beta Weight)**: Slider parameter ($0\%–100\%$, default $80\%$) controlling debt influence on subsequent schedules.
- **$\text{Overdraw Penalty}_i$**: Deductions applied to upstream plots that previously exceeded assigned turns.
- **Supply Constraint & Normalization**: Total allocations strictly constrained by available canal supply budget:
  $$T_{\text{budget}} = \sum D_i \times \frac{\text{Supply}\%}{100}$$
  All allocations $T_i \ge 0$ (no impossible negative schedules).

### 2. Jain’s Fairness Index
$$J = \frac{\left(\sum_{i=1}^{n} x_i\right)^2}{n \sum_{i=1}^{n} x_i^2}$$

Here, $x_i$ represents each plot's fraction of crop-adjusted demand satisfied ($0.0000 \le x_i \le 1.0000$), and $n = 30$ plots.
- **Week 1 Static Baseline**: $J \approx 0.8487$ (severe tail deprivation, head captures full water).
- **KulhWise Week 2 Adjusted**: $J \approx 1.0000$ (equitable demand satisfaction across all reaches).

### 3. Spatial Neighbour Consensus
- For plot $i$, reports are cross-checked against adjacent neighbours $i-1$ and $i+1$.
- **Contradiction Flag**: If Plot $i$ reports "Low/No Water" while neighbours $i-1$ and $i+1$ both received full water, the claim is marked **"Needs Review / Suspected Anomaly"** and water debt is withheld pending Kohli/Panchayat inspection. Contradiction is a flag for human review, never an accusation of fraud.
- **Contiguous Corroboration**: If multiple contiguous tail plots report shortages, it confirms a shared downstream dryout and credits eligible water debt.

---

## 🗺️ 30-Plot Canal Model Data Structure

The prototype simulates 30 realistic plots in downstream sequence along the shared kuhl:

| Reach | Plot IDs | Village | Distance | Est. Seepage Loss | Baseline Status |
|---|---|---|---|---|---|
| **Head** | `#1` – `#10` | Upper Dhar | 0.2 km – 1.8 km | 2.0% – 8.0% | 100% full water delivered |
| **Middle** | `#11` – `#20` | Majhli Basti | 2.0 km – 3.8 km | 9.0% – 17.5% | ~72% effective water (conveyance loss) |
| **Tail** | `#21` – `#30` | Neechla Gaon | 4.0 km – 5.8 km | 19.0% – 28.0% | ~30% effective water (severe starvation) |

---

## 🚀 Quickstart Guide

### 1. Requirements
- Python 3.10+ (Tested on Python 3.14)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 2. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 3. Seed the Baseline Database
```powershell
python backend/seed_data.py
```

### 4. Run the Application
```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

### 5. Open in Browser
👉 Navigate to: **[http://localhost:8000](http://localhost:8000)**  
*(You can also double-click `index.html` directly in your browser for offline standalone mode!)*

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/state` | Returns complete current state: mode, 30 plots, KPI metrics, parameters, activity feed, and ledger status |
| `POST` | `/api/reset` | Resets system state back to the baseline Static Week 1 rotation |
| `POST` | `/api/simulate-week1-chaos` | Injects disruption: Head overdraw (+45 min), tail shortages, and contradiction anomaly at Plot #14 |
| `POST` | `/api/run-week2-scheduler` | Calculates Week 2 schedule with seepage boost, debt compensation, and overdraw penalties |
| `POST` | `/api/bot-report` | Accepts `{ plot_id, report_type }`, executes spatial consensus check, and updates audit ledger |
| `POST` | `/api/tamper-test` | Demo-only: Modifies Block #5 in the audit ledger to demonstrate SHA-256 cryptographic detection |
| `POST` | `/api/repair-ledger` | Restores the verified demo state and rebuilds clean SHA-256 hash chain |
| `GET` | `/api/ledger` | Returns all cryptographic blocks and verification status |

---

## 🎬 3-Minute Hackathon Demo Script

| Time | Action | Presentation Point |
|---|---|---|
| **0:00–0:30** | Show **Overview Dashboard** and Static Week 1. | Point out **Jain's Index: 0.8487**, Head satisfaction at 100%, and Tail satisfaction at 36.2%. The issue is unequal effective delivery, not just timetables. |
| **0:30–0:55** | Scroll down **30-Plot Canal Map**. | Explain Head (green) → Middle → Tail (red shortage). Highlight estimated seepage losses increasing up to 28% at Plot #30. |
| **0:55–1:25** | Click **"Simulate Week 1 Chaos"**. | Observe Head Plot #3 overdrawing (+45 min, purple), tail plots drying out, and Plot #14 triggering a **"Suspected Anomaly"** flag (yellow) due to conflicting neighbour reports. |
| **1:25–1:55** | Click **"Run KulhWise Week 2"**. | Explain how the algorithm applies seepage boost, penalizes Plot #3 (-45 min), and elevates tail turns. Jain's Fairness Index jumps to **1.0000**! |
| **1:55–2:25** | Click **Tail Plot #24 (Mansa Ram)** in Inspector. | Inspect the formula breakdown: Base Share + Seepage Boost + Debt Carry-Forward. Show the plain-language explanation. |
| **2:25–2:45** | Try **Farmer Bot Simulator** (Preset 1 & 2). | Show how contiguous shortages are corroborated, while isolated conflicts are flagged respectfully for Kohli review. |
| **2:45–3:00** | Click **"Simulate Tampering (Block #5)"**. | Show instant red alert: SHA-256 hash mismatch detected at Block #5. Click **"Restore Verified State"** to restore. |

---

## ⚠️ Known Limitations & Responsible Claims

1. **Hardware-Light Simulation**: Flow delivery and effective water volumes are engineering model estimates based on channel geometry and distance; they are not live sensor telemetry.
2. **Neighbour Consensus Bounds**: Spatial cross-checking flags potential inconsistencies for human review; it cannot conclusively prove water theft.
3. **Cryptographic Scope**: SHA-256 hash chaining detects post-hoc data alteration in storage; it does not verify field truthfulness of initial entries and is not a distributed blockchain.
4. **Jain's Metric Scope**: Jain's index measures mathematical equality of demand-satisfaction ratios, not absolute crop yield or complete social fairness.

---

## 👥 Authors
Developed for the **KulhWise Project** — *Digital Kohli Hackathon Build*.
