import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from seed_data import seed_database
from main import (
    get_state, reset_to_week1, simulate_week1_chaos, run_week2_scheduler,
    submit_bot_report, simulate_tamper_test, repair_ledger, get_ledger,
    BotReportRequest, SchedulerParams
)

print('=== 1. SEEDING & BASELINE TEST ===')
seed_database()
s0 = get_state()['data']
assert s0['mode'] == 'Static Week 1', 'Mode mismatch'
assert len(s0['plots']) == 30, 'Plots count mismatch'
assert s0['metrics']['ledger_intact'] is True, 'Ledger should be intact'
print('Baseline Mode:', s0['mode'])
print('Jain Fairness:', s0['metrics']['jains_fairness_index'])
print('Head Sat:', s0['metrics']['head_satisfaction_percent'], '%')
print('Tail Sat:', s0['metrics']['tail_satisfaction_percent'], '%')
print('Total Debt:', s0['metrics']['total_water_debt_minutes'], 'min')

print('\n=== 2. CHAOS SIMULATION TEST ===')
s_chaos = simulate_week1_chaos()['data']
assert s_chaos['mode'] == 'Week 1 Chaos'
p3 = next(p for p in s_chaos['plots'] if p['plot_id'] == 3)
p14 = next(p for p in s_chaos['plots'] if p['plot_id'] == 14)
assert p3['status'] == 'Overdrawn', f"Plot 3 status: {p3['status']}"
assert p3['overdraw_adjustment'] == 45.0, f"Plot 3 overdraw: {p3['overdraw_adjustment']}"
assert p14['status'] == 'Suspected Anomaly', f"Plot 14 status: {p14['status']}"
print('Chaos Mode:', s_chaos['mode'])
print('Plot #3 (Overdraw):', p3['status'], p3['overdraw_adjustment'], 'min')
print('Plot #14 (Anomaly):', p14['status'], '|', p14['explanation'][:60])

print('\n=== 3. KULHWISE WEEK 2 SCHEDULER TEST ===')
s_w2 = run_week2_scheduler(SchedulerParams(supply_percent=100.0, seepage_weight=65.0, debt_weight=80.0))['data']
assert s_w2['mode'] == 'KulhWise Week 2'
jain_w2 = s_w2['metrics']['jains_fairness_index']
assert jain_w2 >= 0.98, f"Expected Jain >= 0.98, got {jain_w2}"
print('Week 2 Mode:', s_w2['mode'])
print('Week 2 Jain Fairness:', jain_w2)
print('Week 2 Head Sat:', s_w2['metrics']['head_satisfaction_percent'], '%')
print('Week 2 Tail Sat:', s_w2['metrics']['tail_satisfaction_percent'], '%')
print('Week 2 Equity Ratio:', s_w2['metrics']['tail_to_head_equity_ratio'])

print('\n=== 4. BOT REPORT SPATIAL CONSENSUS TEST ===')
r1 = submit_bot_report(BotReportRequest(plot_id=14, report_type='LOW_OR_NO'))
assert r1['consensus']['is_anomaly'] is True, 'Expected anomaly on plot 14'
print('Plot 14 report result: is_anomaly =', r1['consensus']['is_anomaly'], '|', r1['consensus']['explanation'][:60])

# Test contiguous shortage across adjacent tail plots 25 and 24
submit_bot_report(BotReportRequest(plot_id=25, report_type='LOW_OR_NO'))
r2 = submit_bot_report(BotReportRequest(plot_id=24, report_type='LOW_OR_NO'))
assert r2['consensus']['is_anomaly'] is False, 'Expected corroborated shortage on tail plot 24'
print('Plot 24 contiguous report: is_anomaly =', r2['consensus']['is_anomaly'], '|', r2['consensus']['explanation'][:60])

print('\n=== 5. CRYPTOGRAPHIC TAMPER & RESTORE TEST ===')
t_res = simulate_tamper_test()
assert t_res['data']['metrics']['ledger_intact'] is False, 'Expected ledger intact to be False'
assert t_res['data']['metrics']['ledger_broken_at'] == 5, 'Expected ledger broken at 5'
print('Tamper test detected:', not t_res['data']['metrics']['ledger_intact'], 'Broken at block:', t_res['data']['metrics']['ledger_broken_at'])

rep_res = repair_ledger()
assert rep_res['data']['metrics']['ledger_intact'] is True, 'Expected ledger to be restored'
print('Ledger restored:', rep_res['data']['metrics']['ledger_intact'])

# Reset back to baseline for clean demo start
reset_to_week1()
print('\n[SUCCESS] ALL 5 VERIFICATION STAGES PASSED WITH 100% SUCCESS!')
