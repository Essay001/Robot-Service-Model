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
    .goal-box {background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 10px solid #2e7d32; text-align: center;}
    .miss-box {background-color: #ffebee; padding: 20px; border-radius: 10px; border-left: 10px solid #c62828; text-align: center;}
    .metric-label {font-size: 14px; color: #555;}
    .metric-value {font-size: 26px; font-weight: bold;}
    .audit-box {background-color: #fff8e1; padding: 15px; border-radius: 5px; border-left: 5px solid #ffc107; font-size: 14px; margin-top: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 2029 Strategic Exit Model")
st.markdown("The complete business plan: **4-Stream Revenue**, **Resource Loading**, **Attrition**, and **Audit Trails**.")

# ==========================================
# 1. SIDEBAR: THE CONTROL TOWER
# ==========================================

with st.sidebar:
    st.header("1. The Exit Goal")
    exit_target = st.number_input("2029 Revenue Target ($)", value=7500000, step=250000, format="%d")

    st.divider()

    st.header("2. Revenue Stream A: Labor")
    st.caption("Revenue generated strictly by billing hours.")
    tm_labor_base = st.number_input("Year 1 Labor Rev ($)", value=2000000, step=100000, format="%d")
    tm_growth = st.slider("Labor Growth %", 0, 100, 20)
    bill_rate = st.number_input("Bill Rate ($/hr)", value=210, format="%d")
    utilization = st.slider("Tech Utilization %", 50, 100, 80) / 100

    st.divider()

    st.header("3. Revenue Stream B: Job Parts")
    st.caption("Parts attached to service tickets.")
    # If Parts is 25% of the TOTAL ticket, then Labor is 75%.
    job_parts_pct = st.slider("Parts % of Service Ticket", 0, 50, 25, help="Example: If 25%, then for every $750 of Labor, you sell $250 of Parts.")
    job_parts_margin = st.slider("Job Parts Margin %", 0, 100, 30)

    st.divider()

    st.header("4. Revenue Stream C: S-Jobs")
    st.caption("Fixed Bid Projects.")
    s_job_base = st.number_input("Year 1 S-Job Rev ($)", value=1000000, step=100000, format="%d")
    s_job_growth = st.slider("S-Job Growth %", 0, 100, 15)
    
    with st.expander("S-Job Cost & Resources"):
        sj_mat_pct = st.slider("S-Job Mat Cost %", 0, 100, 50)
        sj_lab_pct = st.slider("S-Job Labor Cost %", 0, 100, 30)
        st.caption("Resource Split (Labor Portion):")
        c1, c2 = st.columns(2)
        w_tech = c1.number_input("Tech %", value=20, format="%d")/100
        w_me = c2.number_input("ME %", value=40, format="%d")/100
        w_ce = c1.number_input("CE %", value=20, format="%d")/100
        w_prog = c2.number_input("Prog %", value=20, format="%d")/100

    st.divider()

    st.header("5. Revenue Stream D: Spare Parts")
    st.caption("Pure Box Sales (No Labor).")
    spares_base = st.number_input("Year 1 Spare Parts Rev ($)", value=500000, step=50000, format="%d")
    spares_growth = st.slider("Spare Parts Growth %", 0, 100, 10)
    spares_margin = st.slider("Spare Parts Margin %", 0, 100, 35)

    st.divider()

    st.header("6. Costs & Baseline")
    with st.expander("Operational Details"):
        st.caption("Baseline Staff (Already Hired):")
        base_techs = st.number_input("Base Techs", value=2)
        base_me = st.number_input("Base ME", value=1)
        base_ce = st.number_input("Base CE", value=1)
        base_prog = st.number_input("Base Prog", value=1)
        
        st.caption("Costs:")
        cost_tech = st.number_input("Tech Cost ($/hr)", value=85, format="%d")
        cost_eng = st.number_input("Eng Cost ($/hr)", value=95, format="%d")
        
        # RESTORED INPUT
        techs_per_loc_input = st.number_input("Max Techs per Location", value=6)
        
        rent = st.number_input("Rent ($/mo)", value=5000, format="%d")
        central = st.number_input("Central Support ($/mo)", value=8000, format="%d")
        
        st.caption("Hiring & Sales:")
        attrition = st.slider("Attrition %", 0, 20, 10)
        hire_cost = st.number_input("Hire Cost ($)", value=12000, format="%d")
        sales_trigger = st.number_input("Rev per Sales Rep", value=3000000, format="%d")
        
        inflation = st.slider("Inflation %", 0, 10, 3) / 100

# ==========================================
# 2. LOGIC ENGINE
# ==========================================

def run_fusion_model():
    years = [2026, 2027, 2028, 2029]
    data = []
    
    # Growth Trackers
    curr_labor_target = tm_labor_base
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
        
        # 1. INFLATED COSTS
        c_tech_inf = cost_tech * inf
        c_eng_inf = cost_eng * inf
        c_bill_inf = bill_rate * inf
        c_hire_inf = hire_cost * inf
        c_rent_inf = rent * inf
        
        # 2. CALCULATE REVENUE STREAMS
        if i > 0:
            curr_labor_target = curr_labor_target * (1 + tm_growth/100)
            curr_sjob_target = curr_sjob_target * (1 + s_job_growth/100)
            curr_spares_target = curr_spares_target * (1 + spares_growth/100)
            
        # Logic B: Job Parts (Attach Rate)
        # Total Ticket = Labor / (1 - Parts%)
        # Parts = Total - Labor
        total_ticket_rev = curr_labor_target / (1 - (job_parts_pct/100))
        curr_job_parts_rev = total_ticket_rev - curr_labor_target
        
        # Total Top Line
        total_rev = curr_labor_target + curr_job_parts_rev + curr_sjob_target + curr_spares_target
        
        # 3. RESOURCE LOADING
        # A. Techs for Service Labor
        # Capacity = 2080 * Util * BillRate
        labor_capacity_per_tech = 2080 * utilization * c_bill_inf
        techs_for_service = math.ceil(curr_labor_target / labor_capacity_per_tech)
        
        # B. Resources for S-Jobs
        sj_labor_budget = curr_sjob_target * (sj_lab_pct / 100)
        sj_tech_fte = (sj_labor_budget * w_tech) / (c_tech_inf * 2080)
        sj_me_fte = (sj_labor_budget * w_me) / (c_eng_inf * 2080)
        sj_ce_fte = (sj_labor_budget * w_ce) / (c_eng_inf * 2080)
        sj_prog_fte = (sj_labor_budget * w_prog) / (c_eng_inf * 2080)
        
        # C. Total Headcount Requirements
        req_techs = math.ceil(techs_for_service + sj_tech_fte)
        req_me = math.ceil(sj_me_fte)
        req_ce = math.ceil(sj_ce_fte)
        req_prog = math.ceil(sj_prog_fte)
        
        # 4. HIRING & ATTRITION
        # Techs
        new_techs = max(0, req_techs - cum_techs)
        cum_techs = max(cum_techs, req_techs)
        # Eng
        new_me = max(0, req_me - cum_me)
        cum_me = max(cum_me, req_me)
        new_ce = max(0,)

