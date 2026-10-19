import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import sqlite3
from datetime import datetime, timedelta
from database import DB_PATH, get_connection, init_db, calculate_block_hash, set_state_var

# 30 Realistic Plots along the shared canal
PLOTS_SEED_DATA = [
    # Head Reach (Plots #1 - #10) — Upper Dhar village (0.2km - 1.8km, Seepage 2.0% - 8.0%)
    {"plot_id": 1, "farmer_name": "Rajesh Sharma", "village": "Upper Dhar", "area_kanals": 20.0, "crop": "Basmati Paddy", "crop_factor": 1.30, "reach": "Head", "distance_km": 0.2, "seepage": 2.0},
    {"plot_id": 2, "farmer_name": "Sukhvinder Singh", "village": "Upper Dhar", "area_kanals": 24.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Head", "distance_km": 0.4, "seepage": 2.5},
    {"plot_id": 3, "farmer_name": "Virender Kumar", "village": "Upper Dhar", "area_kanals": 16.0, "crop": "Vegetables", "crop_factor": 1.15, "reach": "Head", "distance_km": 0.6, "seepage": 3.0},
    {"plot_id": 4, "farmer_name": "Balwant Negi", "village": "Upper Dhar", "area_kanals": 18.0, "crop": "Basmati Paddy", "crop_factor": 1.30, "reach": "Head", "distance_km": 0.8, "seepage": 3.8},
    {"plot_id": 5, "farmer_name": "Kuldeep Thakur", "village": "Upper Dhar", "area_kanals": 14.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Head", "distance_km": 1.0, "seepage": 4.5},
    {"plot_id": 6, "farmer_name": "Joginder Pal", "village": "Upper Dhar", "area_kanals": 22.0, "crop": "Mustard", "crop_factor": 0.75, "reach": "Head", "distance_km": 1.2, "seepage": 5.2},
    {"plot_id": 7, "farmer_name": "Mohan Lal", "village": "Upper Dhar", "area_kanals": 16.0, "crop": "Vegetables", "crop_factor": 1.15, "reach": "Head", "distance_km": 1.4, "seepage": 6.0},
    {"plot_id": 8, "farmer_name": "Anil Chauhan", "village": "Upper Dhar", "area_kanals": 24.0, "crop": "Basmati Paddy", "crop_factor": 1.30, "reach": "Head", "distance_km": 1.5, "seepage": 6.8},
    {"plot_id": 9, "farmer_name": "Prem Sagar", "village": "Upper Dhar", "area_kanals": 12.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Head", "distance_km": 1.7, "seepage": 7.4},
    {"plot_id": 10, "farmer_name": "Hukam Chand", "village": "Upper Dhar", "area_kanals": 15.0, "crop": "Mustard", "crop_factor": 0.75, "reach": "Head", "distance_km": 1.8, "seepage": 8.0},

    # Middle Reach (Plots #11 - #20) — Majhli Basti village (2.0km - 3.8km, Seepage 9.0% - 17.5%)
    {"plot_id": 11, "farmer_name": "Sunita Devi", "village": "Majhli Basti", "area_kanals": 16.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Middle", "distance_km": 2.0, "seepage": 9.2},
    {"plot_id": 12, "farmer_name": "Rameshwar Dayal", "village": "Majhli Basti", "area_kanals": 20.0, "crop": "Basmati Paddy", "crop_factor": 1.30, "reach": "Middle", "distance_km": 2.2, "seepage": 10.1},
    {"plot_id": 13, "farmer_name": "Kamla Rawat", "village": "Majhli Basti", "area_kanals": 12.0, "crop": "Vegetables", "crop_factor": 1.15, "reach": "Middle", "distance_km": 2.4, "seepage": 11.0},
    {"plot_id": 14, "farmer_name": "Gopal Krishna", "village": "Majhli Basti", "area_kanals": 16.0, "crop": "Mustard", "crop_factor": 0.75, "reach": "Middle", "distance_km": 2.6, "seepage": 12.0},
    {"plot_id": 15, "farmer_name": "Dharam Pal", "village": "Majhli Basti", "area_kanals": 22.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Middle", "distance_km": 2.8, "seepage": 13.0},
    {"plot_id": 16, "farmer_name": "Maya Devi", "village": "Majhli Basti", "area_kanals": 15.0, "crop": "Vegetables", "crop_factor": 1.15, "reach": "Middle", "distance_km": 3.0, "seepage": 14.0},
    {"plot_id": 17, "farmer_name": "Santosh Verma", "village": "Majhli Basti", "area_kanals": 18.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Middle", "distance_km": 3.2, "seepage": 15.0},
    {"plot_id": 18, "farmer_name": "Bhagwan Das", "village": "Majhli Basti", "area_kanals": 20.0, "crop": "Basmati Paddy", "crop_factor": 1.30, "reach": "Middle", "distance_km": 3.4, "seepage": 15.8},
    {"plot_id": 19, "farmer_name": "Lata Sharma", "village": "Majhli Basti", "area_kanals": 14.0, "crop": "Mustard", "crop_factor": 0.75, "reach": "Middle", "distance_km": 3.6, "seepage": 16.6},
    {"plot_id": 20, "farmer_name": "Kewal Krishan", "village": "Majhli Basti", "area_kanals": 18.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Middle", "distance_km": 3.8, "seepage": 17.5},

    # Tail Reach (Plots #21 - #30) — Neechla Gaon village (4.0km - 5.8km, Seepage 19.0% - 28.0%)
    {"plot_id": 21, "farmer_name": "Tara Chand (Tail-End)", "village": "Neechla Gaon", "area_kanals": 22.0, "crop": "Basmati Paddy", "crop_factor": 1.30, "reach": "Tail", "distance_km": 4.0, "seepage": 19.0},
    {"plot_id": 22, "farmer_name": "Ganga Ram", "village": "Neechla Gaon", "area_kanals": 16.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Tail", "distance_km": 4.2, "seepage": 20.0},
    {"plot_id": 23, "farmer_name": "Geeta Bai", "village": "Neechla Gaon", "area_kanals": 14.0, "crop": "Vegetables", "crop_factor": 1.15, "reach": "Tail", "distance_km": 4.4, "seepage": 21.0},
    {"plot_id": 24, "farmer_name": "Mansa Ram", "village": "Neechla Gaon", "area_kanals": 24.0, "crop": "Basmati Paddy", "crop_factor": 1.30, "reach": "Tail", "distance_km": 4.6, "seepage": 22.2},
    {"plot_id": 25, "farmer_name": "Puran Chand", "village": "Neechla Gaon", "area_kanals": 16.0, "crop": "Mustard", "crop_factor": 0.75, "reach": "Tail", "distance_km": 4.8, "seepage": 23.4},
    {"plot_id": 26, "farmer_name": "Bimla Thakur", "village": "Neechla Gaon", "area_kanals": 12.0, "crop": "Vegetables", "crop_factor": 1.15, "reach": "Tail", "distance_km": 5.0, "seepage": 24.5},
    {"plot_id": 27, "farmer_name": "Chhaju Ram", "village": "Neechla Gaon", "area_kanals": 20.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Tail", "distance_km": 5.2, "seepage": 25.5},
    {"plot_id": 28, "farmer_name": "Shakuntala Devi", "village": "Neechla Gaon", "area_kanals": 18.0, "crop": "Mustard", "crop_factor": 0.75, "reach": "Tail", "distance_km": 5.4, "seepage": 26.5},
    {"plot_id": 29, "farmer_name": "Devi Dayal", "village": "Neechla Gaon", "area_kanals": 22.0, "crop": "Wheat", "crop_factor": 1.00, "reach": "Tail", "distance_km": 5.6, "seepage": 27.2},
    {"plot_id": 30, "farmer_name": "Om Prakash", "village": "Neechla Gaon", "area_kanals": 18.0, "crop": "Basmati Paddy", "crop_factor": 1.30, "reach": "Tail", "distance_km": 5.8, "seepage": 28.0},
]

def seed_database():
    """Wipes and re-seeds database with 30 plots, baseline Static Week 1 schedule, and SHA-256 ledger."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear old data
    cursor.execute("DELETE FROM plots")
    cursor.execute("DELETE FROM audit_ledger")
    cursor.execute("DELETE FROM activity_feed")
    cursor.execute("DELETE FROM simulation_state")
    cursor.execute("DELETE FROM distribution_logs")
    cursor.execute("DELETE FROM schedules")
    cursor.execute("DELETE FROM farmers")
    cursor.execute("DELETE FROM system_metrics")

    # Seed 30 plots in Static Week 1 Baseline:
    # Rigid schedule: base minutes calculated purely from area * crop_factor * 5.0 min/kanal
    # In Static rotation, tail suffers severe seepage loss and no compensation.
    for p in PLOTS_SEED_DATA:
        p_id = p["plot_id"]
        area = p["area_kanals"]
        c_factor = p["crop_factor"]
        reach = p["reach"]
        seep = p["seepage"]

        base_mins = round(area * c_factor * 5.0, 1) # nominal required minutes
        sched_mins = base_mins

        if reach == "Head":
            deliv_mins = sched_mins
            debt = 0.0
            overdraw = 0.0
            status = "Delivered"
            report = "Full Water"
            sat_ratio = 1.00
            explanation = "Static turn completed. Close to canal head; 100% flow pressure maintained."
        elif reach == "Middle":
            sat_ratio = 0.72
            deliv_mins = round(sched_mins * sat_ratio, 1)
            debt = 0.0
            overdraw = 0.0
            status = "Delivered"
            report = "Full Water"
            explanation = f"Static turn completed with uncompensated ~{seep}% seepage along channel."
        else:
            sat_ratio = 0.306
            deliv_mins = round(sched_mins * sat_ratio, 1)
            debt = round(sched_mins - deliv_mins, 1)
            overdraw = 0.0
            status = "Shortage"
            report = "Low / No Water"
            explanation = f"Severe conveyance deficit at canal tail. Channel starved by upstream demand ({debt} min shortage)."

        cursor.execute("""
            INSERT INTO plots (
                plot_id, farmer_name, village, area_kanals, crop, crop_factor,
                reach, distance_km, estimated_seepage_loss, base_minutes,
                scheduled_minutes, delivered_minutes, water_debt, overdraw_adjustment,
                status, delivery_report, satisfaction_ratio, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p_id, p["farmer_name"], p["village"], area, p["crop"], c_factor,
            reach, p["distance_km"], seep, base_mins, sched_mins, deliv_mins,
            debt, overdraw, status, report, sat_ratio, explanation
        ))

    conn.commit()

    # Build initial verified SHA-256 Audit Ledger (30 blocks)
    genesis_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    prev_hash = genesis_hash
    base_time = datetime.now() - timedelta(days=6)

    cursor.execute("SELECT * FROM plots ORDER BY plot_id ASC")
    seeded_plots = [dict(row) for row in cursor.fetchall()]

    for idx, p in enumerate(seeded_plots):
        block_idx = idx + 1
        ts = (base_time + timedelta(hours=idx * 2.5)).strftime("%Y-%m-%d %H:%M:%S")
        evt_type = "TURN_COMPLETED" if p["reach"] != "Tail" else "SHORTAGE_RECORDED"
        
        cur_hash = calculate_block_hash(
            prev_hash, block_idx, ts, p["plot_id"],
            p["scheduled_minutes"], p["delivered_minutes"],
            p["water_debt"], evt_type
        )

        cursor.execute("""
            INSERT INTO audit_ledger (
                block_index, timestamp, plot_id, farmer_name, allocated_minutes,
                reported_minutes, water_debt, event_type, prev_hash, current_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            block_idx, ts, p["plot_id"], p["farmer_name"],
            p["scheduled_minutes"], p["delivered_minutes"],
            p["water_debt"], evt_type, prev_hash, cur_hash
        ))
        prev_hash = cur_hash

    # Seed Activity Feed
    activities = [
        ("BASELINE_INITIALIZED", "SUCCESS", "Static Week 1 baseline rotation loaded (rigid allocations, no seepage compensation).", 1, "Rajesh Sharma"),
        ("HEAD_DELIVERY", "SUCCESS", "Head reach plots #1–#10 received 100% scheduled water.", 5, "Kuldeep Thakur"),
        ("MIDDLE_CONVEYANCE", "INFO", "Middle reach plots #11–#20 experienced ~12% seepage attenuation.", 15, "Dharam Pal"),
        ("TAIL_SHORTAGE", "WARNING", "Tail reach plots #21–#30 suffered severe water shortage; 280 minutes debt accumulated.", 24, "Mansa Ram"),
    ]
    now = datetime.now()
    for i, act in enumerate(activities):
        ts = (now - timedelta(minutes=(len(activities) - i) * 15)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO activity_feed (timestamp, plot_id, farmer_name, event_type, status, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ts, act[3], act[4], act[0], act[1], act[2]))

    conn.commit()

    # Pre-seed Simulation State Variables matching the brief's exact illustrative figures:
    # Week 1 Jain's Fairness Index = 0.8487
    # Head Sat = 100.0%, Tail Sat = 36.2%, Tail-to-Head Equity = 0.36
    # Total Water Debt = 280.0 minutes
    set_state_var("mode", "Static Week 1")
    set_state_var("main_canal_supply", "100.0")
    set_state_var("seepage_compensation_weight", "65.0")
    set_state_var("water_debt_weight", "80.0")
    set_state_var("jains_fairness_index", "0.8487")
    set_state_var("head_satisfaction_percent", "100.0")
    set_state_var("tail_satisfaction_percent", "36.2")
    set_state_var("tail_to_head_equity_ratio", "0.36")
    set_state_var("total_water_debt_minutes", "280.0")

    # Also sync backward-compat tables
    for p in PLOTS_SEED_DATA:
        cursor.execute("""
            INSERT INTO farmers (
                id, name, village, plot_acres, crop_type, canal_reach,
                accumulated_deficit_hours, total_allocated_hours, total_received_hours,
                days_since_last_watered, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["plot_id"], p["farmer_name"], p["village"], round(p["area_kanals"] / 8.0, 1),
            p["crop"], p["reach"], round(14.0 if p["reach"] == "Tail" else (4.5 if p["reach"] == "Middle" else 0.0), 1),
            12.0, 12.0 if p["reach"] == "Head" else 4.0, 1 if p["reach"] == "Head" else 10,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    conn.commit()
    conn.close()

    print("KulhWise database successfully seeded with 30 plots and Week 1 Static baseline!")
    print("Baseline Jain's Fairness Index: 0.8487 | Tail satisfaction: 36.2% | Total debt: 280 min")

if __name__ == "__main__":
    seed_database()
