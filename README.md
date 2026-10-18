# 🌾 KulhWise – Smart Water Rotation for Farmers
**Automated, Fair & Tamper-Proof Water Scheduling for Shared Rural & Himalayan Canals ("Kulhs")**

---

## 💡 What is KulhWise?
In communal canal irrigation systems (such as the traditional Himalayan **Kulh** or Northern Indian **Warabandi** systems), water flows down a shared open channel. Farmers at the **head of the canal** often divert more than their share or let water run continuously, while farmers at the **tail end** are starved of water and miss critical watering windows for their crops.

**KulhWise solves this through:**
1. **Algorithmic Fairness**: Rotates canal turns using **Jain’s Fairness Index**, prioritizing farmers who suffered water deficits in previous rounds and dynamically allocating compensatory flow time.
2. **Deficit Compensation Tracking**: If a farmer reports a missed or partial turn, their accumulated deficit directly elevates their priority rank in the next schedule.
3. **Tamper-Evident Cryptographic Ledger**: Every water turn and confirmation is signed into a blockchain-style **SHA-256 hash chain** stored in SQLite, preventing corrupt or secret record alteration.
4. **Interactive Farmer Mobile Simulation**: Allows farmers to confirm full delivery, report partial delivery, or report water theft/diversion directly from their phones.

---

## 📁 Project Directory Structure
```
hack/
│
├── backend/
│   ├── main.py              # FastAPI application & REST API endpoints
│   ├── database.py          # SQLite schema, queries & SHA-256 cryptographic chain
│   ├── algorithm.py         # Priority scheduling & Jain's Fairness Index logic
│   ├── seed_data.py         # 30 simulated farmers with unfair historical imbalance
│   └── kulhwise.db          # Auto-generated SQLite database
│
├── frontend/
│   ├── index.html           # Full self-contained interactive React 18 + Tailwind dashboard
│   ├── package.json         # Node/Vite package setup
│   ├── vite.config.js       # Vite build configuration with API proxying
│   ├── tailwind.config.js   # Tailwind CSS styling configuration
│   ├── postcss.config.js    # PostCSS configuration
│   └── src/
│       ├── main.jsx         # React mounting entrypoint
│       ├── App.jsx          # Main dashboard coordinator
│       ├── index.css        # Tailwind directives
│       └── components/
│           ├── OverviewPanel.jsx       # Fairness score gauge & demo trigger
│           ├── ScheduleTimeline.jsx    # Visual timeline of today's rotation
│           ├── FarmerSimulation.jsx    # Farmer mobile confirmation node
│           └── TransparentLedger.jsx   # Tamper-proof SHA-256 historical ledger
│
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation & run guide
```

---

## 🚀 Quickstart Guide (Step-by-Step for Beginners)

### Step 1: Open Terminal in Project Directory
Open PowerShell or your terminal in the project directory:
```powershell
cd c:\Users\chara\OneDrive\Documents\hack
```

### Step 2: Install Python Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Seed the Database with Unfair Baseline Data
```powershell
python backend/seed_data.py
```
> This populates 30 farmers across **Head, Middle, and Tail** canal sections. Head farmers start with 100% water satisfaction, while Tail farmers have accumulated heavy deficits (~121 hours total deficit).

### Step 4: Start the KulhWise Application
```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

### Step 5: Open in Your Browser
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🎬 How to Give a 2-Minute Winning Hackathon Demo

1. **Show the Problem (Baseline State)**:
   - Point out the **System Fairness Score** gauge showing **~29% - 37% (Severe Tail Deprivation)**.
   - Point out the metrics: **Head-reach deficit is 0 hrs**, while **Tail-reach deficit is 121 hrs**.

2. **Trigger the Algorithm**:
   - Click the prominent **"⚡ Run KulhWise Algorithm"** button.
   - Watch the score instantly jump to **94.2% (Fair & Balanced)**!
   - Scroll to **Today's Rotation Schedule**: Show how tail-end farmers (**Mansa Ram**, **Tara Chand**, **Devi Dayal**) were prioritized at **Rank #1, #2, #3** with compensatory bonus hours added.

3. **Demonstrate Farmer Feedback & Ledger**:
   - Scroll to the **Farmer Simulation Panel**.
   - Select a farmer (e.g. *Tara Chand* or *Geeta Bai*).
   - Select **"Report Water Missed"** or **"Confirm Water Received"** and click **Submit**.
   - Show how the confirmation is instantly added to the **Transparent Distribution Ledger** below with a verifiable **SHA-256 Cryptographic Hash**!

4. **Reset Anytime**:
   - Click **"↺ Reset to Unfair Baseline"** at the top to reset the database and repeat the demo anytime!

---

## 🔌 API Endpoints Reference
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/farmers` | List all 30 farmers with their plot sizes, crops, and deficit status |
| `POST` | `/schedule/generate` | Runs the KulhWise fairness algorithm and generates rotation |
| `GET` | `/schedule` | Fetches today's active rotation schedule |
| `POST` | `/turn/confirm` | Confirms water delivery (`FULL`, `PARTIAL`, `MISSED`) & updates ledger |
| `GET` | `/logs` | Returns cryptographic distribution ledger & verification proof |
| `GET` | `/stats` | Returns system overview statistics and fairness index |
| `POST` | `/reset` | Resets database back to the initial unfair demo baseline |
