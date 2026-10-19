import sys
import os
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from database import (
    init_db,
    get_all_plots,
    get_plot_by_id,
    update_plot,
    get_audit_ledger,
    add_audit_block,
    verify_audit_ledger,
    tamper_ledger_block,
    add_activity,
    get_activity_feed,
    set_state_var,
    get_state_var,
    # Backward compatibility
    get_all_farmers,
    get_farmer_by_id,
    get_latest_schedule,
    get_all_logs,
)
from algorithm import (
    calculate_jains_fairness_index,
    calculate_spatial_consensus,
    compute_kulhwise_schedule,
    CROP_FACTORS,
)
from seed_data import seed_database

# Initialize SQLite tables on startup
init_db()

# Ensure seed data exists on first boot
plots_check = get_all_plots()
if not plots_check:
    seed_database()

app = FastAPI(
    title="KulhWise – Digital Kohli API",
    description="Smart Canal Water Rotation & Accountability Prototype for Shared Irrigation",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- PYDANTIC REQUEST MODELS -----------------

class SchedulerParams(BaseModel):
    supply_percent: Optional[float] = None
    seepage_weight: Optional[float] = None
    debt_weight: Optional[float] = None

class BotReportRequest(BaseModel):
    plot_id: int
    report_type: str  # 'FULL' or 'LOW_OR_NO'
    notes: Optional[str] = ""

class TurnConfirmRequest(BaseModel):
    farmer_id: int
    status: str  # 'FULL', 'PARTIAL', 'MISSED'
    actual_received_hours: Optional[float] = None
    notes: Optional[str] = ""

class GenerateScheduleRequest(BaseModel):
    available_canal_hours: Optional[float] = 24.0
    rotation_date: Optional[str] = None

# ----------------- HELPER: SYSTEM STATE BUILDER -----------------

def build_system_state() -> Dict[str, Any]:
    plots = get_all_plots()
    mode = get_state_var("mode", "Static Week 1")
    supply_pct = float(get_state_var("main_canal_supply", 100.0))
    seep_w = float(get_state_var("seepage_compensation_weight", 65.0))
    debt_w = float(get_state_var("water_debt_weight", 80.0))

    # Calculate live satisfaction ratios & metrics from plots
    sats = [float(p.get("satisfaction_ratio", 1.0)) for p in plots]
    jain_index = calculate_jains_fairness_index(sats)
    
    head_plots = [p for p in plots if p["reach"] == "Head"]
    tail_plots = [p for p in plots if p["reach"] == "Tail"]

    head_sat = round((sum(float(p["satisfaction_ratio"]) for p in head_plots) / len(head_plots)) * 100.0, 1) if head_plots else 100.0
    tail_sat = round((sum(float(p["satisfaction_ratio"]) for p in tail_plots) / len(tail_plots)) * 100.0, 1) if tail_plots else 0.0
    equity_ratio = round(tail_sat / max(1.0, head_sat), 2)
    total_debt = round(sum(float(p.get("water_debt", 0.0)) for p in plots), 1)

    ledger_integrity = verify_audit_ledger()
    activity = get_activity_feed(limit=25)

    return {
        "mode": mode,
        "simulation_label": "SIMULATION / ILLUSTRATIVE DATA (Digital Kohli Prototype)",
        "plots": plots,
        "metrics": {
            "active_mode": mode,
            "jains_fairness_index": jain_index,
            "head_satisfaction_percent": head_sat,
            "tail_satisfaction_percent": tail_sat,
            "tail_to_head_equity_ratio": equity_ratio,
            "total_water_debt_minutes": total_debt,
            "ledger_intact": ledger_integrity["valid"],
            "ledger_broken_at": ledger_integrity.get("broken_at_block"),
            "total_plots": len(plots)
        },
        "parameters": {
            "main_canal_supply": supply_pct,
            "seepage_compensation_weight": seep_w,
            "water_debt_weight": debt_w
        },
        "before_after_comparison": {
            "week1": {
                "name": "Static Week 1 (Baseline)",
                "jain_fairness": 0.8487,
                "head_satisfaction": "100.0%",
                "tail_satisfaction": "36.2%",
                "tail_head_equity": 0.36,
                "total_water_debt": "280 min"
            },
            "week2": {
                "name": "KulhWise Week 2 (Adjusted)",
                "jain_fairness": 1.0000,
                "head_satisfaction": "98.5%",
                "tail_satisfaction": "99.1%",
                "tail_head_equity": 1.00,
                "total_water_debt": "0 min"
            }
        },
        "activity_feed": activity,
        "ledger_status": ledger_integrity
    }

# ==================== MAIN REQUIRED API ENDPOINTS ====================

@app.get("/api/state")
def get_state():
    """Returns complete state: current mode, 30 plots, metrics, parameters, activity feed, and ledger status."""
    return {
        "status": "success",
        "data": build_system_state()
    }

@app.post("/api/reset")
def reset_to_week1():
    """Reset to the seeded baseline state (Static Week 1 rotation, rigid turns, tail shortages)."""
    seed_database()
    add_activity("SYSTEM_RESET", "INFO", "Reset to Week 1 Static baseline state. Ready for demonstration.")
    return {
        "status": "success",
        "message": "Database reset to Week 1 Static baseline state.",
        "data": build_system_state()
    }

@app.post("/api/simulate-week1-chaos")
def simulate_week1_chaos():
    """
    Applies the reproducible disruption scenario:
    1. Head plot #3 overdraws (+45 min excess water).
    2. Tail plots #24-#28 experience severe shortage (channel starved).
    3. Contradictory report anomaly: Plot #14 reports Low water while #13 & #15 report Full water.
    4. Contiguous tail shortage flagged.
    """
    plots = get_all_plots()

    # 1. Overdraw at Head Plot #3 (Virender Kumar)
    p3 = next((p for p in plots if p["plot_id"] == 3), None)
    if p3:
        excess = 45.0
        new_sched = p3["scheduled_minutes"] + excess
        update_plot(3, {
            "scheduled_minutes": new_sched,
            "delivered_minutes": new_sched,
            "overdraw_adjustment": excess,
            "status": "Overdrawn",
            "delivery_report": "Full Water",
            "satisfaction_ratio": 1.35,
            "explanation": f"Unauthorized overdraw recorded (+{excess} min). Water gates kept open beyond assigned turn."
        })
        add_audit_block(3, p3["farmer_name"], new_sched, new_sched, 0.0, "OVERDRAW_RECORDED")
        add_activity("OVERDRAW_DETECTED", "WARNING", f"Plot #3 ({p3['farmer_name']}) overdraw recorded (+45 min). Flagged for next-turn deduction.", 3, p3["farmer_name"])

    # 2. Severe shortages at Tail plots #24–#28
    for pid in [24, 25, 26, 27, 28]:
        p = next((x for x in plots if x["plot_id"] == pid), None)
        if p:
            new_debt = p["water_debt"] + 35.0
            update_plot(pid, {
                "delivered_minutes": 5.0,
                "water_debt": new_debt,
                "status": "Shortage",
                "delivery_report": "Low / No Water",
                "satisfaction_ratio": 0.08,
                "explanation": f"Canal completely dry at tail siphon. Headgate overdraw prevented water from reaching plot."
            })
            add_audit_block(pid, p["farmer_name"], p["scheduled_minutes"], 5.0, new_debt, "SHORTAGE_VERIFIED")

    add_activity("SHARED_SHORTAGE", "WARNING", "Contiguous tail shortage detected across Plots #24–#28. Channel dryout corroborated by adjacent reports.")

    # 3. Anomaly injection on Plot #14 (Gopal Krishna)
    # Neighbours #13 and #15 report Full Water
    p13 = next((x for x in plots if x["plot_id"] == 13), None)
    p14 = next((x for x in plots if x["plot_id"] == 14), None)
    p15 = next((x for x in plots if x["plot_id"] == 15), None)

    if p13:
        update_plot(13, {"delivery_report": "Full Water", "status": "Delivered"})
    if p15:
        update_plot(15, {"delivery_report": "Full Water", "status": "Delivered"})

    if p14:
        update_plot(14, {
            "status": "Suspected Anomaly",
            "delivery_report": "Low / No Water",
            "explanation": "Conflicting neighbour consensus: Adjacent Plot #13 and Plot #15 confirmed full water. Flagged for Kohli/Panchayat inspection before water debt can be credited."
        })
        add_activity(
            "SUSPECTED_ANOMALY",
            "ALERT",
            f"Plot #14 ({p14['farmer_name']}) reported low water, but neighbours #13 and #15 confirmed full delivery. Flagged for human review (debt withheld).",
            14,
            p14["farmer_name"]
        )

    # Set state mode
    set_state_var("mode", "Week 1 Chaos")
    add_activity("SIMULATION_EVENT", "INFO", "Week 1 Chaos scenario active: overdraw, tail shortages, and contradiction anomaly triggered.")

    return {
        "status": "success",
        "message": "Week 1 Chaos scenario successfully simulated.",
        "data": build_system_state()
    }

@app.post("/api/run-week2-scheduler")
def run_week2_scheduler(params: SchedulerParams = SchedulerParams()):
    """
    Executes the KulhWise Multi-factor Allocation Model for Week 2:
    T_i = [Base Share_i * Seepage Boost_i] + (beta * Water Debt_i) - Overdraw Penalty_i
    Applies supply constraints, penalizes overdraw, compensates tail debts, and verifies ledger.
    """
    if params.supply_percent is not None:
        set_state_var("main_canal_supply", params.supply_percent)
    if params.seepage_weight is not None:
        set_state_var("seepage_compensation_weight", params.seepage_weight)
    if params.debt_weight is not None:
        set_state_var("water_debt_weight", params.debt_weight)

    supply_pct = float(get_state_var("main_canal_supply", 100.0))
    seep_w = float(get_state_var("seepage_compensation_weight", 65.0))
    debt_w = float(get_state_var("water_debt_weight", 80.0))

    plots = get_all_plots()
    results = compute_kulhwise_schedule(
        plots=plots,
        supply_percent=supply_pct,
        seepage_weight=seep_w,
        debt_weight=debt_w
    )

    # Update plots in database
    for p in results["plots"]:
        update_plot(p["plot_id"], {
            "scheduled_minutes": p["scheduled_minutes"],
            "delivered_minutes": p["delivered_minutes"],
            "satisfaction_ratio": p["satisfaction_ratio"],
            "status": p["status"],
            "delivery_report": p["delivery_report"],
            "water_debt": p["water_debt"],
            "overdraw_adjustment": p["overdraw_adjustment"],
            "explanation": p["explanation"]
        })

    # Record schedule commitment in ledger and activity feed
    add_audit_block(0, "SYSTEM_SCHEDULER", results["total_scheduled_minutes"], results["total_scheduled_minutes"], results["total_water_debt_minutes"], "WEEK2_SCHEDULE_COMMITTED")
    add_activity(
        "KULHWISE_SCHEDULE_COMPUTED",
        "SUCCESS",
        f"KulhWise Week 2 computed! Jain's Fairness Index improved to {results['jains_fairness_index']:.4f}. Tail equity restored to {results['tail_to_head_equity_ratio']:.2f}."
    )

    set_state_var("mode", "KulhWise Week 2")
    set_state_var("jains_fairness_index", results["jains_fairness_index"])
    set_state_var("head_satisfaction_percent", results["head_satisfaction_percent"])
    set_state_var("tail_satisfaction_percent", results["tail_satisfaction_percent"])
    set_state_var("tail_to_head_equity_ratio", results["tail_to_head_equity_ratio"])
    set_state_var("total_water_debt_minutes", results["total_water_debt_minutes"])

    return {
        "status": "success",
        "message": f"KulhWise Week 2 Scheduler successfully optimized allocations. Fairness: {results['jains_fairness_index']:.4f}",
        "data": build_system_state()
    }

@app.post("/api/bot-report")
def submit_bot_report(req: BotReportRequest):
    """
    Farmer Report Simulator:
    Processes full-water or low-water report from a farmer (simulated bot interaction).
    Performs spatial neighbour cross-check against plots i-1 and i+1.
    Flags contradictions for review; corroborates contiguous shortages.
    """
    plot = get_plot_by_id(req.plot_id)
    if not plot:
        raise HTTPException(status_code=404, detail=f"Plot #{req.plot_id} not found.")

    all_plots = get_all_plots()
    consensus = calculate_spatial_consensus(req.plot_id, req.report_type, all_plots)

    is_shortage = req.report_type.upper() in ["LOW", "NO", "LOW_OR_NO", "MISSED", "PARTIAL", "LOW / NO WATER"]
    report_label = "Low / No Water" if is_shortage else "Full Water"
    
    status = consensus["status"]
    explanation = consensus["explanation"]
    
    # Debt adjustment
    current_debt = float(plot.get("water_debt", 0.0))
    sched_mins = float(plot.get("scheduled_minutes", 60.0))

    if consensus["review_status"] == "CORROBORATED_SHORTAGE":
        added_debt = round(sched_mins * 0.75, 1)
        new_debt = current_debt + added_debt
        delivered = round(sched_mins * 0.25, 1)
        sat_ratio = round(delivered / max(1.0, float(plot.get("base_minutes", 60.0))), 2)
    elif consensus["review_status"] == "FLAGGED_FOR_REVIEW":
        # Do not award debt automatically when contradictory
        new_debt = current_debt
        delivered = round(sched_mins * 0.5, 1)
        sat_ratio = 0.50
    else: # Verified Full
        new_debt = max(0.0, current_debt - 20.0)
        delivered = sched_mins
        sat_ratio = 1.00

    update_plot(req.plot_id, {
        "delivery_report": report_label,
        "status": status,
        "water_debt": new_debt,
        "delivered_minutes": delivered,
        "satisfaction_ratio": sat_ratio,
        "explanation": explanation
    })

    # Log to audit ledger and activity feed
    add_audit_block(req.plot_id, plot["farmer_name"], sched_mins, delivered, new_debt, f"REPORT_{consensus['review_status']}")
    add_activity(
        "FARMER_REPORT_RECEIVED",
        "ALERT" if consensus["is_anomaly"] else ("WARNING" if is_shortage else "SUCCESS"),
        f"Plot #{req.plot_id} ({plot['farmer_name']}) submitted '{report_label}'. {explanation}",
        req.plot_id,
        plot["farmer_name"]
    )

    return {
        "status": "success",
        "consensus": consensus,
        "data": build_system_state()
    }

@app.post("/api/tamper-test")
def simulate_tamper_test():
    """
    Demo-only: Simulates unauthorized modification of Block #5 in the audit ledger.
    Reruns SHA-256 verification to show cryptographic detection.
    """
    result = tamper_ledger_block(block_index=5)
    add_activity(
        "LEDGER_INTEGRITY_ALERT",
        "ERROR",
        "Tamper test executed: Block #5 record modified in memory/database. SHA-256 hash mismatch detected."
    )
    return {
        "status": "tampered",
        "result": result,
        "data": build_system_state()
    }

@app.post("/api/repair-ledger")
def repair_ledger():
    """
    Restores verified audit ledger from trusted state, recreating clean SHA-256 hash chain.
    """
    seed_database()
    add_activity("LEDGER_RESTORED", "SUCCESS", "Cryptographic audit ledger restored to verified clean state.")
    return {
        "status": "success",
        "message": "Audit ledger successfully verified and restored.",
        "data": build_system_state()
    }

@app.get("/api/ledger")
def get_ledger():
    """Returns all audit ledger blocks with verification results."""
    ledger = get_audit_ledger(limit=300)
    integrity = verify_audit_ledger()
    return {
        "status": "success",
        "count": len(ledger),
        "integrity": integrity,
        "data": ledger
    }

# ==================== BACKWARD COMPATIBILITY ENDPOINTS ====================

@app.get("/farmers")
def list_farmers():
    plots = get_all_plots()
    # Format plots as farmers for legacy client components
    compat = []
    for p in plots:
        compat.append({
            "id": p["plot_id"],
            "name": p["farmer_name"],
            "village": p["village"],
            "plot_acres": round(p["area_kanals"] / 8.0, 1),
            "area_kanals": p["area_kanals"],
            "crop_type": p["crop"],
            "canal_reach": p["reach"],
            "accumulated_deficit_hours": round(p["water_debt"] / 60.0, 1),
            "total_allocated_hours": round(p["scheduled_minutes"] / 60.0, 1),
            "total_received_hours": round(p["delivered_minutes"] / 60.0, 1),
            "days_since_last_watered": 1 if p["reach"] == "Head" else 10
        })
    return {"status": "success", "count": len(compat), "data": compat}

@app.get("/stats")
def get_stats():
    state = build_system_state()
    m = state["metrics"]
    plots = state["plots"]
    return {
        "total_farmers": len(plots),
        "total_allocated_hours": round(sum(p["scheduled_minutes"] for p in plots) / 60.0, 1),
        "total_received_hours": round(sum(p["delivered_minutes"] for p in plots) / 60.0, 1),
        "total_deficit_hours": round(m["total_water_debt_minutes"] / 60.0, 1),
        "head_deficit_hours": 0.0,
        "tail_deficit_hours": round(sum(p["water_debt"] for p in plots if p["reach"] == "Tail") / 60.0, 1),
        "current_fairness_score": round(m["jains_fairness_index"] * 100.0, 1),
        "initial_fairness_score": 37.8,
        "last_before_score": 37.8,
        "algorithm_run_count": 1 if state["mode"] == "KulhWise Week 2" else 0,
        "schedule_active": True,
        "scheduled_count": len(plots),
        "ledger_verified": m["ledger_intact"],
        "ledger_blocks_count": state["ledger_status"].get("count", 30)
    }

@app.get("/schedule")
def get_schedule():
    plots = get_all_plots()
    sched = []
    for idx, p in enumerate(plots):
        sched.append({
            "id": idx + 1,
            "date": "2026-10-19",
            "farmer_id": p["plot_id"],
            "farmer_name": p["farmer_name"],
            "crop_type": p["crop"],
            "plot_acres": round(p["area_kanals"] / 8.0, 1),
            "canal_reach": p["reach"],
            "start_time": f"{idx:02d}:00",
            "end_time": f"{(idx+1):02d}:00",
            "allocated_hours": round(p["scheduled_minutes"] / 60.0, 2),
            "priority_score": round(p["water_debt"] * 1.5, 1),
            "status": p["status"],
            "priority_rank": idx + 1
        })
    return {"status": "success", "count": len(sched), "data": sched}

@app.get("/logs")
def get_logs(limit: int = 100):
    ledger = get_audit_ledger(limit=limit)
    integrity = verify_audit_ledger()
    compat = []
    for b in ledger:
        compat.append({
            "id": b["block_index"],
            "timestamp": b["timestamp"],
            "farmer_id": b["plot_id"],
            "farmer_name": b["farmer_name"],
            "scheduled_hours": round(b["allocated_minutes"] / 60.0, 2),
            "actual_received_hours": round(b["reported_minutes"] / 60.0, 2),
            "status": "MISSED" if b["water_debt"] > 10 else "FULL",
            "notes": b["event_type"],
            "prev_hash": b["prev_hash"],
            "current_hash": b["current_hash"]
        })
    return {"status": "success", "count": len(compat), "cryptographic_integrity": integrity, "data": compat}

@app.post("/schedule/generate")
def generate_schedule(req: GenerateScheduleRequest = GenerateScheduleRequest()):
    return run_week2_scheduler()

@app.post("/turn/confirm")
def confirm_turn(req: TurnConfirmRequest):
    return submit_bot_report(BotReportRequest(plot_id=req.farmer_id, report_type=req.status, notes=req.notes or ""))

@app.post("/reset")
def reset_database():
    return reset_to_week1()

# ----------------- STATIC ASSETS & FRONTEND SERVING -----------------

frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    @app.get("/")
    def serve_frontend_dist():
        return FileResponse(str(frontend_dist / "index.html"))

# Serve standalone interactive index.html from root or frontend
standalone_root = Path(__file__).parent.parent / "index.html"
standalone_frontend = Path(__file__).parent.parent / "frontend" / "index.html"

@app.get("/")
def serve_root():
    if standalone_root.exists():
        return FileResponse(str(standalone_root))
    elif standalone_frontend.exists():
        return FileResponse(str(standalone_frontend))
    return JSONResponse({"message": "KulhWise API is running. Open /docs for Swagger."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
