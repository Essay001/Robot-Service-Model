import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# ==========================================
# 1. HARDCODED SETTINGS (From Your Export)
# ==========================================

# 1. EXIT GOAL
exit_target_val = 3750000
valuation_multiple = 7.0

# 2. TALENT
mix_pct = 50
g_base = 75000
r_base = 130000

# 3. 2025 BASELINE
act_rev_labor = 900000
act_rev_parts = 425000
act_rev_sjob = 750000
act_rev_spares = 110000
act_cogs = 1400000
act_opex = 425000
act_total_rev = act_rev_labor + act_rev_parts + act_rev_sjob + act_rev_spares
act_ebitda = act_total_rev - act_cogs - act_opex

# 4. SERVICE REVENUE
tm_service_base = 1750000
tm_growth = 20
labor_split_pct = 75
bill_rate = 210
utilization_pct = 75
job_parts_margin = 30

# 5. S-JOBS
s_job_base = 750000
s_job_growth = 10
s_job_hire_trigger = 1200000
mix_mat_pct = 60
target_margin_mat = 35
target_margin_lab = 50
w_tech = 0.0
w_me = 0.30
w_ce = 0.20
w_prog = 0.50

# 6. SPARES
spares_base = 150000
spares_growth = 10
spares_margin = 35

# 7. OPS & COSTS
base_techs = 2
base_me = 1
base_ce = 1
base_prog = 1
techs_per_loc_input = 4
rent_per_loc = 0
central_cost = 0
central_start_year = 2027
sales_trigger = 5000000
inflation_pct = 3.0
hire_cost = 12000
sales_rep_cost = 120000
eng_base = 120000

# Derived & Constants
rebadge_ratio = mix_pct / 100
green_ratio = 1 - rebadge_ratio
g_ramp_yr1_factor = 0.50
r_ramp_yr1_factor = 0.92
w_ramp_factor = (g_ramp_yr1_factor * green_ratio) + (r_ramp_yr1_factor * rebadge_ratio)
grad_year = 2028
grad_raise = 35000
utilization = utilization_pct / 100
inflation = inflation_pct / 100
attrition = 10
rework_rebadge = 0.01 
rework_green = 0.05   
w_rework_pct = (rework_rebadge * rebadge_ratio) + (rework_green * green_ratio)
depreciation_pct = 1.5
interest_expense = 0
tax_rate = 25

def calc_burden(base): return base + (base * 0.11) + 23000

# ==========================================
# 2. LOGIC ENGINE (Replicating app.py)
# ==========================================

def run_fusion_model():
    row_2025 = {
        "Year": 2025,
        "Total Revenue": act_total_rev,
        "Rev: Labor": act_rev_labor,
        "Rev: Job Parts": act_rev_parts,
        "Rev: S-Jobs": act_rev_sjob,
        "Rev: Spare Parts": act_rev_spares,
        "EBITDA Margin %": act_ebitda/act_total_rev if act_total_rev else 0
    }

    years = [2026, 2027, 2028, 2029]
    data = [row_2025]
    
    base_overhead_start = act_opex
    curr_service_target = tm_service_base
    curr_sjob_target = s_job_base
    curr_spares_target = spares_base
    cum_techs = base_techs
    cum_me = base_me; cum_ce = base_ce; cum_prog = base_prog
    prev_total_hc = base_techs + base_me + base_ce + base_prog

    for i, year in enumerate(years):
        inf = (1 + inflation) ** (i + 1)

        # Cost Updates
        current_g_base = g_base
        if year >= grad_year:
            current_g_base += grad_raise
            
        g_cost_curr = calc_burden(current_g_base)
        r_cost_curr = calc_burden(r_base)
        
        w_cost_tech_annual = (g_cost_curr * green_ratio) + (r_cost_curr * rebadge_ratio)
        tech_annual_inf = w_cost_tech_annual * inf
        c_tech_inf = tech_annual_inf / 2080 

        eng_annual = eng_base + (eng_base * 0.11) + 23000
        eng_annual_inf = eng_annual * inf
        c_eng_inf = eng_annual_inf / 2080

        c_bill_inf = bill_rate * inf
        c_hire_inf = hire_cost * inf
        c_rent_inf = rent_per_loc * inf

        # 2. REVENUE
        if i > 0:
            curr_service_target = curr_service_target * (1 + tm_growth/100)
            curr_sjob_target = curr_sjob_target * (1 + s_job_growth/100)
            curr_spares_target = curr_spares_target * (1 + spares_growth/100)

        curr_labor_target = curr_service_target * (labor_split_pct / 100)
        curr_job_parts_rev = curr_service_target * (1 - (labor_split_pct / 100))
        total_rev = curr_labor_target + curr_job_parts_rev + curr_sjob_target + curr_spares_target

        # 3. RESOURCE LOADING
        full_capacity_per_tech = 2080 * utilization * c_bill_inf
        existing_capacity_rev = cum_techs * full_capacity_per_tech
        gap_revenue = max(0, curr_labor_target - existing_capacity_rev)
        new_hire_yr1_capacity = full_capacity_per_tech * w_ramp_factor
        needed_new_techs_service = math.ceil(gap_revenue / new_hire_yr1_capacity)
        
        s_job_labor_revenue = curr_sjob_target * (mix_lab_pct/100)
        s_job_labor_cost_budget = s_job_labor_revenue * (1 - (target_margin_lab/100))
        
        sj_tech_fte = (s_job_labor_cost_budget * (w_tech/100)) / tech_annual_inf
        sj_me_fte = (s_job_labor_cost_budget * (w_me/100)) / eng_annual_inf
        sj_ce_fte = (s_job_labor_cost_budget * (w_ce/100)) / eng_annual_inf
        sj_prog_fte = (s_job_labor_cost_budget * (w_prog/100)) / eng_annual_inf

        # 4. HIRING & CONTRACTING LOGIC
        use_contractors = curr_sjob_target < s_job_hire_trigger
        
        cogs_sjob_contractor = 0
        req_me = 0; req_ce = 0; req_prog = 0
        
        if use_contractors:
            req_me = base_me
            req_ce = base_ce
            req_prog = base_prog
            eng_portion_share = (w_me + w_ce + w_prog)/100
            cogs_sjob_contractor = s_job_labor_cost_budget * eng_portion_share
        else:
            total_eng_fte_demand = sj_me_fte + sj_ce_fte + sj_prog_fte
            total_eng_bodies_needed = math.ceil(total_eng_fte_demand)
            existing_eng_pool = cum_me + cum_ce + cum_prog
            net_new_eng = max(0, total_eng_bodies_needed - existing_eng_pool)
            req_me = cum_me + net_new_eng
            req_ce = cum_ce 
            req_prog = cum_prog
            cogs_sjob_contractor = 0

        final_tech_count = cum_techs + needed_new_techs_service + math.ceil(sj_tech_fte)
        net_new_techs = final_tech_count - cum_techs
        cum_techs = final_tech_count
        
        new_me = max(0, req_me - cum_me); cum_me = max(cum_me, req_me)
        new_ce = max(0, req_ce - cum_ce); cum_ce = max(cum_ce, req_ce)
        new_prog = max(0, req_prog - cum_prog); cum_prog = max(cum_prog, req_prog)

        growth_hires = net_new_techs + new_me + new_ce + new_prog
        attrition_count = math.ceil(prev_total_hc * (attrition/100))
        total_hires = growth_hires + attrition_count
        prev_total_hc = cum_techs + cum_me + cum_ce + cum_prog

        locs = math.ceil(cum_techs / techs_per_loc_input) 
        managers_total = math.ceil(cum_techs / 10)
        managers_incremental = max(0, managers_total - 1)
        sales_reps = math.floor(total_rev / sales_trigger)

        # 6. FINANCIALS
        cogs_labor_tech = cum_techs * 2080 * c_tech_inf
        total_eng_fte_actual = cum_me + cum_ce + cum_prog
        cogs_eng_labor = total_eng_fte_actual * 2080 * c_eng_inf
        s_job_mat_rev = curr_sjob_target * (mix_mat_pct/100)
        cogs_sjob_mat = s_job_mat_rev * (1 - (target_margin_mat/100))
        cogs_job_parts = curr_job_parts_rev * (1 - (job_parts_margin/100))
        cogs_spares = curr_spares_target * (1 - (spares_margin/100))

        total_cogs = cogs_labor_tech + cogs_eng_labor + cogs_job_parts + cogs_spares + cogs_sjob_mat + cogs_sjob_contractor
        gross_profit = total_rev - total_cogs

        base_overhead_curr = base_overhead_start * inf
        billable_locs = max(0, locs - 1) 
        opex_rent = billable_locs * c_rent_inf * 12
        central_fee = central_cost * 12 * inf if (year >= central_start_year and locs > 1) else 0
        opex_mgr = managers_incremental * (85000 * 1.2 * inf)
        opex_sales = sales_reps * (sales_rep_cost * inf)
        opex_hire = total_hires * c_hire_inf
        opex_rework = total_rev * w_rework_pct

        total_opex = base_overhead_curr + opex_rent + opex_hire + central_fee + opex_sales + opex_rework + opex_mgr
        ebitda = gross_profit - total_opex

        data.append({
            "Year": year,
            "Total Revenue": total_rev,
            "Rev: Labor": curr_labor_target,
            "Rev: Job Parts": curr_job_parts_rev,
            "Rev: S-Jobs": curr_sjob_target,
            "Rev: Spare Parts": curr_spares_target,
            "EBITDA Margin %": ebitda/total_rev,
        })

    return pd.DataFrame(data)

df = run_fusion_model()

# ==========================================
# 3. GENERATE CHART
# ==========================================

fig, ax = plt.subplots(figsize=(10, 5))

years = df['Year']
p1 = ax.bar(years, df['Rev: Labor'], label='Service Labor', color='#1565c0')
p2 = ax.bar(years, df['Rev: Job Parts'], bottom=df['Rev: Labor'], label='Job Parts', color='#64b5f6')
p3 = ax.bar(years, df['Rev: S-Jobs'], bottom=df['Rev: Labor']+df['Rev: Job Parts'], label='S-Jobs', color='#ffb74d')
p4 = ax.bar(years, df['Rev: Spare Parts'], bottom=df['Rev: Labor']+df['Rev: Job Parts']+df['Rev: S-Jobs'], label='Spare Parts', color='#81c784')

for container in ax.containers:
    labels = [f'${v/1000000:.1f}M' if v > 100000 else "" for v in container.datavalues]
    ax.bar_label(container, labels=labels, label_type='center', color='white', fontsize=9, padding=0)

ax2 = ax.twinx()
ax2.plot(years, df['EBITDA Margin %'] * 100, color='#212121', linestyle='-', linewidth=3, marker='o', label='EBITDA Margin')
ax2.set_ylabel('EBITDA Margin (%)', color='#212121')

lines, labels = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)

ax.axhline(y=exit_target_val/valuation_multiple*4, color='red', linestyle='--', linewidth=1) 
ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
ax.spines['top'].set_visible(False)
plt.title(f"Revenue Path to Exit (With EBITDA Margin)\nScenario: {tm_growth}% Service Growth | {s_job_growth}% S-Job Growth", fontsize=14)
plt.tight_layout()
plt.savefig('revenue_path_chart.png')
print("Chart generated: revenue_path_chart.png")
