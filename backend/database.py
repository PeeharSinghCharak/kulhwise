import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent / "kulhwise.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_hash(prev_hash: str, timestamp: str, farmer_id: int, 
                   scheduled_hours: float, actual_received_hours: float, 
                   status: str, notes: str) -> str:
    """Calculates SHA-256 hash for a log entry to maintain tamper-evident blockchain-like chain."""
    payload = f"{prev_hash}|{timestamp}|{farmer_id}|{scheduled_hours:.2f}|{actual_received_hours:.2f}|{status}|{notes}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Farmers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        village TEXT NOT NULL,
        plot_acres REAL NOT NULL,
        crop_type TEXT NOT NULL,
        canal_reach TEXT NOT NULL, -- 'Head', 'Middle', 'Tail'
        accumulated_deficit_hours REAL DEFAULT 0.0,
        total_allocated_hours REAL DEFAULT 0.0,
        total_received_hours REAL DEFAULT 0.0,
        days_since_last_watered INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    # Schedules table
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
        status TEXT DEFAULT 'SCHEDULED', -- 'SCHEDULED', 'FULL', 'PARTIAL', 'MISSED'
        priority_rank INTEGER NOT NULL,
        FOREIGN KEY(farmer_id) REFERENCES farmers(id)
    )
    """)

    # Tamper-evident Distribution Log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS distribution_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        farmer_id INTEGER NOT NULL,
        farmer_name TEXT NOT NULL,
        scheduled_hours REAL NOT NULL,
        actual_received_hours REAL NOT NULL,
        status TEXT NOT NULL, -- 'FULL', 'PARTIAL', 'MISSED'
        notes TEXT,
        prev_hash TEXT NOT NULL,
        current_hash TEXT NOT NULL,
        FOREIGN KEY(farmer_id) REFERENCES farmers(id)
    )
    """)

    # System Metrics table for tracking fairness scores over time
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metrics (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def get_all_farmers() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM farmers 
        ORDER BY accumulated_deficit_hours DESC, id ASC
    """)
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
    cursor.execute("""
        SELECT * FROM schedules 
        ORDER BY priority_rank ASC
    """)
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
    """Adds a log entry with tamper-evident cryptographic SHA-256 hash chaining."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get latest log entry to find previous hash
    cursor.execute("SELECT current_hash FROM distribution_logs ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    genesis_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    prev_hash = last_row["current_hash"] if last_row else genesis_hash

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_hash = calculate_hash(prev_hash, timestamp, farmer_id, 
                                  scheduled_hours, actual_received_hours, status, notes)

    cursor.execute("""
        INSERT INTO distribution_logs (
            timestamp, farmer_id, farmer_name, scheduled_hours, 
            actual_received_hours, status, notes, prev_hash, current_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, farmer_id, farmer_name, scheduled_hours, 
        actual_received_hours, status, notes, prev_hash, current_hash
    ))

    # Update farmer deficit & totals
    # If missed, deficit increases by scheduled_hours
    # If full, deficit reduces by actual_received_hours (or stays bounded at 0)
    # If partial, deficit adjusts accordingly
    deficit_diff = scheduled_hours - actual_received_hours
    cursor.execute("""
        UPDATE farmers 
        SET accumulated_deficit_hours = MAX(0.0, accumulated_deficit_hours + ?),
            total_allocated_hours = total_allocated_hours + ?,
            total_received_hours = total_received_hours + ?,
            days_since_last_watered = CASE WHEN ? > 0 THEN 0 ELSE days_since_last_watered + 1 END
        WHERE id = ?
    """, (deficit_diff, scheduled_hours, actual_received_hours, actual_received_hours, farmer_id))

    # Also update schedule status if matching slot exists
    cursor.execute("""
        UPDATE schedules 
        SET status = ? 
        WHERE farmer_id = ?
    """, (status, farmer_id))

    conn.commit()
    log_id = cursor.lastrowid
    conn.close()

    return {
        "id": log_id,
        "timestamp": timestamp,
        "farmer_id": farmer_id,
        "farmer_name": farmer_name,
        "scheduled_hours": scheduled_hours,
        "actual_received_hours": actual_received_hours,
        "status": status,
        "notes": notes,
        "prev_hash": prev_hash,
        "current_hash": current_hash
    }

def get_all_logs(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM distribution_logs 
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def verify_ledger_integrity() -> Dict[str, Any]:
    """Scans entire tamper-evident chain and verifies SHA-256 cryptographically."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM distribution_logs ORDER BY id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not rows:
        return {"valid": True, "count": 0, "message": "Ledger is empty. Cryptographic root initialized."}

    expected_prev = "0000000000000000000000000000000000000000000000000000000000000000"
    for idx, row in enumerate(rows):
        if row["prev_hash"] != expected_prev:
            return {
                "valid": False,
                "broken_at_id": row["id"],
                "reason": f"Hash chain broken at Record #{row['id']}: prev_hash does not match previous block.",
                "verified_count": idx
            }
        recomputed = calculate_hash(
            row["prev_hash"], row["timestamp"], row["farmer_id"],
            row["scheduled_hours"], row["actual_received_hours"],
            row["status"], row["notes"] or ""
        )
        if recomputed != row["current_hash"]:
            return {
                "valid": False,
                "broken_at_id": row["id"],
                "reason": f"Data tampering detected at Record #{row['id']}! Recomputed hash does not match current_hash.",
                "verified_count": idx
            }
        expected_prev = row["current_hash"]

    return {
        "valid": True,
        "count": len(rows),
        "latest_block_hash": rows[-1]["current_hash"],
        "message": f"Cryptographic integrity verified! All {len(rows)} blocks unbroken & tamper-proof."
    }

def set_metric(key: str, value: Any):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO system_metrics (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
    """, (key, str(value), now))
    conn.commit()
    conn.close()

def get_metric(key: str, default: Any = None) -> Any:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_metrics WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default
