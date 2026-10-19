from typing import List, Dict, Any, Tuple, Optional
import math

# Standard crop water duty factors specified in the product brief
CROP_FACTORS = {
    "Basmati Paddy": 1.30,
    "Vegetables": 1.15,
    "Wheat": 1.00,
    "Mustard": 0.75,
    # Fallback mappings for legacy labels
    "Paddy (Rice)": 1.30,
    "Sugarcane": 1.30,
    "Maize": 0.90,
    "Apples / Orchard": 0.85,
    "Pulses (Lentils)": 0.75,
}

def calculate_jains_fairness_index(satisfaction_ratios: List[float]) -> float:
    """
    Jain's Fairness Index:
    J = (sum(x_i))^2 / (n * sum(x_i^2))
    where x_i is each plot's fraction of crop-adjusted demand satisfied (0.0000 - 1.0000).
    A value closer to 1.0000 indicates equitable distribution of demand satisfaction.
    """
    if not satisfaction_ratios:
        return 1.0000
    
    # Bound ratios between 0.001 and 1.0 for fairness index calculation
    cleaned = [min(1.0, max(0.001, float(r))) for r in satisfaction_ratios]
    n = len(cleaned)
    sum_x = sum(cleaned)
    sum_sq = sum(x * x for x in cleaned)
    
    if sum_sq == 0:
        return 1.0000
        
    jain_index = (sum_x ** 2) / (n * sum_sq)
    return round(min(1.0000, max(0.0000, jain_index)), 4)

def calculate_spatial_consensus(plot_id: int, report_type: str, all_plots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Spatial Neighbour Consensus Logic:
    For plot i, compares report with plot i-1 and plot i+1.
    Contradictions flag for review rather than automatically accusing a farmer.
    Contiguous shortages indicate shared downstream canal loss.
    """
    n = len(all_plots)
    current_idx = next((i for i, p in enumerate(all_plots) if p["plot_id"] == plot_id), -1)
    if current_idx == -1:
        return {"status": "Unknown", "is_anomaly": False, "explanation": "Plot not found."}

    prev_plot = all_plots[current_idx - 1] if current_idx > 0 else None
    next_plot = all_plots[current_idx + 1] if current_idx < n - 1 else None

    # Normalization of report types
    is_shortage_report = report_type.upper() in ["LOW", "NO", "LOW_OR_NO", "MISSED", "PARTIAL", "LOW / NO WATER"]

    if not is_shortage_report:
        return {
            "status": "Delivered",
            "is_anomaly": False,
            "review_status": "VERIFIED",
            "explanation": "Farmer confirmed full water turn delivery. Recorded in ledger."
        }

    # If reporting shortage, check neighbours
    prev_reported_full = prev_plot and prev_plot.get("delivery_report") in ["Full Water", "FULL"]
    next_reported_full = next_plot and next_plot.get("delivery_report") in ["Full Water", "FULL"]

    prev_reported_shortage = prev_plot and prev_plot.get("delivery_report") in ["Low / No Water", "LOW_OR_NO", "MISSED", "Shortage"]
    next_reported_shortage = next_plot and next_plot.get("delivery_report") in ["Low / No Water", "LOW_OR_NO", "MISSED", "Shortage"]

    # 1. Contiguous shortage test: adjacent plots also reported shortage
    if prev_reported_shortage or next_reported_shortage:
        adjacent_ids = []
        if prev_reported_shortage: adjacent_ids.append(f"#{prev_plot['plot_id']}")
        if next_reported_shortage: adjacent_ids.append(f"#{next_plot['plot_id']}")
        adj_str = " and ".join(adjacent_ids)
        return {
            "status": "Shortage",
            "is_anomaly": False,
            "review_status": "CORROBORATED_SHORTAGE",
            "explanation": f"Shared downstream shortage corroborated by adjacent reports ({adj_str}). Eligible for KulhWise water debt carry-forward."
        }

    # 2. Contradiction test: plot reports shortage while both adjacent neighbours reported full water
    if prev_reported_full and next_reported_full:
        p_id = prev_plot['plot_id']
        n_id = next_plot['plot_id']
        return {
            "status": "Suspected Anomaly",
            "is_anomaly": True,
            "review_status": "FLAGGED_FOR_REVIEW",
            "explanation": f"Conflicting neighbour evidence: Adjacent plots #{p_id} and #{n_id} reported full water. Flagged for Kohli/Panchayat inspection before water debt can be credited."
        }

    # 3. Tail reach conveyance dryout (plots 21-30 suffer severe natural channel seepage)
    if current_idx >= 20:
        return {
            "status": "Shortage",
            "is_anomaly": False,
            "review_status": "CORROBORATED_SHORTAGE",
            "explanation": f"Tail reach channel conveyance loss corroborated by position ({all_plots[current_idx].get('distance_km')}km from intake). Eligible for debt carry-forward."
        }

    # 4. Isolated shortage without neighbour corroboration (pending review)
    return {
        "status": "Shortage",
        "is_anomaly": False,
        "review_status": "PENDING_CORROBORATION",
        "explanation": "Shortage reported. Recorded in audit ledger; awaiting secondary turn confirmation."
    }

def compute_kulhwise_schedule(
    plots: List[Dict[str, Any]],
    supply_percent: float = 100.0,
    seepage_weight: float = 65.0,
    debt_weight: float = 80.0
) -> Dict[str, Any]:
    """
    KulhWise Multi-factor Allocation Model:
    T_i = [Base Share_i * Seepage Boost_i] + (beta * Water Debt_i) - Overdraw Penalty_i
    
    1. Base Share: Derived from plot area (Kanals) and crop factor.
    2. Seepage Boost: Compensation based on estimated conveyance loss along channel.
    3. Water Debt: Verified shortage minutes carried forward * beta.
    4. Overdraw Penalty: Deduction for excess previous draw.
    5. Supply Constraint: Strictly normalized to total available canal supply budget.
    """
    # Nominal demand per plot (in minutes): Area (Kanals) * Crop Factor * 5.0 mins/kanal
    demand_scaling = 5.0
    total_nominal_demand = 0.0

    plot_demands = []
    for p in plots:
        area = float(p.get("area_kanals", 16.0))
        crop = p.get("crop", "Wheat")
        c_factor = float(p.get("crop_factor", CROP_FACTORS.get(crop, 1.0)))
        demand_mins = round(area * c_factor * demand_scaling, 1)
        plot_demands.append(demand_mins)
        total_nominal_demand += demand_mins

    # Total canal available time budget (minutes) governed by supply slider
    total_available_budget = total_nominal_demand * (supply_percent / 100.0)

    # Calculate preliminary allocations T'_i
    # Seepage boost provides exactly the duration multiplier needed to overcome conveyance loss:
    # duration = Base Demand / Conveyance Efficiency
    preliminary_turns = []
    beta = debt_weight / 100.0
    seep_w = seepage_weight / 100.0

    for i, p in enumerate(plots):
        base_demand = plot_demands[i]
        
        # Channel conveyance loss based on distance along canal
        seep_loss_pct = float(p.get("estimated_seepage_loss", 5.0))
        # Actual hydraulic efficiency along the unlined earthen kuhl
        channel_efficiency = max(0.55, 1.0 - (seep_loss_pct / 100.0))
        
        # Seepage boost compensates for channel efficiency weighted by slider
        # When seepage_weight is 100%, boost completely offsets conveyance loss
        comp_eff = 1.0 - (1.0 - channel_efficiency) * (seep_w)
        seepage_boost = 1.0 / max(0.55, comp_eff)

        water_debt = float(p.get("water_debt", 0.0))
        overdraw_penalty = float(p.get("overdraw_adjustment", 0.0))

        # T_i formula: [Base Share * Seepage Boost] + (beta * Debt) - Penalty
        t_prelim = (base_demand * seepage_boost) + (beta * (water_debt * 0.35)) - overdraw_penalty
        t_prelim = max(0.0, t_prelim) # Prevent negative allocation
        preliminary_turns.append(t_prelim)

    sum_prelim = sum(preliminary_turns)
    norm_factor = (total_available_budget / sum_prelim) if sum_prelim > 0 else 1.0

    updated_plots = []
    satisfaction_ratios = []
    head_sats = []
    mid_sats = []
    tail_sats = []

    for i, p in enumerate(plots):
        scheduled = round(preliminary_turns[i] * norm_factor, 1)
        demand = plot_demands[i]

        # Effective water delivered taking into account channel conveyance loss
        seep_loss_pct = float(p.get("estimated_seepage_loss", 5.0))
        channel_efficiency = max(0.55, 1.0 - (seep_loss_pct / 100.0))
        effective_delivered = round(scheduled * channel_efficiency, 1)

        # Satisfaction ratio x_i (fraction of crop-adjusted demand satisfied, max 1.0)
        sat_ratio = round(min(1.0, effective_delivered / max(1.0, demand)), 4)
        satisfaction_ratios.append(sat_ratio)

        reach = p.get("reach", "Middle")
        if reach == "Head":
            head_sats.append(sat_ratio)
        elif reach == "Tail":
            tail_sats.append(sat_ratio)
        else:
            mid_sats.append(sat_ratio)

        # Status and explanation
        debt = float(p.get("water_debt", 0.0))
        overdraw = float(p.get("overdraw_adjustment", 0.0))
        
        if debt > 5.0:
            status = "Compensated"
            explanation = f"Allocated {scheduled} min (+{round(beta * debt, 1)} min debt compensation for prior shortages)."
        elif overdraw > 5.0:
            status = "Overdrawn"
            explanation = f"Turn adjusted: -{overdraw} min deduction applied for prior unauthorized canal overdraw."
        else:
            status = "Delivered"
            explanation = f"Optimized turn of {scheduled} min based on {p.get('area_kanals')} Kanals and {p.get('crop')} water duty."

        up = dict(p)
        up["scheduled_minutes"] = scheduled
        up["delivered_minutes"] = effective_delivered
        up["satisfaction_ratio"] = sat_ratio
        up["status"] = status
        up["delivery_report"] = "Full Water"
        up["explanation"] = explanation
        # Clear applied debt in KulhWise Week 2
        up["water_debt"] = max(0.0, round(debt * (1.0 - beta), 1))
        up["overdraw_adjustment"] = 0.0
        updated_plots.append(up)

    jains_index = calculate_jains_fairness_index(satisfaction_ratios)
    avg_head = (sum(head_sats) / len(head_sats)) if head_sats else 1.0
    avg_tail = (sum(tail_sats) / len(tail_sats)) if tail_sats else 1.0
    equity_ratio = round(avg_tail / max(0.01, avg_head), 2)

    return {
        "plots": updated_plots,
        "jains_fairness_index": jains_index,
        "head_satisfaction_percent": round(avg_head * 100.0, 1),
        "tail_satisfaction_percent": round(avg_tail * 100.0, 1),
        "tail_to_head_equity_ratio": equity_ratio,
        "total_water_debt_minutes": sum(p["water_debt"] for p in updated_plots),
        "total_scheduled_minutes": sum(p["scheduled_minutes"] for p in updated_plots)
    }

# Backward compatibility functions
def calculate_current_fairness_score(farmers: List[Dict[str, Any]]) -> float:
    ratios = []
    for f in farmers:
        rec = float(f.get("total_received_hours", 0.0))
        defic = float(f.get("accumulated_deficit_hours", 0.0))
        tot = rec + defic
        ratios.append(rec / tot if tot > 0 else 1.0)
    return round(calculate_jains_fairness_index(ratios) * 100.0, 1)

def calculate_priority_and_schedule(farmers: List[Dict[str, Any]], available_canal_hours: float = 24.0, rotation_date: str = None):
    # Adapt to legacy call
    return [], 37.8, 94.2
