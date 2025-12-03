import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Master Integrated Model (Allocated)", layout="wide")

st.markdown("""
<style>
    .big-metric {font-size: 20px !important; font-weight: bold;}
    .audit-box {background-color: #fff8e1; padding: 15px; border-radius: 5px; border-left: 5px solid #ffc107; font-size: 14px; margin-top: 10px;}
    .highlight-box {background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3;}
    .success-box {background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50;}
</style>
""", unsafe_allow_html=True)

st.title("🤖 The Grand Unified Model")
st.markdown("Combines **Service**, **S-Jobs**, **Attrition**, **Hiring Costs** with **FTE-Based Cost Allocation**.")

# ==========================================
# 1. SIDEBAR: THE CONTROL TOWER
# ==========================================

with st.sidebar:
    st.header("1. Existing Team (Baseline)")
    st.caption("Staff you already have (No hiring cost):")
    base_techs = st.number_input("Existing Techs", value=2, format="%d")
    base_me = st.number_input("Existing Mech Eng", value=1, format="%d")
    base_ce = st.number_input("Existing Controls", value=1, format="%d")
    base_prog = st.number_input("Existing Progs", value=1, format="%d")
    
    st.divider()

    st.header("2. Revenue Targets")
    # T&M
    base_tm_revenue = st.number_input("Year 1 T&M Revenue ($)", value=1500000, step=100000, format="%d")
    tm_growth_rate = st.slider("T&M Growth %", 0, 100, 20)
    # S-Jobs
    s_job_revenue = st.number_input("Year 1 S-Job Revenue ($)", value=1000000, step=100000, format="%d")
    s_job_growth = st.slider("S-Job Growth %", 0, 100, 10)
    # Misc
    misc_revenue = st.number_input("Misc. Revenue ($/yr)", value=50000, format="%d")

    st.divider()

    st.header("3. S-Job Definition")
    st.caption("Cost Structure per $1 Revenue:")
    sj_mat_pct = st.slider("Material Cost %", 0, 100, 50)
    sj_lab_pct = st.slider("Labor Cost %", 0, 100, 30)
    
    st.caption("Resource Split (Labor Portion):")
    c1, c2 = st.columns(2)
    w_tech = c1.number_input("Tech %", value=20, format="%d") / 100
    w_me = c2.number_input("Mech Eng %", value=40, format="%d") / 100
    w_ce = c1.number_input("Controls %", value=20, format="%d") / 100
    w_prog = c2.number_input("Prog %", value=20, format="%d") / 100
    
    if abs((w_tech+w_me+w_ce+w_prog) - 1.0) > 0.01:
        st.error(f"⚠️ Split sums to {(w_tech+w_me+w_ce+w_prog)*100:.0f}%, should be 100%")

    st.divider()

    st.header("4. The 'Real World' Costs")
    attrition_rate = st.slider("Attrition Rate %", 0, 30, 10, help="% of staff who quit each year.")
    cost_per_hire = st.number_input("Cost per Hire ($)", value=12000, help="Recruiting + Tooling cost per new head.", format="%d")
    sales_trigger = st.number_input("Rev per Sales Rep ($)", value=3000000, format="%d")
    
    st.divider()
    
    st.header("5. Rates & Efficiency")
    # Costs
    cost_tech = st.number_input("Tech Cost ($/hr)", value=85, format="%d")
    cost_eng = st.number_input("Engineer Cost ($/hr)", value=95, format="%d")
    # Billing
    bill_rate = st.number_input("T&M Bill Rate ($/hr)", value=210, format="%d")
    utilization = st.slider("T&M Utilization (%)", 40, 100, 80) / 100
    tm_parts_pct = st.slider("T&M Parts %", 0, 50, 30) / 100
    
    st.divider()
    
    st.header("6. Operational Overhead")
    techs_per_loc = st.number_input("Max Techs per Loc", value=6, format="%d")
    rent_cost = st.number_input("Rent ($/mo)", value=5000, format="%d")
    central_cost = st.number_input("Central Support ($/mo)", value=8000, format="%d")
    inflation = st.slider("Inflation %", 0, 10, 3) / 100

# ==========================================
# 2. SIMULATION ENGINE
# ==========================================

def run_grand_model():
    years = [2026, 2027, 2028, 2029, 2030]
    data = []
    
    # Trackers
    prev_tm = base_tm_revenue / (1 + tm_growth_rate/100)
    prev_sj = s_job_revenue / (1 + s_job_growth/100)
    
    # Headcount Trackers (Whole People)
    cum_techs = base_techs
    cum_me = base_me
    cum_ce = base_ce
    cum_prog = base_prog
    
    prev_year_total_headcount = base_techs + base_me + base_ce + base_prog
    
    for i, year in enumerate(years):
        inf = (1 + inflation) ** i
        
        # A. INFLATED RATES
        c_tech_inf = cost_tech * inf
        c_eng_inf = cost_eng * inf
        c_bill_inf = bill_rate * inf
        c_hire_inf = cost_per_hire * inf
        c_rent_inf = rent_cost * inf
        
        # B. REVENUE TARGETS
        if year == 2026:
            curr_tm = base_tm_revenue
            curr_sj = s_job_revenue
        else:
            curr_tm = prev_tm * (1 + tm_growth_rate/100)
            curr_sj = prev_sj * (1 + s_job_growth/100)
            
        prev_tm = curr_tm
        prev_sj = curr_sj
        curr_misc = misc_revenue * inf
        
        # C. RESOURCE CALCULATIONS (FTEs)
        
        # T&M Capacity (Techs are 100% burdened)
        tm_cap = (2080 * utilization * c_bill_inf) / (1 - tm_parts_pct)
        tm_techs_needed = math.ceil(curr_tm / tm_cap)
        
        # S-Job Resource Needs (Exact FTEs)
        sj_labor_budget = curr_sj * (sj_lab_pct / 100)
        
        sj_techs_fte = (sj_labor_budget * w_tech) / (c_tech_inf * 2080)
        sj_me_fte = (sj_labor_budget * w_me) / (c_eng_inf * 2080)
        sj_ce_fte = (sj_labor_budget * w_ce) / (c_eng_inf * 2080)
        sj_prog_fte = (sj_labor_budget * w_prog) / (c_eng_inf * 2080)
        
        # D. HEADCOUNT (For Hiring/Operations)
        # We still need to hire whole people even if we only bill 20% of them
        # Note: Techs are summed (T&M + S-Job FTE) and rounded UP
        req_techs = math.ceil(tm_techs_needed + sj_techs_fte)
        req_me = math.ceil(sj_me_fte)
        req_ce = math.ceil(sj_ce_fte)
        req_prog = math.ceil(sj_prog_fte)
        
        # E. HIRING LOGIC (Net New vs Baseline)
        new_techs = max(0, req_techs - cum_techs)
        cum_techs = max(cum_techs, req_techs)
        
        new_me = max(0, req_me - cum_me)
        cum_me = max(cum_me, req_me)
        
        new_ce = max(0, req_ce - cum_ce)
        cum_ce = max(cum_ce, req_ce)
        
        new_prog = max(0, req_prog - cum_prog)
        cum_prog = max(cum_prog, req_prog)
        
        growth_hires_count = new_techs + new_me + new_ce + new_prog
        attrition_loss = math.ceil(prev_year_total_headcount * (attrition_rate/100))
        replacement_hires = attrition_loss
        total_hires_this_year = growth_hires_count + replacement_hires
        
        curr_total_headcount = cum_techs + cum_me + cum_ce + cum_prog
        prev_year_total_headcount = curr_total_headcount
        
        # F. OPERATIONS
        locs = math.ceil(cum_techs / techs_per_loc)
        managers = math.ceil(cum_techs / 10)
        sales_reps = math.floor((curr_tm + curr_sj) / sales_trigger)
        
        # G. FINANCIALS (Allocated Cost Logic)
        total_rev = curr_tm + curr_sj + curr_misc
        
        # 1. COGS - TECHS
        # Service Techs are fully burdened (we pay for the person, slack included)
        cogs_labor_techs = cum_techs * 2080 * c_tech_inf
        
        # 2. COGS - ENGINEERS (ALLOCATED)
        # We only pay for the FTE utilization. Operations eats the slack.
        # Cost = Exact FTE * 2080 * Rate
        # We sum the FTEs for ME, CE, Prog
        total_eng_fte = sj_me_fte + sj_ce_fte + sj_prog_fte
        cogs_labor_eng = total_eng_fte * 2080 * c_eng_inf
        
        # 3. COGS - MATERIAL
        cogs_parts_tm = (curr_tm * tm_parts_pct) * 0.7 
        cogs_mat_sj = curr_sj * (sj_mat_pct / 100)
        
        total_cogs = cogs_labor_techs + cogs_labor_eng + cogs_parts_tm + cogs_mat_sj
        gross_profit = total_rev - total_cogs
        
        # OpEx
        opex_rent = locs * c_rent_inf * 12
        opex_mgr = managers * (85000 * 1.2 * inf)
        opex_sales = sales_reps * (120000 * inf)
        opex_central = (central_cost * 12 * inf) if locs > 1 else 0
        
        # Hiring Fees - We assume Service pays for Tech hiring. 
        # Operations likely pays for Engineer hiring since they "own" the resource.
        # Let's count hiring cost only for Techs + Managers to be fair to the "Allocated" model.
        # Tech Hires = Growth Techs + Tech Replacements
        # Tech ratio of staff = cum_techs / curr_total_headcount
        tech_ratio = cum_techs / curr_total_headcount if curr_total_headcount > 0 else 0
        service_hires = math.ceil(total_hires_this_year * tech_ratio)
        opex_hiring = service_hires * c_hire_inf
        
        total_opex = opex_rent + opex_mgr + opex_sales + opex_central + opex_hiring
        
        ebitda = gross_profit - total_opex
        
        data.append({
            "Year": year,
            # Top Line
            "Total Revenue": total_rev,
            "Rev: T&M": curr_tm,
            "Rev: S-Job": curr_sj,
            "Rev: Misc": curr_misc,
            # COGS Detail
            "COGS: Tech Labor": cogs_labor_techs,
            "COGS: Eng Labor (Alloc)": cogs_labor_eng,
            "COGS: T&M Parts": cogs_parts_tm,
            "COGS: S-Job Mat": cogs_mat_sj,
            "Total COGS": total_cogs,
            # Margin
            "Gross Profit": gross_profit,
            # OpEx Detail
            "OpEx: Rent": opex_rent,
            "OpEx: Managers": opex_mgr,
            "OpEx: Sales Reps": opex_sales,
            "OpEx: Central": opex_central,
            "OpEx: Hiring Fees": opex_hiring,
            "Total OpEx": total_opex,
            # Bottom Line
            "EBITDA": ebitda,
            "EBITDA Margin": (ebitda/total_rev),
            # Counts
            "HC: Techs": cum_techs,
            "HC: MEs": cum_me,
            "HC: CEs": cum_ce,
            "HC: Progs": cum_prog,
            "FTE: Engineers": total_eng_fte,
            "HC: Managers": managers,
            "HC: Sales Reps": sales_reps,
            "Total HC": curr_total_headcount + managers + sales_reps,
            "Locations": locs,
            # Hiring
            "Hires: Total": total_hires_this_year
        })
        
    return pd.DataFrame(data)

df = run_grand_model()

# ==========================================
# 3. DASHBOARD VISUALS
# ==========================================

c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Profitability Overview")
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    # Revenue
    ax1.bar(df['Year'], df['Total Revenue'], label='Total Revenue', color='#cfd8dc')
    ax1.set_ylabel('Revenue ($)')
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    
    # EBITDA Line
    ax2 = ax1.twinx()
    ax2.plot(df['Year'], df['EBITDA'], color='#2e7d32', marker='o', linewidth=3, label='EBITDA')
    ax2.set_ylabel('EBITDA ($)')
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    
    st.pyplot(fig)

with c2:
    st.subheader("Quick Stats (2030)")
    last = df.iloc[-1]
    st.metric("Total Revenue", f"${last['Total Revenue']:,.0f}")
    st.metric("Total COGS", f"${last['Total COGS']:,.0f}")
    st.metric("Total OpEx", f"${last['Total OpEx']:,.0f}")
    st.metric("EBITDA", f"${last['EBITDA']:,.0f}", delta=f"{last['EBITDA Margin']*100:.1f}% Margin")

st.divider()

# ==========================================
# 4. AUDIT CENTER (FULL DRILL DOWN)
# ==========================================

st.subheader("🔍 Audit Center: Drill Down")
st.markdown("Explore the detailed math behind every number.")

tab1, tab2, tab3, tab4 = st.tabs(["💰 Revenue & P&L", "🏗️ Cost Breakdown", "👥 Headcount Detail", "🚨 Hiring & Churn"])

# --- HELPER FUNCTION FOR FORMATTING ---
def format_df(dataframe, format_map):
    return dataframe.style.format(format_map)

with tab1:
    st.markdown("### Revenue Composition & P&L")
    cols_rev = ['Year', 'Rev: T&M', 'Rev: S-Job', 'Rev: Misc', 'Total Revenue', 'Gross Profit', 'EBITDA', 'EBITDA Margin']
    
    # Custom Format Map
    fmt_rev = {
        'Year': '{:.0f}',
        'EBITDA Margin': '{:.1f}%'
    }
    for c in cols_rev:
        if c not in fmt_rev:
            fmt_rev[c] = "${:,.0f}"

    st.dataframe(format_df(df[cols_rev], fmt_rev), use_container_width=True)
    
    st.info("Logic: T&M grows annually based on rate. S-Job grows annually based on rate. Misc is added flat (inflated).")

with tab2:
    st.markdown("### Expense Breakdown (COGS & OpEx)")
    cols_exp = ['Year', 'COGS: Tech Labor', 'COGS: Eng Labor (Alloc)', 'COGS: T&M Parts', 'COGS: S-Job Mat', 
                'OpEx: Rent', 'OpEx: Managers', 'OpEx: Hiring Fees']
    
    fmt_exp = {'Year': '{:.0f}'}
    for c in cols_exp:
        if c != 'Year':
            fmt_exp[c] = "${:,.0f}"

    st.dataframe(format_df(df[cols_exp], fmt_exp), use_container_width=True)
    
    st.markdown("""
    <div class='success-box'>
    <b>Logic Update (Allocation):</b><br>
    The <b>COGS: Eng Labor (Alloc)</b> line now only charges for the <b>Utilized FTEs</b>.<br>
    Example: If you need 1.2 MEs, you still hire 2 people, but this P&L is only charged for 1.2 MEs.<br>
    <i>Operations absorbs the cost of the remaining 0.8 ME.</i>
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown("### Staffing & Resources")
    cols_hc = ['Year', 'HC: Techs', 'HC: MEs', 'HC: CEs', 'HC: Progs', 'FTE: Engineers', 'HC: Managers', 'HC: Sales Reps', 'Total HC', 'Locations']
    
    fmt_hc = {'Year': '{:.0f}', 'FTE: Engineers': '{:.2f}'}
    for c in cols_hc:
        if c not in fmt_hc:
            fmt_hc[c] = "{:.0f}"
            
    st.dataframe(format_df(df[cols_hc], fmt_hc), use_container_width=True)
    
    st.info("Note: 'HC' is Physical People on Payroll. 'FTE: Engineers' is the Billable Fraction charged to Service.")

with tab4:
    st.markdown("### Hiring & Attrition Analysis")
    cols_hire = ['Year', 'Hires: Total', 'OpEx: Hiring Fees']
    
    fmt_hire = {
        'Year': '{:.0f}',
        'OpEx: Hiring Fees': '${:,.0f}',
        'Hires: Total': '{:.0f}'
    }
    
    st.dataframe(format_df(df[cols_hire], fmt_hire), use_container_width=True)
    st.caption("Note: Hiring Fees are pro-rated to reflect that Service only pays for Tech/Manager acquisition costs.")