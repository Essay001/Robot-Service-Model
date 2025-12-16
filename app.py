import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="2029 Strategic Exit Model", layout="wide")

st.markdown("""
<style>
    .goal-box {background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 10px solid #2e7d32; text-align: center; height: 100%;}
    .miss-box {background-color: #ffebee; padding: 15px; border-radius: 10px; border-left: 10px solid #c62828; text-align: center; height: 100%;}
    .info-box {background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 10px solid #1565c0; text-align: center; height: 100%;}
    .metric-label {font-size: 14px; color: #555;}
    .metric-value {font-size: 24px; font-weight: bold;}
    .audit-box {background-color: #fff8e1; padding: 15px; border-radius: 5px; border-left: 5px solid #ffc107; font-size: 14px; margin-top: 10px;}
    .resource-box {background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 12px;}
    .split-box {background-color: #f3f3f3; padding: 10px; border-radius: 5px; margin-top: 5px; margin-bottom: 15px; font-size: 13px;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 2029 Strategic Exit Model")
st.markdown("The complete business plan: **Matrix Service Organization**, **Internal Chargebacks**, and **Corp Allocations**.")

# ==========================================
# 1. SIDEBAR: THE CONTROL TOWER
# ==========================================

with st.sidebar:
    st.header("1. Strategic Goals")
    c_g1, c_g2 = st.columns(2)
    target_2026 = c_g1.number_input("2026 Target ($)", value=2500000, step=250000, format="%d", help="Your goal for Year 1.")
    exit_target = c_g2.number_input("2029 Target ($)", value=7500000, step=250000, format="%d", help="Your Exit Number.")

    st.divider()

    # --- ACTUALS SECTION ---
    with st.expander("📝 Input 2025 Actuals (Baseline)", expanded=False):
        st.caption("Enter your real FY2025 numbers here to set the baseline.")
        act_rev_labor = st.number_input("2025 Labor Rev", value=1200000, step=10000, format="%d")
        act_rev_parts = st.number_input("2025 Job Parts Rev", value=300000, step=10000, format="%d")
        act_rev_sjob = st.number_input("2025 S-Job Rev", value=750000, step=10000, format="%d")
        act_rev_spares = st.number_input("2025 Spare Parts Rev", value=110000, step=10000, format="%d")
        
        st.markdown("---")
        act_cogs = st.number_input("2025 Total COGS", value=1400000, step=10000, format="%d")
        act_opex = st.number_input("2025 Total OpEx", value=800000, step=10000, format="%d")

        # Calculate derived 2025 stats
        act_total_rev = act_rev_labor + act_rev_parts + act_rev_sjob + act_rev_spares
        act_ebitda = act_total_rev - act_cogs - act_opex
        st.markdown(f"**2025 EBITDA:** ${act_ebitda:,.0f} ({(act_ebitda/act_total_rev)*100:.1f}%)")

    st.divider()

    # --- REVENUE INPUTS ---
    st.header("2. Service Revenue (Labor + Job Parts)")
    tm_service_base = st.number_input("2026 Total Service Rev ($)", value=1500000, step=100000, format="%d")
    tm_growth = st.number_input("Service Growth %", value=20, step=1, min_value=0, max_value=100)

    st.subheader("Revenue Split")
    labor_split_pct = st.number_input("Split: % from Labor", value=75, step=1, min_value=0, max_value=100)

    disp_labor = tm_service_base * (labor_split_pct/100)
    disp_parts = tm_service_base * (1 - (labor_split_pct/100))
    st.markdown(f"<div class='split-box'><b>2026 Breakdown:</b><br>🛠️ Labor: <b>${disp_labor:,.0f}</b><br>⚙️ Job Parts: <b>${disp_parts:,.0f}</b></div>", unsafe_allow_html=True)

    with st.expander("Service Settings"):
        bill_rate = st.number_input("Bill Rate ($/hr)", value=210, format="%d")
        utilization_pct = st.number_input("Tech Utilization %", value=80, step=1, min_value=10, max_value=100)
        utilization = utilization_pct / 100
        job_parts_margin = st.number_input("Job Parts Margin %", value=30, step=1, min_value=0, max_value=100)

    st.divider()

    st.header("3. S-Jobs (Projects)")
    s_job_base = st.number_input("2026 S-Job Rev ($)", value=1000000, step=100000, format="%d")
    s_job_growth = st.number_input("S-Job Growth %", value=15, step=1, min_value=0, max_value=100)

    # --- UPDATED: MARGIN & MIX LOGIC ---
    with st.expander("S-Job Settings (Margin & Mix)"):
        st.caption("How do you quote a typical project?")
        
        # 1. THE MIX
        st.markdown("**1. The Revenue Mix**")
        mix_mat_pct = st.slider("% Material (Hardware/Subs)", 0, 100, 50, help="What % of the invoice is Hardware?")
        mix_lab_pct = 100 - mix_mat_pct
        st.caption(f"Mix: {mix_mat_pct}% Material / {mix_lab_pct}% Labor")
        
        st.divider()
        
        # 2. THE MARGINS
        st.markdown("**2. Target Margins**")
        target_margin_mat = st.slider("Margin on Material %", 0, 50, 20)
        target_margin_lab = st.slider("Margin on Labor %", 0, 80, 50)
        
        # Derived Cost % (For internal calcs)
        # Cost = Revenue * (1 - Margin)
        # We calculate the weighted cost % to use in the P&L
        # Total Rev = 1.0. 
        # Mat Rev = 0.5. Mat Cost = 0.5 * (1 - 0.2) = 0.4
        # Lab Rev = 0.5. Lab Cost = 0.5 * (1 - 0.5) = 0.25
        # Total Cost = 0.65. Total Margin = 0.35.
        
        calc_mat_cost_pct = (mix_mat_pct/100) * (1 - target_margin_mat/100)
        calc_lab_cost_pct = (mix_lab_pct/100) * (1 - target_margin_lab/100)
        
        st.markdown(f"""
        <div style='background-color:#eee; padding:5px; border-radius:5px; font-size:12px;'>
        <b>Resulting Project Profile:</b><br>
        Blended Margin: <b>{((1 - (calc_mat_cost_pct + calc_lab_cost_pct))*100):.1f}%</b><br>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.caption("Resource Split (Of the Labor Portion):")
        c1, c2 = st.columns(2)
        w_tech = c1.number_input("Tech %", value=20, format="%d")/100
        w_me = c2.number_input("ME %", value=40, format="%d")/100
        w_ce = c1.number_input("CE %", value=20, format="%d")/100
        w_prog = c2.number_input("Prog %", value=20, format="%d")/100

    st.divider()

    st.header("4. Spare Parts (Direct)")
    spares_base = st.number_input("2026 Spare Parts Rev ($)", value=150000, step=10000, format="%d")
    spares_growth = st.number_input("Spare Parts Growth %", value=10, step=1, min_value=0, max_value=100)
    spares_margin = st.number_input("Spare Parts Margin %", value=35, step=1, min_value=0, max_value=100)

    st.divider()

    st.header("5. Costs & Baseline")
    with st.expander("Operational Details", expanded=True):
        st.caption("Baseline Staff (Already Hired):")
        c_h1, c_h2 = st.columns(2)
        base_techs = c_h1.number_input("Base Techs", value=2)
        base_me = c_h2.number_input("Base ME", value=1)
        base_ce = c_h1.number_input("Base CE", value=1)
        base_prog = c_h2.number_input("Base Prog", value=1)

        # --- BURDEN LOGIC ---
        st.markdown("#### 💸 Labor Cost (Burdened)")
        st.caption("Cost = Base + 11% Tax + $23k Insurance")
        
        tech_base = st.number_input("Tech Base Salary ($)", value=90000, step=5000)
        eng_base = st.number_input("Engineer Base Salary ($)", value=120000, step=5000)
        
        # Helper Display
        tech_burd = tech_base + (tech_base * 0.11) + 23000
        eng_burd = eng_base + (eng_base * 0.11) + 23000
        
        st.markdown(f"""
        <div style='font-size:12px; color:#555; background-color:#eee; padding:5px; border-radius:3px;'>
        <b>Effective Cost:</b><br>
        Tech: ${tech_burd:,.0f}/yr (${tech_burd/2080:.0f}/hr)<br>
        Eng: ${eng_burd:,.0f}/yr (${eng_burd/2080:.0f}/hr)
        </div>
        """, unsafe_allow_html=True)
        
        techs_per_loc_input = st.number_input("Max Techs per Location", value=4)

        # --- TIMING SECTION ---
        st.markdown("---")
        st.markdown("#### ⏳ Timing & Triggers")
        rent_per_loc = st.number_input("Rent ($/mo)", value=5000, format="%d")
        is_hq_free = st.checkbox("Is HQ Rent Free?", value=True, help="If checked, you only pay rent for Location 2, 3, etc.")

        central_cost = st.number_input("Corp Allocation (IT/HR) $/mo", value=8000, format="%d")
        central_start_year = st.selectbox("Start Corp Allocation In:", [2026, 2027, 2028, 2029], index=1)

    st.markdown("---")

    st.caption("Hiring & Sales:")
    attrition = st.number_input("Attrition %", value=10, step=1, min_value=0)
    hire_cost = st.number_input("Hire Cost ($)", value=12000, format="%d")
    sales_trigger = st.number_input("Rev per Sales Rep", value=3000000, format="%d")
    sales_rep_cost = 120000

    inflation_pct = st.number_input("Inflation %", value=3.0, step=0.5)
    inflation = inflation_pct / 100

    # Live calc of 2026 Total
    total_2026_input = tm_service_base + s_job_base + spares_base

    st.markdown(f"""
        <div class='resource-box'>
        <b>2026 Check:</b><br>
        Inputs Total: <b>${total_2026_input:,.0f}</b><br>
        Target: <b>${target_2026:,.0f}</b><br>
        Gap: <b style='color:{"green" if total_2026_input >= target_2026 else "red"}'>${total_2026_input - target_2026:,.0f}</b>
        </div>
        """, unsafe_allow_html=True)

    # --- BELOW THE LINE ---
    st.header("6. Below the Line (Estimates)")
    st.caption("Deductions from EBITDA to get Net Income.")
    depreciation_pct = st.number_input("Depreciation (% of Rev)", value=1.5, step=0.5)
    interest_expense = st.number_input("Annual Interest Exp ($)", value=0, step=10000, format="%d")
    tax_rate = st.number_input("Tax Rate %", value=25, step=1, min_value=0, max_value=50)

# ==========================================
# 2. LOGIC ENGINE
# ==========================================

def run_fusion_model():
    # --- STEP 1: CREATE 2025 ACTUALS ROW ---
    row_2025 = {
        "Year": 2025,
        "Total Revenue": act_total_rev,
        "Rev: Labor": act_rev_labor,
        "Rev: Job Parts": act_rev_parts,
        "Rev: S-Jobs": act_rev_sjob,
        "Rev: Spare Parts": act_rev_spares,
        "Total COGS": act_cogs,
        "Total OpEx": act_opex,
        "Gross Profit": act_total_rev - act_cogs,
        "Gross Margin %": (act_total_rev - act_cogs)/act_total_rev if act_total_rev else 0,
        "EBITDA": act_ebitda,
        "EBITDA Margin %": act_ebitda/act_total_rev if act_total_rev else 0,
        # Fill other columns with Base/NA for 2025
        "Techs": base_techs,
        "Locations": 1, 
        "Sales Reps": 0,
        "Total Hires": 0,
        "OpEx: Hiring": 0,
        "OpEx: Rent": 0, 
        "OpEx: Central": 0,
        "Eng FTE": base_me + base_ce + base_prog, # Approx
        "MEs": base_me, "CEs": base_ce, "Progs": base_prog, # Add these explicitly
        "Net Income": act_ebitda * (1 - (tax_rate/100)), # Rough est
        "Net Margin %": (act_ebitda * (1 - (tax_rate/100))) / act_total_rev if act_total_rev else 0,
        "D&A": 0, "Interest": 0, "Taxes": 0
    }

    # --- STEP 2: RUN PROJECTIONS 2026-2029 ---
    years = [2026, 2027, 2028, 2029]
    data = [row_2025]

    # Growth Trackers
    curr_service_target = tm_service_base
    curr_sjob_target = s_job_base
    curr_spares_target = spares_base

    # Staff Trackers
    cum_techs = base_techs
    cum_me = base_me
    cum_ce = base_ce
    cum_prog = base_prog

    prev_total_hc = base_techs + base_me + base_ce + base_prog

    for i, year in enumerate(years):
        # Inflation: 2026 is Year 1 (no inflation applied to inputs), 2027 is Year 2 (1 year inflation)
        inf = (1 + inflation) ** i

        # 1. CALCULATE EFFECTIVE HOURLY COST BASED ON BURDEN LOGIC
        
        # Tech Cost
        tech_annual = tech_base + (tech_base * 0.11) + 23000
        tech_annual_inf = tech_annual * inf
        c_tech_inf = tech_annual_inf / 2080 # Derived hourly rate

        # Engineer Cost (Applies to ME, CE, Prog)
        eng_annual = eng_base + (eng_base * 0.11) + 23000
        eng_annual_inf = eng_annual * inf
        c_eng_inf = eng_annual_inf / 2080 # Derived hourly rate

        # Other Costs
        c_bill_inf = bill_rate * inf
        c_hire_inf = hire_cost * inf
        c_rent_inf = rent_per_loc * inf

        # 2. CALCULATE REVENUE STREAMS
        if i > 0:
            curr_service_target = curr_service_target * (1 + tm_growth/100)
            curr_sjob_target = curr_sjob_target * (1 + s_job_growth/100)
            curr_spares_target = curr_spares_target * (1 + spares_growth/100)

        # SPLIT SERVICE REVENUE
        curr_labor_target = curr_service_target * (labor_split_pct / 100)
        curr_job_parts_rev = curr_service_target * (1 - (labor_split_pct / 100))

        # Total Top Line
        total_rev = curr_labor_target + curr_job_parts_rev + curr_sjob_target + curr_spares_target

        # 3. RESOURCE LOADING
        # A. Techs for Service Labor
        labor_capacity_per_tech = 2080 * utilization * c_bill_inf
        techs_for_service = math.ceil(curr_labor_target / labor_capacity_per_tech)

        # B. Resources for S-Jobs
        # New Logic: We use the Margin & Mix inputs to determine the Labor Budget
        
        # Total S-Job Revenue = curr_sjob_target
        # Labor Revenue Portion = curr_sjob_target * (mix_lab_pct/100)
        # Labor Cost Budget = Labor Revenue Portion * (1 - target_margin_lab/100)
        
        s_job_labor_revenue = curr_sjob_target * (mix_lab_pct/100)
        s_job_labor_cost_budget = s_job_labor_revenue * (1 - (target_margin_lab/100))

        # Now convert that COST budget into Headcount using the Weighted %
        # (Assuming Labor Budget is spent on Internal Engineering Staff)
        
        sj_tech_fte = (s_job_labor_cost_budget * w_tech) / tech_annual_inf
        sj_me_fte = (s_job_labor_cost_budget * w_me) / eng_annual_inf
        sj_ce_fte = (s_job_labor_cost_budget * w_ce) / eng_annual_inf
        sj_prog_fte = (s_job_labor_cost_budget * w_prog) / eng_annual_inf

        # C. Total Headcount Requirements
        req_techs = math.ceil(techs_for_service + sj_tech_fte)
        req_me = math.ceil(sj_me_fte)
        req_ce = math.ceil(sj_ce_fte)
        req_prog = math.ceil(sj_prog_fte)

        # 4. HIRING & ATTRITION
        new_techs = max(0, req_techs - cum_techs)
        cum_techs = max(cum_techs, req_techs)
        new_me = max(0, req_me - cum_me)
        cum_me = max(cum_me, req_me)
        new_ce = max(0, req_ce - cum_ce)
        cum_ce = max(cum_ce, req_ce)
        new_prog = max(0, req_prog - cum_prog)
        cum_prog = max(cum_prog, req_prog)

        growth_hires = new_techs + new_me + new_ce + new_prog
        attrition_count = math.ceil(prev_total_hc * (attrition/100))
        total_hires = growth_hires + attrition_count

        curr_total_hc = cum_techs + cum_me + cum_ce + cum_prog
        prev_total_hc = curr_total_hc

        # 5. OPERATIONS
        locs = math.ceil(cum_techs / techs_per_loc_input) 
        managers = math.ceil(cum_techs / 10)
        sales_reps = math.floor(total_rev / sales_trigger)

        # 6. FINANCIALS (OPERATING)

        # COGS
        # Service Labor
        cogs_labor_tech = cum_techs * 2080 * c_tech_inf
        
        # S-Job Labor Chargeback (The hours allocated to S-Jobs)
        # Note: In this model, we hire staff to meet demand. 
        # So "COGS Chargeback" is effectively the cost of the FTEs we dedicated to S-Jobs.
        
        # Since we calculate Total Payroll via Headcount, we don't need a separate chargeback line 
        # unless we want to split COGS for reporting. 
        # But for total P&L, Total Payroll covers it.
        # However, to match the previous structure:
        
        # We will sum Total Payroll and put it in COGS for simplicity of this specific view
        # Or split it. Let's stick to the previous robust way: 
        # Total Tech Cost + Total Eng Cost = Total Labor COGS.
        
        total_eng_fte_actual = cum_me + cum_ce + cum_prog
        cogs_eng_labor = total_eng_fte_actual * 2080 * c_eng_inf
        
        # Material COGS (S-Job)
        # S-Job Material Rev = curr_sjob_target * (mix_mat_pct/100)
        # S-Job Material Cost = Mat Rev * (1 - target_margin_mat/100)
        s_job_mat_rev = curr_sjob_target * (mix_mat_pct/100)
        cogs_sjob_mat = s_job_mat_rev * (1 - (target_margin_mat/100))

        cogs_job_parts = curr_job_parts_rev * (1 - (job_parts_margin/100))
        cogs_spares = curr_spares_target * (1 - (spares_margin/100))

        total_cogs = cogs_labor_tech + cogs_eng_labor + cogs_job_parts + cogs_spares + cogs_sjob_mat
        gross_profit = total_rev - total_cogs

        # OpEx
        if is_hq_free:
            billable_locs = max(0, locs - 1)
        else:
            billable_locs = locs

        opex_rent = billable_locs * c_rent_inf * 12

        if year >= central_start_year and locs > 1:
            central_fee = central_cost * 12 * inf
        else:
            central_fee = 0

        opex_mgr = managers * (85000 * 1.2 * inf)
        opex_sales = sales_reps * (sales_rep_cost * inf)
        opex_hire = total_hires * c_hire_inf

        total_opex = opex_rent + opex_mgr + opex_sales + central_fee + opex_hire

        # 7. EBITDA (OPERATING PROFIT)
        ebitda = gross_profit - total_opex

        # 8. BELOW THE LINE (NET INCOME)
        da_cost = total_rev * (depreciation_pct / 100)
        ebit = ebitda - da_cost
        interest = interest_expense
        ebt = ebit - interest
        taxes = ebt * (tax_rate / 100) if ebt > 0 else 0
        net_income = ebt - taxes

        data.append({
            "Year": year,
            "Total Revenue": total_rev,
            "Rev: Labor": curr_labor_target,
            "Rev: Job Parts": curr_job_parts_rev,
            "Rev: S-Jobs": curr_sjob_target,
            "Rev: Spare Parts": curr_spares_target,
            # MARGINS
            "Gross Profit": gross_profit,
            "Gross Margin %": gross_profit/total_rev,
            "EBITDA": ebitda,
            "EBITDA Margin %": ebitda/total_rev,
            "Net Income": net_income,
            "Net Margin %": net_income/total_rev,
            # DETAILS
            "Techs": cum_techs,
            "MEs": cum_me,
            "CEs": cum_ce,
            "Progs": cum_prog,
            "Locations": locs,
            "Sales Reps": sales_reps,
            "Total Hires": total_hires,
            "OpEx: Hiring": opex_hire,
            "Eng FTE": total_eng_fte_actual, # Updated variable name
            "OpEx: Rent": opex_rent,
            "OpEx: Central": central_fee,
            "Total COGS": total_cogs,
            "Total OpEx": total_opex,
            # BTL
            "D&A": da_cost,
            "Interest": interest,
            "Taxes": taxes
        })

    return pd.DataFrame(data)

df = run_fusion_model()

# ==========================================
# 3. TOP ROW: SCORECARDS (Side-by-Side)
# ==========================================

yr1 = df.iloc[1] # 2026 (Index 1)
yr4 = df.iloc[-1] # 2029 (Last)

c1, c2, c3 = st.columns(3)

with c1:
    gap_26 = yr1['Total Revenue'] - target_2026
    color_26 = "green" if gap_26 >= 0 else "red"
    label_26 = "Surplus" if gap_26 >= 0 else "Shortfall"

    st.markdown(f"""
    <div class='goal-box' style='border-left: 10px solid {color_26}; background-color: {"#e8f5e9" if gap_26 >= 0 else "#ffebee"};'>
    <h4>2026 Performance</h4>
    <span class='metric-label'>Projected vs Target</span><br>
    <span class='metric-value'>${yr1['Total Revenue']:,.0f}</span><br>
    <span style='color:{color_26}; font-weight:bold;'>{'+' if gap_26>=0 else ''}${gap_26:,.0f} {label_26}</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    gap_29 = yr4['Total Revenue'] - exit_target
    color_29 = "green" if gap_29 >= 0 else "red"
    label_29 = "Surplus" if gap_29 >= 0 else "Shortfall"

    st.markdown(f"""
    <div class='goal-box' style='border-left: 10px solid {color_29}; background-color: {"#e8f5e9" if gap_29 >= 0 else "#ffebee"};'>
    <h4>2029 Exit Status</h4>
    <span class='metric-label'>Projected vs Target</span><br>
    <span class='metric-value'>${yr4['Total Revenue']:,.0f}</span><br>
    <span style='color:{color_29}; font-weight:bold;'>{'+' if gap_29>=0 else ''}${gap_29:,.0f} {label_29}</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    lab_cap = 2080 * utilization * bill_rate
    ticket_cap = lab_cap / (labor_split_pct/100)
    parts_cap = ticket_cap - lab_cap

    st.markdown(f"""
    <div class='info-box'>
    <h4>💡 Tech Revenue Reality</h4>
    <span class='metric-label'>Rev per 1 Tech (Full Utilization)</span><br>
    <span class='metric-value'>${ticket_cap:,.0f}</span><br>
    <span style='font-size:12px; color:#333;'>(${lab_cap:,.0f} Labor + ${parts_cap:,.0f} Parts)</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ==========================================
# 4. CHART SECTION (Full Width)
# ==========================================

st.subheader("Revenue Path to Exit (With EBITDA Margin)")
fig, ax = plt.subplots(figsize=(10, 5))

years = df['Year']
# Stacked Bars
p1 = ax.bar(years, df['Rev: Labor'], label='Service Labor', color='#1565c0')
p2 = ax.bar(years, df['Rev: Job Parts'], bottom=df['Rev: Labor'], label='Job Parts', color='#64b5f6')
p3 = ax.bar(years, df['Rev: S-Jobs'], bottom=df['Rev: Labor']+df['Rev: Job Parts'], label='S-Jobs', color='#ffb74d')
p4 = ax.bar(years, df['Rev: Spare Parts'], bottom=df['Rev: Labor']+df['Rev: Job Parts']+df['Rev: S-Jobs'], label='Spare Parts', color='#81c784')

# Add Data Labels (Compact Millions)
for container in ax.containers:
    labels = [f'${v/1000000:.1f}M' if v > 100000 else "" for v in container.datavalues]
    ax.bar_label(container, labels=labels, label_type='center', color='white', fontsize=9, padding=0)

# EBITDA Line on Secondary Axis (NOW PERCENTAGE)
ax2 = ax.twinx()
ax2.plot(years, df['EBITDA Margin %'] * 100, color='#212121', linestyle='-', linewidth=3, marker='o', label='EBITDA Margin')
ax2.set_ylabel('EBITDA Margin (%)', color='#212121')

# Combined Legend logic - MOVED TO BOTTOM
lines, labels = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)

# Target Lines
ax.axhline(y=exit_target, color='red', linestyle='--', linewidth=2)
ax.text(2026.5, exit_target, f" Exit: ${exit_target/1000000:.1f}M", color='red', va='bottom', fontweight='bold')

ax.axhline(y=target_2026, color='blue', linestyle=':', linewidth=2)
ax.text(2026.1, target_2026, f" Year 1: ${target_2026/1000000:.1f}M", color='blue', va='bottom', fontsize=8)

# Format Axes
ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))

ax.spines['top'].set_visible(False)
plt.tight_layout()

st.pyplot(fig)

st.divider()

# ==========================================
# 5. AUDIT CENTER (TABBED)
# ==========================================

st.subheader("🔍 Audit Center")

tab1, tab2, tab3 = st.tabs(["💰 Detailed P&L Waterfall", "👥 Headcount Path", "📊 Hiring & Ops"])

def format_df(d, m): return d.style.format(m)

with tab1:
    st.markdown("### P&L Statement (The Waterfall)")
    st.info("Includes 2025 Actuals (Baseline) -> 2029 Projections.")
    
    # Selecting columns in logical P&L order
    cols_pl = ['Year', 
               'Total Revenue', 
               'Total COGS', 
               'Gross Profit', 
               'Total OpEx', 
               'EBITDA', 'EBITDA Margin %',
               'D&A', 'Interest', 'Taxes',
               'Net Income', 'Net Margin %']
    
    fmt = {
        'Year': '{:.0f}', 
        'EBITDA Margin %': '{:.1%}', 
        'Net Margin %': '{:.1%}'
    }
    # Currency format for the rest
    for c in cols_pl:
        if c not in fmt: fmt[c] = "${:,.0f}"
    
    st.dataframe(format_df(df[cols_pl], fmt), use_container_width=True)

with tab2:
    st.markdown("### Resource Path")
    cols = ['Year', 'Techs', 'MEs', 'CEs', 'Progs', 'Locations', 'Sales Reps']
    fmt = {'Year':'{:.0f}', 'Techs':'{:.0f}', 'MEs':'{:.0f}', 'CEs':'{:.0f}', 'Progs':'{:.0f}', 'Locations':'{:.0f}', 'Sales Reps':'{:.0f}'}
    st.dataframe(format_df(df[cols], fmt), use_container_width=True)

with tab3:
    st.markdown("### Hiring & Operations Audit")
    cols = ['Year', 'Total Hires', 'OpEx: Hiring', 'OpEx: Rent', 'OpEx: Central']
    fmt = {'Year':'{:.0f}', 'Total Hires':'{:.0f}', 'OpEx: Hiring':'${:,.0f}', 'OpEx: Rent':'${:,.0f}', 'OpEx: Central':'${:,.0f}'}
    st.dataframe(format_df(df[cols], fmt), use_container_width=True)
    st.markdown(f"""
    <div class='audit-box'>
    <b>Rent Rule:</b> HQ Free = {is_hq_free}. You pay for Locs-1.<br>
    <b>Central Rule:</b> Starts in {central_start_year} AND requires > 1 Location.
    </div>
    """, unsafe_allow_html=True)
