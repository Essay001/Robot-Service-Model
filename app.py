import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="2029 Exit Strategy Model", layout="wide")

st.markdown("""
<style>
    .goal-box {background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 10px solid #2e7d32; text-align: center;}
    .miss-box {background-color: #ffebee; padding: 20px; border-radius: 10px; border-left: 10px solid #c62828; text-align: center;}
    .metric-label {font-size: 14px; color: #555;}
    .metric-value {font-size: 26px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 2029 Exit Strategy: Strategic Planner")
st.markdown("Model the path to **$7.5M Revenue**. Control **Labor**, **Job Parts**, **Pure Spares**, and **Projects** separately.")

# ==========================================
# 1. SIDEBAR: REVENUE STREAMS
# ==========================================

with st.sidebar:
    st.header("1. The Exit Goal")
    exit_target = st.number_input("2029 Revenue Target ($)", value=7500000, step=250000)
    
    st.divider()
    
    st.header("2. Revenue Stream A: Service Labor")
    tm_labor_base = st.number_input("Year 1 Labor Rev ($)", value=2000000, step=100000, help="Revenue from HOURS only.")
    tm_growth = st.slider("Labor Growth %", 0, 100, 20)
    bill_rate = st.number_input("Bill Rate ($/hr)", value=210)
    utilization = st.slider("Tech Utilization %", 50, 100, 80) / 100
    
    st.divider()

    st.header("3. Revenue Stream B: Job Parts")
    st.info("Parts sold *during* a service call.")
    # Input: Parts as % of Total Job? Or Parts relative to Labor?
    # User said: "20-30% of overall revenue is parts".
    # Let's use % of Ticket.
    job_parts_pct = st.slider("Parts % of Service Ticket", 0, 50, 25, help="If 25%, then a $1000 invoice is $750 Labor / $250 Parts.")
    job_parts_margin = st.slider("Job Parts Margin %", 0, 100, 30)

    st.divider()

    st.header("4. Revenue Stream C: S-Jobs (Projects)")
    s_job_base = st.number_input("Year 1 S-Job Rev ($)", value=1000000, step=100000)
    s_job_growth = st.slider("S-Job Growth %", 0, 100, 15)
    
    # S-Job definition
    with st.expander("S-Job Cost Details"):
        sj_mat_pct = st.slider("Material Cost %", 0, 100, 50)
        sj_lab_pct = st.slider("Labor Cost %", 0, 100, 30)
        st.caption("Resource Split:")
        w_tech = st.number_input("Tech %", value=0.20)
        w_me = st.number_input("ME %", value=0.40)
        w_ce = st.number_input("CE %", value=0.20)
        w_prog = st.number_input("Prog %", value=0.20)

    st.divider()

    st.header("5. Revenue Stream D: Pure Spares")
    st.info("Direct box sales (No labor attached).")
    spares_base = st.number_input("Year 1 Spares Rev ($)", value=500000, step=50000)
    spares_growth = st.slider("Spares Growth %", 0, 100, 10)
    spares_margin = st.slider("Spares Margin %", 0, 100, 35)

    st.divider()
    
    st.header("6. Costs & Baseline")
    with st.expander("Staff & OpEx Settings"):
        base_techs = st.number_input("Existing Techs", value=2)
        base_others = st.number_input("Existing Engineers", value=3)
        cost_tech = st.number_input("Tech Cost ($/hr)", value=85)
        cost_eng = st.number_input("Eng Cost ($/hr)", value=95)
        techs_per_loc = st.number_input("Techs/Loc", value=6)
        rent = st.number_input("Rent", value=5000)
        attrition = st.slider("Attrition %", 0, 20, 10)
        hire_cost = st.number_input("Hire Cost", value=12000)
        inflation = st.slider("Inflation %", 0, 10, 3) / 100

# ==========================================
# 2. LOGIC ENGINE
# ==========================================

def run_exit_model():
    years = [2026, 2027, 2028, 2029]
    data = []
    
    # Growth Trackers
    curr_labor_target = tm_labor_base
    curr_sjob_target = s_job_base
    curr_spares_target = spares_base
    
    # Baseline Staff
    cum_techs = base_techs
    cum_eng = base_others
    prev_total_hc = base_techs + base_others
    
    for i, year in enumerate(years):
        inf = (1 + inflation) ** i
        
        # 1. Calculate Revenue Streams
        if i > 0:
            curr_labor_target = curr_labor_target * (1 + tm_growth/100)
            curr_sjob_target = curr_sjob_target * (1 + s_job_growth/100)
            curr_spares_target = curr_spares_target * (1 + spares_growth/100)
            
        # 2. Calculate "Job Parts" (The Attach Rate)
        # If Labor Rev is X, and Parts is Y% of TOTAL Ticket...
        # Labor = Total * (1 - Y%)  ->  Total = Labor / (1 - Y%)
        # Parts = Total - Labor
        total_ticket_rev = curr_labor_target / (1 - (job_parts_pct/100))
        curr_job_parts_rev = total_ticket_rev - curr_labor_target
        
        # 3. Total Revenue
        total_rev = curr_labor_target + curr_job_parts_rev + curr_sjob_target + curr_spares_target
        
        # 4. Resource Requirements
        # A. Techs for Labor Service
        # Capacity = 2080 * Util * BillRate
        tech_capacity_labor_only = 2080 * utilization * (bill_rate * inf)
        techs_for_service = math.ceil(curr_labor_target / tech_capacity_labor_only)
        
        # B. Resources for S-Jobs
        sj_labor_budget = curr_sjob_target * (sj_lab_pct/100)
        sj_tech_fte = (sj_labor_budget * w_tech) / ((cost_tech*inf) * 2080)
        sj_eng_fte = (sj_labor_budget * (w_me+w_ce+w_prog)) / ((cost_eng*inf) * 2080)
        
        # C. Total Headcount Needed
        req_techs = math.ceil(techs_for_service + sj_tech_fte)
        req_eng = math.ceil(sj_eng_fte) # Simplifying all eng to one bucket for high level
        
        # D. Hiring (Growth + Attrition)
        # Growth
        new_techs = max(0, req_techs - cum_techs)
        cum_techs = max(cum_techs, req_techs)
        new_eng = max(0, req_eng - cum_eng)
        cum_eng = max(cum_eng, req_eng)
        
        # Attrition
        attrition_count = math.ceil(prev_total_hc * (attrition/100))
        total_hires = new_techs + new_eng + attrition_count
        
        curr_total_hc = cum_techs + cum_eng
        prev_total_hc = curr_total_hc
        
        # 5. Financials
        
        # COGS
        # Labor (Techs + Eng)
        cogs_labor_tech = cum_techs * 2080 * (cost_tech * inf)
        # Allocated Eng COGS (FTE based)
        cogs_labor_eng = sj_eng_fte * 2080 * (cost_eng * inf)
        
        # Parts COGS
        cogs_job_parts = curr_job_parts_rev * (1 - (job_parts_margin/100))
        cogs_spares = curr_spares_target * (1 - (spares_margin/100))
        cogs_sjob_mat = curr_sjob_target * (sj_mat_pct/100)
        
        total_cogs = cogs_labor_tech + cogs_labor_eng + cogs_job_parts + cogs_spares + cogs_sjob_mat
        gross_profit = total_rev - total_cogs
        
        # OpEx
        locs = math.ceil(cum_techs / techs_per_loc)
        managers = math.ceil(cum_techs / 10)
        
        opex_rent = locs * (rent * inf) * 12
        opex_mgr = managers * (85000 * 1.2 * inf)
        opex_hire = total_hires * (hire_cost * inf)
        
        total_opex = opex_rent + opex_mgr + opex_hire
        ebitda = gross_profit - total_opex
        
        data.append({
            "Year": year,
            "Total Revenue": total_rev,
            "Rev: Labor": curr_labor_target,
            "Rev: Job Parts": curr_job_parts_rev,
            "Rev: S-Jobs": curr_sjob_target,
            "Rev: Spares": curr_spares_target,
            "EBITDA": ebitda,
            "EBITDA %": ebitda/total_rev,
            "Techs": cum_techs,
            "Locations": locs
        })
        
    return pd.DataFrame(data)

df = run_exit_model()

# ==========================================
# 3. GOAL SEEK VISUALIZER
# ==========================================

final_yr = df.iloc[-1]
actual_2029 = final_yr['Total Revenue']
gap = actual_2029 - exit_target

c_goal, c_chart = st.columns([1, 2])

with c_goal:
    if gap >= 0:
        st.markdown(f"""
        <div class='goal-box'>
        <h3>🎉 GOAL MET</h3>
        <span class='metric-label'>2029 Projection</span><br>
        <span class='metric-value'>${actual_2029:,.0f}</span><br>
        <span class='metric-label' style='color:green'>+${gap:,.0f} Surplus</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='miss-box'>
        <h3>⚠️ GAP TO GOAL</h3>
        <span class='metric-label'>2029 Projection</span><br>
        <span class='metric-value'>${actual_2029:,.0f}</span><br>
        <span class='metric-label' style='color:red'>-${abs(gap):,.0f} Shortfall</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("### 💡 Tech Revenue Reality")
    # Calculate the Blended Tech Revenue
    # Labor Capacity = 2080 * Util * BillRate
    lab_cap = 2080 * utilization * bill_rate
    # Total Ticket = Labor / (1 - Parts%)
    tot_cap = lab_cap / (1 - (job_parts_pct/100))
    parts_cap = tot_cap - lab_cap
    
    st.write(f"**Labor Revenue:** ${lab_cap:,.0f}")
    st.write(f"**+ Job Parts:** ${parts_cap:,.0f}")
    st.markdown(f"**= Total per Tech:** :blue[**${tot_cap:,.0f}**]")
    st.caption(f"This is the actual revenue 1 Tech generates at {utilization*100:.0f}% utilization.")

with c_chart:
    st.subheader("Revenue Mix to $7.5M")
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Stacked Bar
    years = df['Year']
    p1 = ax.bar(years, df['Rev: Labor'], label='Service Labor', color='#1976d2')
    p2 = ax.bar(years, df['Rev: Job Parts'], bottom=df['Rev: Labor'], label='Job Parts', color='#64b5f6')
    p3 = ax.bar(years, df['Rev: S-Jobs'], bottom=df['Rev: Labor']+df['Rev: Job Parts'], label='S-Jobs', color='#ff9800')
    p4 = ax.bar(years, df['Rev: Spares'], bottom=df['Rev: Labor']+df['Rev: Job Parts']+df['Rev: S-Jobs'], label='Pure Spares', color='#4caf50')
    
    # Target Line
    ax.axhline(y=exit_target, color='red', linestyle='--', linewidth=2, label='Exit Target')
    
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    st.pyplot(fig)

st.divider()

# ==========================================
# 4. DATA TABLES
# ==========================================

st.subheader("Detailed Projections")
view = df[['Year', 'Total Revenue', 'Rev: Labor', 'Rev: Job Parts', 'Rev: S-Jobs', 'Rev: Spares', 'EBITDA', 'EBITDA %']].copy()

# Formatting
for c in view.columns:
    if "Rev" in c or "EBITDA" == c:
        view[c] = view[c].apply(lambda x: f"${x:,.0f}")
view['EBITDA %'] = view['EBITDA %'].apply(lambda x: f"{x*100:.1f}%")

st.dataframe(view, use_container_width=True)

st.markdown("""
### 🧠 How to use this to hit your number:
1.  **Start with Labor:** Adjust `Year 1 Labor Rev` and `Labor Growth`. This is your engine.
2.  **Adjust the Attach Rate:** Use `Parts % of Service Ticket`. Increasing this pumps up revenue without adding headcount (Techs just sell more parts per job).
3.  **Layer S-Jobs & Spares:** These are your "layer cakes" on top.
4.  **Watch the Goal Box:** Keep tweaking until the red box turns **Green**.
""")
