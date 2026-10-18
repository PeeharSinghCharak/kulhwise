import sys
import os
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from typing import Optional, List
from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from database import (
    init_db,
    get_all_farmers,
    get_farmer_by_id,
    clear_and_save_schedule,
    get_latest_schedule,
    add_log_entry,
    get_all_logs,
    verify_ledger_integrity,
    set_metric,
    get_metric
)
from algorithm import calculate_priority_and_schedule, calculate_current_fairness_score
from seed_data import seed_database

# Initialize SQLite tables on startup
init_db()

app = FastAPI(
    title="KulhWise API",
    description="Smart Water Rotation System for Farmers – Fair, Transparent, and Tamper-Proof",
    version="1.0.0"
)

# Enable CORS for local React/Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Request Models
class TurnConfirmRequest(BaseModel):
    farmer_id: int
    status: str  # 'FULL', 'PARTIAL', 'MISSED'
    actual_received_hours: Optional[float] = None
    notes: Optional[str] = ""

class GenerateScheduleRequest(BaseModel):
    available_canal_hours: Optional[float] = 24.0
    rotation_date: Optional[str] = None

# Ensure seed data exists on first boot
farmers_check = get_all_farmers()
if not farmers_check:
    seed_database()

# ==================== API ENDPOINTS ====================

@app.get("/farmers")
def list_farmers():
    """List all simulated farmers with their current deficit status, plot size, crop, and reach."""
    farmers = get_all_farmers()
    return {
        "status": "success",
        "count": len(farmers),
        "data": farmers
    }

@app.post("/schedule/generate")
def generate_schedule(req: GenerateScheduleRequest = GenerateScheduleRequest()):
    """
    Triggers the KulhWise fairness algorithm to generate the next rotation schedule.
    Prioritizes farmers with accumulated water deficits and high-demand crops.
    Returns the schedule and Before/After Fairness Scores.
    """
    farmers = get_all_farmers()
    if not farmers:
        raise HTTPException(status_code=400, detail="No farmers found. Please seed the database first.")

    scheduled_slots, before_score, after_score = calculate_priority_and_schedule(
        farmers=farmers,
        available_canal_hours=req.available_canal_hours,
        rotation_date=req.rotation_date
    )

    # Persist the newly generated schedule
    clear_and_save_schedule(scheduled_slots)

    # Update metrics in database
    set_metric("current_fairness_score", after_score)
    set_metric("projected_fairness_score", after_score)
    set_metric("last_before_score", before_score)
    
    run_count = int(get_metric("algorithm_run_count", 0)) + 1
    set_metric("algorithm_run_count", run_count)

    return {
        "status": "success",
        "message": "KulhWise schedule successfully computed and optimized for fair distribution.",
        "before_fairness_score": before_score,
        "after_fairness_score": after_score,
        "improvement_percentage": round(after_score - before_score, 1),
        "total_scheduled_farmers": len(scheduled_slots),
        "schedule": scheduled_slots
    }

@app.get("/schedule")
def get_schedule():
    """Fetch the current rotation schedule."""
    schedule = get_latest_schedule()
    return {
        "status": "success",
        "count": len(schedule),
        "data": schedule
    }

@app.post("/turn/confirm")
def confirm_turn(req: TurnConfirmRequest):
    """
    Endpoint for a farmer to confirm or report water delivery.
    Statuses:
      - FULL: received all scheduled hours (deficit clears/decreases)
      - PARTIAL: received less than scheduled (difference added to deficit)
      - MISSED: received 0 hours (full scheduled time added to deficit for next round)
    Creates an immutable, cryptographically hashed record in the ledger.
    """
    farmer = get_farmer_by_id(req.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")

    # Find scheduled hours for this farmer if available, else derive from plot size
    schedule = get_latest_schedule()
    matching_slot = next((s for s in schedule if s["farmer_id"] == req.farmer_id), None)
    
    if matching_slot:
        scheduled_hours = float(matching_slot["allocated_hours"])
    else:
        scheduled_hours = round(max(0.5, float(farmer["plot_acres"]) * 1.0), 2)

    status_upper = req.status.upper()
    if status_upper not in ["FULL", "PARTIAL", "MISSED"]:
        raise HTTPException(status_code=400, detail="Status must be one of: FULL, PARTIAL, MISSED")

    if status_upper == "FULL":
        actual_hours = scheduled_hours
        default_note = "Water received successfully as scheduled."
    elif status_upper == "MISSED":
        actual_hours = 0.0
        default_note = "Farmer reported turn missed (canal dried up or diverted upstream)."
    else: # PARTIAL
        actual_hours = req.actual_received_hours if req.actual_received_hours is not None else round(scheduled_hours * 0.5, 2)
        default_note = f"Partial flow received: {actual_hours}h out of {scheduled_hours}h scheduled."

    final_notes = req.notes.strip() if req.notes and req.notes.strip() else default_note

    # Add to tamper-evident ledger and update farmer deficit
    log_entry = add_log_entry(
        farmer_id=farmer["id"],
        farmer_name=farmer["name"],
        scheduled_hours=scheduled_hours,
        actual_received_hours=actual_hours,
        status=status_upper,
        notes=final_notes
    )

    # Re-evaluate system fairness score
    all_farmers = get_all_farmers()
    new_fairness = calculate_current_fairness_score(all_farmers)
    set_metric("current_fairness_score", new_fairness)

    return {
        "status": "success",
        "message": f"Confirmation recorded for {farmer['name']} ({status_upper}). Deficit and ledger updated.",
        "log_entry": log_entry,
        "new_fairness_score": new_fairness
    }

@app.get("/logs")
def get_logs(limit: int = 100):
    """Fetch the transparent tamper-evident history of past turns and cryptographic hashes."""
    logs = get_all_logs(limit=limit)
    integrity = verify_ledger_integrity()
    return {
        "status": "success",
        "count": len(logs),
        "cryptographic_integrity": integrity,
        "data": logs
    }

@app.get("/stats")
def get_system_stats():
    """Returns overview statistics for dashboard."""
    farmers = get_all_farmers()
    schedule = get_latest_schedule()
    logs = get_all_logs(limit=1000)
    integrity = verify_ledger_integrity()

    total_farmers = len(farmers)
    total_allocated = sum(float(f["total_allocated_hours"]) for f in farmers)
    total_received = sum(float(f["total_received_hours"]) for f in farmers)
    total_deficit = sum(float(f["accumulated_deficit_hours"]) for f in farmers)
    
    current_fairness = float(get_metric("current_fairness_score", calculate_current_fairness_score(farmers)))
    initial_fairness = float(get_metric("initial_fairness_score", 37.8))
    last_before = float(get_metric("last_before_score", initial_fairness))
    run_count = int(get_metric("algorithm_run_count", 0))

    tail_deficit = sum(float(f["accumulated_deficit_hours"]) for f in farmers if f["canal_reach"] == "Tail")
    head_deficit = sum(float(f["accumulated_deficit_hours"]) for f in farmers if f["canal_reach"] == "Head")

    return {
        "total_farmers": total_farmers,
        "total_allocated_hours": round(total_allocated, 1),
        "total_received_hours": round(total_received, 1),
        "total_deficit_hours": round(total_deficit, 1),
        "head_deficit_hours": round(head_deficit, 1),
        "tail_deficit_hours": round(tail_deficit, 1),
        "current_fairness_score": current_fairness,
        "initial_fairness_score": initial_fairness,
        "last_before_score": last_before,
        "algorithm_run_count": run_count,
        "schedule_active": len(schedule) > 0,
        "scheduled_count": len(schedule),
        "ledger_verified": integrity["valid"],
        "ledger_blocks_count": integrity.get("count", 0)
    }

@app.post("/reset")
def reset_database():
    """Resets database to the initial unfair demo state (Tail farmers severely deprived)."""
    seed_database()
    return {
        "status": "success",
        "message": "Database successfully reset to initial unfair baseline (Tail-end farmers with high deficit). Ready for demonstration!"
    }

# Mount static frontend directory if built or available
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
frontend_static = Path(__file__).parent.parent / "frontend" / "public"

if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    @app.get("/")
    def serve_frontend_dist():
        return FileResponse(str(frontend_dist / "index.html"))

# Serve standalone interactive React UI from public/index.html if available
standalone_index = Path(__file__).parent.parent / "frontend" / "index.html"
if standalone_index.exists():
    @app.get("/")
    def serve_frontend_root():
        return FileResponse(str(standalone_index))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
