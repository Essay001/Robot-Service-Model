import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="2029 Strategic Exit Model (Annotated)", layout="wide")

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
st.markdown("The **Full Operational Model** (Matrix/S-Jobs) + **Talent Strategy** (Green vs. Rebadge).")

# ==========================================
# 1. SIDEBAR: THE CONTROL TOWER
# ==========================================

with st.sidebar:
    st.header("🎯 The Exit Goal")
    st.caption("How much do you want to sell the company for?")
    
    # THE ANCHOR
    exit_target_val = st.number_input(
        "Target Exit Valuation ($)", 
        value=7500000, 
        step=250000, 
        format="%d",
        help="The 'Walk Away' check size you want in 2029. This is calculated as: EBITDA × Multiple."
    )
    
    valuation_multiple = st.number_input(
        "EBITDA Multiple", 
        value=6.5, 
        step=0.5,
        help="The multiplier a PE firm pays for your profit. Service firms usually trade at 4x-8x EBITDA. Higher growth/margins = Higher Multiple."
    )
    
    # Calculate Required EBITDA
    req_ebitda = exit_target_val / valuation_multiple
    st.markdown(f"""
    <div style='background-color:#dcedc8; padding:5px; border-radius:5px; text-align:center;'>
    <b>REQUIRED 2029 EBITDA</b><br>
    <span style='font-size:18px; font-weight:bold;'>${req_ebitda:,.0f}</span><br>
    <small>(Target ${exit_target_val/1000000:.1f}M ÷ {valuation_multiple}x)</small>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- TALENT STRATEGY (NEW) ---
    st.header("🧬 Talent Strategy")
    st.caption("Green vs. Rebadge Mix")
    
    # The Slider
    mix_pct = st.slider(
        "Hiring Mix (% Rebadge)", 
        0, 100, 50, 
        help="0% = Hiring all Junior 'Green' Techs (Cheaper, slower ramp). 100% = Hiring all Senior 'Rebadge' Techs (Expensive, instant revenue)."
    )
    
    with st.expander("Talent Assumptions (Base Pay)"):
        st.markdown("**Green Tech (Junior)**")
        g_base = st.number_input("Green Base ($)", value=75000, help="Base Salary for a Junior Tech.")
        
        st.markdown("**Rebadge Tech (Senior)**")
        r_base = st.number_input("Rebadge Base ($)", value=130000, help="Base Salary for a Senior/Rebadge Tech.")
        
        # Burden Calc
        def calc_burden(base): return base + (base * 0.11) + 23000
        g_cost = calc_burden(g_base)
        r_cost = calc_burden(r_base)
        
        # Weighted Average Cost per Head
        rebadge_ratio = mix_pct / 100
        green_ratio = 1 - rebadge_ratio
        
        w_cost_tech = (g_cost * green_ratio) + (r_cost * rebadge_ratio)
        
        st.info(f"**Blended Tech Cost:** ${w_cost_tech:,.0f}/yr\n\n(Includes 11% Tax + $23k Insurance)")

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
    st.header("2. Service Revenue")
    tm_service_base = st.number_input(
        "2026 Total Service Rev ($)", 
        value=1500000, step=100000, format="%d",
        help="Projected total revenue for T&M Service (Labor + Parts) for next year."
    )
    tm_growth = st.number_input("Service Growth %", value=20, step=1, min_value=0, max_value=100)

    st.subheader("Revenue Split")
    labor_split_pct = st.number_input(
        "Split: % from Labor", 
        value=75, step=1, min_value=0, max_value=100,
        help="Of the total Service Revenue, what % is billed labor? The rest is assumed to be Parts."
    )

    disp_labor = tm_service_base * (labor_split_pct/100)
    disp_parts = tm_service_base * (1 - (labor_split_pct/100))
    st.markdown(f"<div class='split-box'><b>2026 Breakdown:</b><br>🛠️ Labor: <b>${disp_labor:,.0f}</b><br>⚙️ Job Parts: <b>${disp_parts:,.0f}</b></div>", unsafe_allow_html=True)

    with st.expander("Service Settings"):
        bill_rate = st.number_input("Bill Rate ($/hr)", value=210, format="%d")
        utilization_pct = st.number_input(
            "Tech Utilization %", 
            value=80, step=1, min_value=10, max_value=100,
            help="What % of a 2,080 hour year is billed? 80% is standard."
        )
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
        mix_mat_pct = st.slider(
            "% Material (Hardware/Subs)", 
            0, 100, 50, 
            help="On a $100k project, how much is Hardware/Material? (vs Labor)"
        )
        mix_lab_pct = 100 - mix_mat_pct
        st.caption(f"Mix: {mix_mat_pct}% Material / {mix_lab_pct}% Labor")
        
        st.divider()
        
        # 2. THE MARGINS
        st.markdown("**2. Target Margins**")
        target_margin_mat = st.slider(
            "Margin on Material %", 
            0, 50, 20,
            help="Profit margin on the hardware portion."
        )
        target_margin_lab = st.slider(
            "Margin on Labor %", 
            0, 80, 50,
            help="Profit margin on the engineering portion. Used to set the labor budget."
        )
        
        # Derived Cost % (For internal calcs)
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
        st.caption("Auto-Calculated Burden: Base + 11% Tax + $23k Insurance")
        
        # We use the Blended Tech cost from above
        eng_base = st.number_input("Engineer Base Salary ($)", value=120000, step=5000)
        
        # Helper Display
        eng_burd = eng_base + (eng_base * 0.11) + 23000
        
        st.markdown(f"""
        <div style='font-size:12px; color:#555; background-color:#eee; padding:5px; border-radius:3px;'>
        <b>Effective Annual Cost (Burdened):</b><br>
        Tech (Blended): ${w_cost_tech:,.0f}/yr<br>
        Eng (Fixed): ${eng_burd:,.0f}/yr
        </div>
        """, unsafe_allow_html=True)
        
        techs_per_loc_input = st.number_input(
            "Max Techs per Location", 
            value=4,
            help="When tech count exceeds this number, the model automatically adds a new location (and new rent)."
        )

        # --- TIMING SECTION ---
        st.markdown("---")
        st.markdown("#### ⏳ Timing & Triggers")
        rent_per_loc = st.number_input("Rent ($/mo)", value=5000, format="%d")
        is_hq_free = st.checkbox("Is HQ Rent Free?", value=True, help="If checked, you only pay rent for Location 2, 3, etc.")

        central_cost = st.number_input(
            "Corp Allocation (IT/HR) $/mo", 
            value=8000, format="%d",
            help="Shared service fees (HR, IT, Finance) charged by HQ once you scale up."
        )
        central_start_year = st.selectbox("Start Corp Allocation In:", [2026, 2027, 2028, 2029], index=1)

    st.markdown("---")

    st.caption("Hiring & Sales:")
    attrition = st.number_input("Attrition %", value=10, step=1, min_value=0, help="Percentage of staff that quit each year.")
    hire_cost = st.number_input("Hire Cost ($)", value=12000, format="%d", help="Recruiting fees per new hire.")
    sales_trigger = st.number_input("Rev per Sales Rep", value=3000000, format="%d", help="We hire 1 Sales Rep for every X dollars in revenue.")
    sales_rep_cost = 120000

    inflation_pct = st.number_input("Inflation %", value=3.0, step=0.5)
    inflation = inflation_pct / 100

    # Live calc of 2026 Total
    total_2026_input = tm_service_base + s_job_base + spares_base

    st.markdown(f"""
        <div class='resource-box'>
        <b>2026 Check:</b><br>
        Inputs Total: <b>${total_2026_input:,.0f}</b><br>
        Gap to 26 Goal: <b>${total_2026_input - 2500000:,.0f}</b>
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
        "Eng FTE": base_me + base_ce + base_prog, 
        "MEs": base_me, "CEs": base_ce, "Progs": base_prog,
        "Net Income": act_ebitda * (1 - (tax_rate/100)),
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
        inf = (1 + inflation) ** i

        # 1. CALCULATE EFFECTIVE HOURLY COST BASED ON BURDEN LOGIC
        
        # Tech Cost (Uses the Blended W_Cost from Sidebar)
        tech_annual_inf = w_cost_tech * inf
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
        s_job_labor_revenue = curr_sjob_target * (mix_lab_pct/100)
        s_job_labor_cost_budget = s_job_labor_revenue * (1 - (target_margin_lab/100))

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
        cogs_labor_tech = cum_techs * 2080 * c_tech_inf
        
        total_eng_fte_actual = cum_me + cum_ce + cum_prog
        cogs_eng_labor = total_eng_fte_actual * 2080 * c_eng_inf
        
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
            "Eng FTE": total_eng_fte_actual, 
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
exit_val = yr4['EBITDA'] * valuation_multiple

c1, c2, c3 = st.columns(3)

with c1:
    gap_exit = exit_val - exit_target_val
    color_exit = "green" if gap_exit >= 0 else "red"
    label_exit = "Surplus" if gap_exit >= 0 else "Shortfall"

    st.markdown(f"""
    <div class='goal-box' style='border-left: 10px solid {color_exit}; background-color: {"#e8f5e9" if gap_exit >= 0 else "#ffebee"};'>
    <h4>2029 Exit Value</h4>
    <span class='metric-label'>Goal: ${exit_target_val/1000000:.1f}M</span><br>
    <span class='metric-value'>${exit_val/1000000:.1f}M</span><br>
    <span style='color:{color_exit}; font-weight:bold;'>{'+' if gap_exit>=0 else ''}${gap_exit/1000000:.1f}M {label_exit}</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    # 2029 EBITDA CHECK
    gap_ebitda = yr4['EBITDA'] - req_ebitda
    color_eb = "green" if gap_ebitda >= 0 else "red"
    
    st.markdown(f"""
    <div class='goal-box' style='border-left: 10px solid {color_eb}; background-color: {"#e8f5e9" if gap_ebitda >= 0 else "#ffebee"};'>
    <h4>2029 EBITDA</h4>
    <span class='metric-label'>Goal: ${req_ebitda/1000000:.1f}M</span><br>
    <span class='metric-value'>${yr4['EBITDA']/1000000:.1f}M</span><br>
    <span style='color:{color_eb}; font-weight:bold;'>Margin: {yr4['EBITDA Margin %']*100:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    lab_cap = 2080 * utilization * bill_rate
    ticket_cap = lab_cap / (labor_split_pct/100)
    
    st.markdown(f"""
    <div class='info-box'>
    <h4>💡 Strategy Check</h4>
    <span class='metric-label'>Tech Count in 2029</span><br>
    <span class='metric-value'>{yr4['Techs']:.0f} Techs</span><br>
    <span style='font-size:12px; color:#333;'>Locations: {yr4['Locations']:.0f} | Rebadge Mix: {mix_pct}%</span>
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
ax.axhline(y=exit_target_val/valuation_multiple*4, color='red', linestyle='--', linewidth=1) 
# Note: Visual target line for revenue is hard because EBITDA is the real goal. 
# We will just show the EBITDA text on the right axis if possible, or skip for clean chart.

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
