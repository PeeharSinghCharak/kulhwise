import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent / "kulhwise.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_block_hash(prev_hash: str, block_index: int, timestamp: str, plot_id: int,
                         allocated_minutes: float, reported_minutes: float,
                         water_debt: float, event_type: str) -> str:
    """Calculates SHA-256 hash for an audit ledger block."""
    payload = f"{prev_hash}|{block_index}|{timestamp}|{plot_id}|{allocated_minutes:.1f}|{reported_minutes:.1f}|{water_debt:.1f}|{event_type}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def init_db():
    """Initializes SQLite tables for 30-plot canal model, audit ledger, and activity feed."""
    conn = get_connection()
    cursor = conn.cursor()

    # 30-Plot Canal Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plots (
        plot_id INTEGER PRIMARY KEY,
        farmer_name TEXT NOT NULL,
        village TEXT NOT NULL,
        area_kanals REAL NOT NULL,
        crop TEXT NOT NULL,
        crop_factor REAL NOT NULL,
        reach TEXT NOT NULL, -- 'Head', 'Middle', 'Tail'
        distance_km REAL NOT NULL,
        estimated_seepage_loss REAL NOT NULL, -- e.g. 3.5%
        base_minutes REAL NOT NULL,
        scheduled_minutes REAL NOT NULL,
        delivered_minutes REAL NOT NULL,
        water_debt REAL DEFAULT 0.0,
        overdraw_adjustment REAL DEFAULT 0.0,
        status TEXT NOT NULL, -- 'Delivered', 'Overdrawn', 'Shortage', 'Suspected Anomaly', 'Compensated'
        delivery_report TEXT DEFAULT 'Not Reported', -- 'Full Water', 'Low / No Water', 'Not Reported'
        satisfaction_ratio REAL DEFAULT 1.0,
        explanation TEXT
    )
    """)

    # Tamper-Evident SHA-256 Audit Ledger Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_index INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        plot_id INTEGER NOT NULL,
        farmer_name TEXT NOT NULL,
        allocated_minutes REAL NOT NULL,
        reported_minutes REAL NOT NULL,
        water_debt REAL NOT NULL,
        event_type TEXT NOT NULL,
        prev_hash TEXT NOT NULL,
        current_hash TEXT NOT NULL
    )
    """)

    # Activity Feed Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_feed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        plot_id INTEGER,
        farmer_name TEXT,
        event_type TEXT NOT NULL,
        status TEXT NOT NULL,
        explanation TEXT NOT NULL
    )
    """)

    # Simulation State and Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulation_state (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # Backward compatibility tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        village TEXT NOT NULL,
        plot_acres REAL NOT NULL,
        crop_type TEXT NOT NULL,
        canal_reach TEXT NOT NULL,
        accumulated_deficit_hours REAL DEFAULT 0.0,
        total_allocated_hours REAL DEFAULT 0.0,
        total_received_hours REAL DEFAULT 0.0,
        days_since_last_watered INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        farmer_id INTEGER NOT NULL,
        farmer_name TEXT NOT NULL,
        crop_type TEXT NOT NULL,
        plot_acres REAL NOT NULL,
        canal_reach TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        allocated_hours REAL NOT NULL,
        priority_score REAL NOT NULL,
        status TEXT DEFAULT 'SCHEDULED',
        priority_rank INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS distribution_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        farmer_id INTEGER NOT NULL,
        farmer_name TEXT NOT NULL,
        scheduled_hours REAL NOT NULL,
        actual_received_hours REAL NOT NULL,
        status TEXT NOT NULL,
        notes TEXT,
        prev_hash TEXT NOT NULL,
        current_hash TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metrics (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

# ----------------- PLOT QUERIES -----------------

def get_all_plots() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plots ORDER BY plot_id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_plot_by_id(plot_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plots WHERE plot_id = ?", (plot_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_plot(plot_id: int, updates: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in updates.items():
        fields.append(f"{k} = ?")
        values.append(v)
    values.append(plot_id)
    sql = f"UPDATE plots SET {', '.join(fields)} WHERE plot_id = ?"
    cursor.execute(sql, tuple(values))
    conn.commit()
    conn.close()

# ----------------- AUDIT LEDGER -----------------

def get_audit_ledger(limit: int = 200) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_ledger ORDER BY block_index ASC LIMIT ?", (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def add_audit_block(plot_id: int, farmer_name: str, allocated_minutes: float,
                    reported_minutes: float, water_debt: float, event_type: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT current_hash, block_index FROM audit_ledger ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    genesis_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    prev_hash = last_row["current_hash"] if last_row else genesis_hash
    next_index = (last_row["block_index"] + 1) if last_row else 1

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_hash = calculate_block_hash(
        prev_hash, next_index, timestamp, plot_id, allocated_minutes,
        reported_minutes, water_debt, event_type
    )

    cursor.execute("""
        INSERT INTO audit_ledger (
            block_index, timestamp, plot_id, farmer_name, allocated_minutes,
            reported_minutes, water_debt, event_type, prev_hash, current_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        next_index, timestamp, plot_id, farmer_name, allocated_minutes,
        reported_minutes, water_debt, event_type, prev_hash, current_hash
    ))

    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()

    return {
        "id": inserted_id,
        "block_index": next_index,
        "timestamp": timestamp,
        "plot_id": plot_id,
        "farmer_name": farmer_name,
        "allocated_minutes": allocated_minutes,
        "reported_minutes": reported_minutes,
        "water_debt": water_debt,
        "event_type": event_type,
        "prev_hash": prev_hash,
        "current_hash": current_hash
    }

def verify_audit_ledger() -> Dict[str, Any]:
    """Verifies cryptographic hash chain integrity of the audit ledger."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_ledger ORDER BY block_index ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not rows:
        return {"valid": True, "count": 0, "message": "Audit ledger is empty."}

    expected_prev = "0000000000000000000000000000000000000000000000000000000000000000"
    for idx, row in enumerate(rows):
        if row["prev_hash"] != expected_prev:
            return {
                "valid": False,
                "broken_at_block": row["block_index"],
                "reason": f"Hash chain broken at Block #{row['block_index']}: prev_hash does not match preceding block hash.",
                "verified_count": idx
            }
        recomputed = calculate_block_hash(
            row["prev_hash"], row["block_index"], row["timestamp"], row["plot_id"],
            float(row["allocated_minutes"]), float(row["reported_minutes"]),
            float(row["water_debt"]), row["event_type"]
        )
        if recomputed != row["current_hash"]:
            return {
                "valid": False,
                "broken_at_block": row["block_index"],
                "reason": f"Tampering detected at Block #{row['block_index']}! Block data modified without updating SHA-256 hash.",
                "verified_count": idx
            }
        expected_prev = row["current_hash"]

    return {
        "valid": True,
        "count": len(rows),
        "latest_block_hash": rows[-1]["current_hash"],
        "message": f"SHA-256 ledger integrity verified. All {len(rows)} blocks cryptographically intact."
    }

def tamper_ledger_block(block_index: int = 5) -> Dict[str, Any]:
    """Demo-only function: Tamper with a block to demonstrate tamper-evident detection."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_ledger WHERE block_index = ?", (block_index,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"status": "error", "message": f"Block #{block_index} not found."}

    # Alter allocated minutes from original to 999.0 without recalculating the dependent hash
    original_val = row["allocated_minutes"]
    tampered_val = original_val + 75.0
    cursor.execute("""
        UPDATE audit_ledger 
        SET allocated_minutes = ?, event_type = 'UNAUTHORIZED_ALTERATION'
        WHERE block_index = ?
    """, (tampered_val, block_index))
    conn.commit()
    conn.close()

    integrity = verify_audit_ledger()
    return {
        "status": "tampered",
        "block_index": block_index,
        "original_minutes": original_val,
        "tampered_minutes": tampered_val,
        "integrity_result": integrity
    }

# ----------------- ACTIVITY FEED -----------------

def add_activity(event_type: str, status: str, explanation: str, plot_id: Optional[int] = None, farmer_name: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO activity_feed (timestamp, plot_id, farmer_name, event_type, status, explanation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, plot_id, farmer_name, event_type, status, explanation))
    conn.commit()
    conn.close()

def get_activity_feed(limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_feed ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

# ----------------- SIMULATION STATE -----------------

def set_state_var(key: str, value: Any):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO simulation_state (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
    """, (key, str(value), now))
    conn.commit()
    conn.close()

def get_state_var(key: str, default: Any = None) -> Any:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM simulation_state WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

# ----------------- BACKWARD COMPATIBILITY HELPERS -----------------

def get_all_farmers() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM farmers ORDER BY accumulated_deficit_hours DESC, id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_farmer_by_id(farmer_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_latest_schedule() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules ORDER BY priority_rank ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def clear_and_save_schedule(schedule_entries: List[Dict[str, Any]]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules")
    for entry in schedule_entries:
        cursor.execute("""
            INSERT INTO schedules (
                date, farmer_id, farmer_name, crop_type, plot_acres, 
                canal_reach, start_time, end_time, allocated_hours, 
                priority_score, status, priority_rank
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["date"], entry["farmer_id"], entry["farmer_name"], 
            entry["crop_type"], entry["plot_acres"], entry["canal_reach"], 
            entry["start_time"], entry["end_time"], entry["allocated_hours"], 
            entry["priority_score"], entry.get("status", "SCHEDULED"), 
            entry["priority_rank"]
        ))
    conn.commit()
    conn.close()

def add_log_entry(farmer_id: int, farmer_name: str, scheduled_hours: float, 
                  actual_received_hours: float, status: str, notes: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_hash FROM distribution_logs ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    genesis = "0000000000000000000000000000000000000000000000000000000000000000"
    prev = last_row["current_hash"] if last_row else genesis
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = f"{prev}|{ts}|{farmer_id}|{scheduled_hours:.2f}|{actual_received_hours:.2f}|{status}|{notes}"
    cur_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    cursor.execute("""
        INSERT INTO distribution_logs (
            timestamp, farmer_id, farmer_name, scheduled_hours, 
            actual_received_hours, status, notes, prev_hash, current_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ts, farmer_id, farmer_name, scheduled_hours, actual_received_hours, status, notes, prev, cur_hash))

    diff = scheduled_hours - actual_received_hours
    cursor.execute("""
        UPDATE farmers 
        SET accumulated_deficit_hours = MAX(0.0, accumulated_deficit_hours + ?),
            total_allocated_hours = total_allocated_hours + ?,
            total_received_hours = total_received_hours + ?,
            days_since_last_watered = CASE WHEN ? > 0 THEN 0 ELSE days_since_last_watered + 1 END
        WHERE id = ?
    """, (diff, scheduled_hours, actual_received_hours, actual_received_hours, farmer_id))

    cursor.execute("UPDATE schedules SET status = ? WHERE farmer_id = ?", (status, farmer_id))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return {
        "id": log_id, "timestamp": ts, "farmer_id": farmer_id, "farmer_name": farmer_name,
        "scheduled_hours": scheduled_hours, "actual_received_hours": actual_received_hours,
        "status": status, "notes": notes, "prev_hash": prev, "current_hash": cur_hash
    }

def get_all_logs(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM distribution_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def verify_ledger_integrity() -> Dict[str, Any]:
    # Bridges to verify_audit_ledger
    return verify_audit_ledger()

def set_metric(key: str, value: Any):
    set_state_var(key, value)

def get_metric(key: str, default: Any = None) -> Any:
    return get_state_var(key, default)
