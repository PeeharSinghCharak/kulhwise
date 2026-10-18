import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
from database import DB_PATH, init_db, calculate_hash, set_metric

FARMERS_DATA = [
    # Head Reach (Privileged, received full water, 0 deficit)
    {"name": "Rajesh Sharma", "village": "Upper Dhar", "plot_acres": 3.5, "crop_type": "Paddy (Rice)", "canal_reach": "Head", "deficit": 0.0, "allocated": 14.0, "received": 14.0, "unwatered": 1},
    {"name": "Sukhvinder Singh", "village": "Upper Dhar", "plot_acres": 4.0, "crop_type": "Wheat", "canal_reach": "Head", "deficit": 0.0, "allocated": 12.0, "received": 12.0, "unwatered": 1},
    {"name": "Virender Kumar", "village": "Upper Dhar", "plot_acres": 2.5, "crop_type": "Sugarcane", "canal_reach": "Head", "deficit": 0.0, "allocated": 11.0, "received": 11.0, "unwatered": 0},
    {"name": "Balwant Negi", "village": "Upper Dhar", "plot_acres": 3.0, "crop_type": "Vegetables", "canal_reach": "Head", "deficit": 0.0, "allocated": 10.5, "received": 10.5, "unwatered": 1},
    {"name": "Kuldeep Thakur", "village": "Upper Dhar", "plot_acres": 2.0, "crop_type": "Paddy (Rice)", "canal_reach": "Head", "deficit": 0.0, "allocated": 9.5, "received": 9.5, "unwatered": 0},
    {"name": "Joginder Pal", "village": "Upper Dhar", "plot_acres": 3.2, "crop_type": "Wheat", "canal_reach": "Head", "deficit": 0.0, "allocated": 9.0, "received": 9.0, "unwatered": 1},
    {"name": "Mohan Lal", "village": "Upper Dhar", "plot_acres": 2.8, "crop_type": "Maize", "canal_reach": "Head", "deficit": 0.0, "allocated": 8.0, "received": 8.0, "unwatered": 2},
    {"name": "Anil Chauhan", "village": "Upper Dhar", "plot_acres": 4.5, "crop_type": "Sugarcane", "canal_reach": "Head", "deficit": 0.0, "allocated": 15.0, "received": 15.0, "unwatered": 1},
    {"name": "Prem Sagar", "village": "Upper Dhar", "plot_acres": 1.8, "crop_type": "Vegetables", "canal_reach": "Head", "deficit": 0.0, "allocated": 6.5, "received": 6.5, "unwatered": 0},
    {"name": "Hukam Chand", "village": "Upper Dhar", "plot_acres": 2.2, "crop_type": "Paddy (Rice)", "canal_reach": "Head", "deficit": 0.0, "allocated": 8.5, "received": 8.5, "unwatered": 1},

    # Middle Reach (Inconsistent, missed 40-50% water)
    {"name": "Sunita Devi", "village": "Majhli Basti", "plot_acres": 2.5, "crop_type": "Wheat", "canal_reach": "Middle", "deficit": 4.5, "allocated": 10.0, "received": 5.5, "unwatered": 4},
    {"name": "Rameshwar Dayal", "village": "Majhli Basti", "plot_acres": 3.0, "crop_type": "Paddy (Rice)", "canal_reach": "Middle", "deficit": 5.0, "allocated": 12.0, "received": 7.0, "unwatered": 3},
    {"name": "Kamla Rawat", "village": "Majhli Basti", "plot_acres": 1.5, "crop_type": "Vegetables", "canal_reach": "Middle", "deficit": 3.5, "allocated": 7.0, "received": 3.5, "unwatered": 5},
    {"name": "Gopal Krishna", "village": "Majhli Basti", "plot_acres": 2.0, "crop_type": "Mustard", "canal_reach": "Middle", "deficit": 4.0, "allocated": 8.0, "received": 4.0, "unwatered": 4},
    {"name": "Dharam Pal", "village": "Majhli Basti", "plot_acres": 3.5, "crop_type": "Wheat", "canal_reach": "Middle", "deficit": 6.0, "allocated": 11.0, "received": 5.0, "unwatered": 5},
    {"name": "Maya Devi", "village": "Majhli Basti", "plot_acres": 2.2, "crop_type": "Maize", "canal_reach": "Middle", "deficit": 4.5, "allocated": 8.5, "received": 4.0, "unwatered": 3},
    {"name": "Santosh Verma", "village": "Majhli Basti", "plot_acres": 2.8, "crop_type": "Apples / Orchard", "canal_reach": "Middle", "deficit": 5.5, "allocated": 9.5, "received": 4.0, "unwatered": 6},
    {"name": "Bhagwan Das", "village": "Majhli Basti", "plot_acres": 3.0, "crop_type": "Pulses (Lentils)", "canal_reach": "Middle", "deficit": 4.0, "allocated": 9.0, "received": 5.0, "unwatered": 4},
    {"name": "Lata Sharma", "village": "Majhli Basti", "plot_acres": 1.9, "crop_type": "Vegetables", "canal_reach": "Middle", "deficit": 3.8, "allocated": 7.5, "received": 3.7, "unwatered": 4},
    {"name": "Kewal Krishan", "village": "Majhli Basti", "plot_acres": 2.4, "crop_type": "Wheat", "canal_reach": "Middle", "deficit": 5.2, "allocated": 9.2, "received": 4.0, "unwatered": 5},

    # Tail Reach (Severely Deprived, 0-10% water received, massive deficits)
    {"name": "Tara Chand (Tail-End)", "village": "Neechla Gaon", "plot_acres": 3.0, "crop_type": "Paddy (Rice)", "canal_reach": "Tail", "deficit": 14.5, "allocated": 15.0, "received": 0.5, "unwatered": 12},
    {"name": "Ganga Ram", "village": "Neechla Gaon", "plot_acres": 2.5, "crop_type": "Wheat", "canal_reach": "Tail", "deficit": 11.0, "allocated": 11.5, "received": 0.5, "unwatered": 10},
    {"name": "Geeta Bai", "village": "Neechla Gaon", "plot_acres": 2.0, "crop_type": "Vegetables", "canal_reach": "Tail", "deficit": 9.5, "allocated": 10.0, "received": 0.5, "unwatered": 9},
    {"name": "Mansa Ram", "village": "Neechla Gaon", "plot_acres": 3.8, "crop_type": "Paddy (Rice)", "canal_reach": "Tail", "deficit": 16.0, "allocated": 16.0, "received": 0.0, "unwatered": 14},
    {"name": "Puran Chand", "village": "Neechla Gaon", "plot_acres": 2.2, "crop_type": "Mustard", "canal_reach": "Tail", "deficit": 10.0, "allocated": 10.0, "received": 0.0, "unwatered": 11},
    {"name": "Bimla Thakur", "village": "Neechla Gaon", "plot_acres": 1.8, "crop_type": "Pulses (Lentils)", "canal_reach": "Tail", "deficit": 8.5, "allocated": 8.5, "received": 0.0, "unwatered": 8},
    {"name": "Chhaju Ram", "village": "Neechla Gaon", "plot_acres": 3.2, "crop_type": "Wheat", "canal_reach": "Tail", "deficit": 13.0, "allocated": 13.5, "received": 0.5, "unwatered": 13},
    {"name": "Shakuntala Devi", "village": "Neechla Gaon", "plot_acres": 2.7, "crop_type": "Maize", "canal_reach": "Tail", "deficit": 12.0, "allocated": 12.0, "received": 0.0, "unwatered": 10},
    {"name": "Devi Dayal", "village": "Neechla Gaon", "plot_acres": 3.4, "crop_type": "Apples / Orchard", "canal_reach": "Tail", "deficit": 14.0, "allocated": 15.0, "received": 1.0, "unwatered": 12},
    {"name": "Om Prakash", "village": "Neechla Gaon", "plot_acres": 2.6, "crop_type": "Paddy (Rice)", "canal_reach": "Tail", "deficit": 12.5, "allocated": 13.0, "received": 0.5, "unwatered": 11},
]

def seed_database():
    """Wipes and seeds the database with the 30 realistic farmers and unfair distribution history."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear old data
    cursor.execute("DELETE FROM distribution_logs")
    cursor.execute("DELETE FROM schedules")
    cursor.execute("DELETE FROM farmers")
    cursor.execute("DELETE FROM system_metrics")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Insert farmers
    farmer_ids = []
    for f in FARMERS_DATA:
        cursor.execute("""
            INSERT INTO farmers (
                name, village, plot_acres, crop_type, canal_reach,
                accumulated_deficit_hours, total_allocated_hours, total_received_hours,
                days_since_last_watered, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f["name"], f["village"], f["plot_acres"], f["crop_type"], f["canal_reach"],
            f["deficit"], f["allocated"], f["received"], f["unwatered"], now
        ))
        farmer_ids.append(cursor.lastrowid)

    conn.commit()

    # Build simulated tamper-evident logs showing historical unfair turns
    prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    base_time = datetime.now() - timedelta(days=5)

    for i, f in enumerate(FARMERS_DATA):
        f_id = farmer_ids[i]
        log_time = (base_time + timedelta(hours=i*3.5)).strftime("%Y-%m-%d %H:%M:%S")

        if f["canal_reach"] == "Head":
            sched_h = round(f["allocated"] / 3.0, 1)
            rec_h = sched_h
            status = "FULL"
            notes = "Full water received at upstream canal gate."
        elif f["canal_reach"] == "Middle":
            sched_h = round(f["allocated"] / 3.0, 1)
            rec_h = round(sched_h * 0.5, 1)
            status = "PARTIAL"
            notes = "Flow pressure reduced due to excessive upstream draw."
        else:
            sched_h = round(f["allocated"] / 3.0, 1)
            rec_h = 0.0
            status = "MISSED"
            notes = "Canal completely dry at tail siphon. Upstream headgate diverted water."

        current_hash = calculate_hash(prev_hash, log_time, f_id, sched_h, rec_h, status, notes)

        cursor.execute("""
            INSERT INTO distribution_logs (
                timestamp, farmer_id, farmer_name, scheduled_hours, 
                actual_received_hours, status, notes, prev_hash, current_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_time, f_id, f["name"], sched_h, rec_h, status, notes, prev_hash, current_hash))

        prev_hash = current_hash

    conn.commit()
    conn.close()

    # Pre-seed metrics
    set_metric("initial_fairness_score", 37.8)
    set_metric("current_fairness_score", 37.8)
    set_metric("projected_fairness_score", 37.8)
    set_metric("algorithm_run_count", 0)

    print("Successfully seeded KulhWise database with 30 farmers and realistic unfair canal history!")
    print("Initial Unfairness State: Head farmers 100%, Mid farmers ~50%, Tail farmers 0-10% water received.")

if __name__ == "__main__":
    seed_database()
