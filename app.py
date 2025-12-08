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
    .resource-box {background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 12px;}
    .split-box {background-color: #f3f3f3; padding: 10px; border-radius: 5px; margin-top: 5px; margin-bottom: 15px; font-size: 13px;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 2029 Strategic Exit Model")
st.markdown("The complete business plan: **4-Stream Revenue**, **Resource Loading**, **Attrition**, and **Audit Trails**.")

# ==========================================
# 1. SIDEBAR: THE CONTROL TOWER
# ==========================================

with st.sidebar:
    st.header("1. Strategic Goals")
    c_g1, c_g2 = st.columns(2)
    target_2026 = c_g1.number_input("2026 Target ($)", value=4000000, step=250000, format="%d", help="Your goal for Year 1.")
    exit_target = c_g2.number_input("2029 Target ($)", value=7500000, step=250000, format="%d", help="Your Exit Number.")

    st.divider()

    # --- REVENUE INPUTS ---
    st.header("2. Service Revenue (Labor + Job Parts)")
    tm_service_base = st.number_input("Year 1 Total Service Rev ($)", value=2500000, step=100000, format="%d")
    tm_growth = st.slider("Service Growth %", 0, 100, 20)
    
    st.subheader("Revenue Split")
    labor_split_pct = st.slider("Split: % from Labor", 0, 100, 75)
    
    disp_labor = tm_service_base * (labor_split_pct/100)
    disp_parts = tm_service_base * (1 - (labor_split_pct/100))
    st.markdown(f"<div class='split-box'><b>Year 1 Breakdown:</b><br>🛠️ Labor: <b>${disp_labor:,.0f}</b><br>⚙️ Job Parts: <b>${disp_parts:,.0f}</b></div>", unsafe_allow_html=True)
    
    with st.expander("Service Settings"):
        bill_rate = st.number_input("Bill Rate ($/hr)", value=210, format="%d")
        utilization = st.slider("Tech Utilization %", 50, 100, 80) / 100
        job_parts_margin = st.slider("Job Parts Margin %", 0, 100, 30)

    st.divider()

    st.header("3. S-Jobs (Projects)")
    s_job_base = st.number_input("Year 1 S-Job Rev ($)", value=1000000, step=100000, format="%d")
    s_job_growth = st.slider("S-Job Growth %", 0, 100, 15)
    
    with st.expander("S-Job Settings"):
        sj_mat_pct = st.slider("S-Job Mat Cost %", 0, 100, 50)
        sj_lab_pct = st.slider("S-Job Labor Cost %", 0, 100, 30)
        c1, c2 = st.columns(2)
        w_tech = c1.number_input("Tech %", value=20, format="%d")/100
        w_me = c2.number_input("ME %", value=40, format="%d")/100
        w_ce = c1.number_input("CE %", value=20, format="%d")/100
        w_prog = c2.number_input("Prog %", value=20, format="%d")/100

    st.divider()

    st.header("4. Spare Parts (Direct)")
    spares_base = st.number_input("Year 1 Spare Parts Rev ($)", value=500000, step=50000, format="%d")
    spares_growth = st.slider("Spare Parts Growth %", 0, 100, 10)
    spares_margin = st.slider("Spare Parts Margin %", 0, 100, 35)

    st.divider()

    st.header("5. Costs & Baseline")
    with st.expander("Operational Details", expanded=True):
        st.caption("Baseline Staff (Already Hired):")
        base_techs = st.number_input("Base Techs", value=2)
        base_me = st.number_input("Base ME", value=1)
        base_ce = st.number_input("Base CE", value=1)
        base_prog = st.number_input("Base Prog", value=1)
        
        st.caption("Costs:")
        cost_tech = st.number_input("Tech Cost ($/hr)", value=85, format="%d")
        cost_eng = st.number_input("Eng Cost ($/hr)", value=95, format="%d")
        
        techs_per_loc_input = st.number_input("Max Techs per Location", value=6)
        
        # --- TIMING SECTION ---
        st.markdown("---")
        st.markdown("#### ⏳ Timing & Triggers")
        rent_per_loc = st.number_input("Rent ($/mo)", value=5000, format="%d")
        is_hq_free = st.checkbox("Is HQ Rent Free?", value=True, help="If checked, you only pay rent for Location 2, 3, etc.")
        
        central_cost = st.number_input("Central Support ($/mo)", value=8000, format="%d")
        central_start_year = st.selectbox("Start Central Support In:", [2026, 2027, 2028, 2029], index=1, help="Defers corporate allocations until this year.")
        
        st.markdown("---")
        
        st.caption("Hiring & Sales:")
        attrition = st.slider("Attrition %", 0, 20, 10)
        hire_cost = st.number_input("Hire Cost ($)", value=12000, format="%d")
        sales_trigger = st.number_input("Rev per Sales Rep", value=3000000, format="%d")
        sales_rep_cost = 120000
        
        inflation = st.slider("Inflation %", 0, 10, 3) / 100
        
        # Live calc of 2026 Total
        total_2026_input = tm_service_base + s_job_base + spares_base
        
        st.markdown(f"""
        <div class='resource-box'>
        <b>Year 1 Check:</b><br>
        Inputs Total: <b>${total_2026_input:,.0f}</b><br>
        Target: <b>${target_2026:,.0f}</b><br>
        Gap: <b style='color:{"green" if total_2026_input >= target_2026 else "red"}'>${total_2026_input - target_2026:,.0f}</b>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 2. LOGIC ENGINE
# ==========================================

def run_fusion_model():
    years = [2026, 2027, 2028, 2029]
    data = []
    
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
        
        # 1. INFLATED COSTS
        c_tech_inf = cost_tech * inf
        c_eng_inf = cost_eng * inf
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
        
        # 6. FINANCIALS
        
        # COGS
        cogs_labor_tech = cum_techs * 2080 * c_tech_inf
        total_eng_fte = sj_me_fte + sj_ce_fte + sj_prog_fte
        cogs_labor_eng = total_eng_fte * 2080 * c_eng_inf
        
        cogs_job_parts = curr_job_parts_rev * (1 - (job_parts_margin/100))
        cogs_spares = curr_spares_target * (1 - (spares_margin/100))
        cogs_sjob_mat = curr_sjob_target * (sj_mat_pct/100)
        
        total_cogs = cogs_labor_tech + cogs_labor_eng + cogs_job_parts + cogs_spares + cogs_sjob_mat
        gross_profit = total_rev - total_cogs
        
        # OpEx: RENT LOGIC UPDATE
        if is_hq_free:
            billable_locs = max(0, locs - 1)
        else:
            billable_locs = locs
            
        opex_rent = billable_locs * c_rent_inf * 12
        
        # OpEx: CENTRAL SUPPORT UPDATE
        if year >= central_start_year and locs > 1:
            central_fee = central_cost * 12 * inf
        else:
            central_fee = 0
            
        opex_mgr = managers * (85000 * 1.2 * inf)
        opex_sales = sales_reps * (sales_rep_cost * inf)
        opex_hire = total_hires * c_hire_inf
        
        total_opex = opex_rent + opex_mgr + opex_sales + central_fee + opex_hire
        
        ebitda = gross_profit - total_opex
        
        data.append({
            "Year": year,
            "Total Revenue": total_rev,
            "Rev: Labor": curr_labor_target,
            "Rev: Job Parts": curr_job_parts_rev,
            "Rev: S-Jobs": curr_sjob_target,
            "Rev: Spare Parts": curr_spares_target,
            "EBITDA": ebitda,
            "EBITDA %": ebitda/total_rev,
            "Techs": cum_techs,
            "MEs": cum_me,
            "CEs": cum_ce,
            "Progs": cum_prog,
            "Total Hires": total_hires,
            "Locations": locs,
            "Sales Reps": sales_reps,
            "OpEx: Rent": opex_rent,
            "OpEx: Central": central_fee,
            "Total COGS": total_cogs,
            "Total OpEx": total_opex
        })
        
    return pd.DataFrame(data)

df = run_fusion_model()

# ==========================================
# 3. GOAL SEEK DASHBOARD
# ==========================================

# Compare 2026 (Row 0) and 2029 (Row 3)
yr1 = df.iloc[0]
yr4 = df.iloc[-1]

c_goal1, c_goal2, c_chart = st.columns([1, 1, 3])

with c_goal1:
    gap_26 = yr1['Total Revenue'] - target_2026
    color_26 = "green" if gap_26 >= 0 else "red"
    label_26 = "Surplus" if gap_26 >= 0 else "Shortfall"
    
    st.markdown(f"""
    <div style='background-color: {"#e8f5e9" if gap_26 >= 0 else "#ffebee"}; padding: 15px; border-radius: 10px; border-left: 8px solid {color_26}; text-align: center;'>
    <h4>2026 Performance</h4>
    <span style='font-size:14px; color:#555;'>Projected</span><br>
    <span style='font-size:22px; font-weight:bold;'>${yr1['Total Revenue']:,.0f}</span><br>
    <span style='color:{color_26}; font-weight:bold;'>{'+' if gap_26>=0 else ''}${gap_26:,.0f} {label_26}</span>
    </div>
    """, unsafe_allow_html=True)

with c_goal2:
    gap_29 = yr4['Total Revenue'] - exit_target
    color_29 = "green" if gap_29 >= 0 else "red"
    label_29 = "Surplus" if gap_29 >= 0 else "Shortfall"
    
    st.markdown(f"""
    <div style='background-color: {"#e8f5e9" if gap_29 >= 0 else "#ffebee"}; padding: 15px; border-radius: 10px; border-left: 8px solid {color_29}; text-align: center;'>
    <h4>2029 Exit Status</h4>
    <span style='font-size:14px; color:#555;'>Projected</span><br>
    <span style='font-size:22px; font-weight:bold;'>${yr4['Total Revenue']:,.0f}</span><br>
    <span style='color:{color_29}; font-weight:bold;'>{'+' if gap_29>=0 else ''}${gap_29:,.0f} {label_29}</span>
    </div>
    """, unsafe_allow_html=True)

with c_chart:
    st.subheader("Revenue Path (With Margin)")
    fig, ax = plt.subplots(figsize=(10, 5))
    
    years = df['Year']
    p1 = ax.bar(years, df['Rev: Labor'], label='Service Labor', color='#1565c0')
    p2 = ax.bar(years, df['Rev: Job Parts'], bottom=df['Rev: Labor'], label='Job Parts', color='#64b5f6')
    p3 = ax.bar(years, df['Rev: S-Jobs'], bottom=df['Rev: Labor']+df['Rev: Job Parts'], label='S-Jobs', color='#ffb74d')
    p4 = ax.bar(years, df['Rev: Spare Parts'], bottom=df['Rev: Labor']+df['Rev: Job Parts']+df['Rev: S-Jobs'], label='Spare Parts', color='#81c784')
    
    # Data Labels
    for container in ax.containers:
        labels = [f'${v/1000000:.1f}M' if v > 100000 else "" for v in container.datavalues]
        ax.bar_label(container, labels=labels, label_type='center', color='white', fontsize=9, padding=0)

    # EBITDA Line
    ax2 = ax.twinx()
    ax2.plot(years, df['EBITDA %'] * 100, color='#212121', linestyle='-', linewidth=3, marker='o', label='EBITDA Margin')
    ax2.set_ylabel('EBITDA Margin (%)', color='#212121')
    
    # Legend at bottom
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
    
    # Target Lines
    ax.axhline(y=exit_target, color='red', linestyle='--', linewidth=2)
    ax.text(2026.5, exit_target, f" Exit: ${exit_target/1000000:.1f}M", color='red', va='bottom', fontweight='bold')
    
    ax.axhline(y=target_2026, color='blue', linestyle=':', linewidth=2)
    ax.text(2025.6, target_2026, f" 2026 Goal: ${target_2026/1000000:.1f}M", color='blue', va='bottom', fontsize=8)
    
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.spines['top'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)

st.divider()

# ==========================================
# 4. AUDIT CENTER (TABBED)
# ==========================================

st.subheader("🔍 Audit Center")

tab1, tab2, tab3 = st.tabs(["💰 P&L Detail", "👥 Headcount Path", "📊 Hiring & Ops"])

def format_df(d, m): return d.style.format(m)

with tab1:
    st.markdown("### Detailed P&L")
    cols = ['Year', 'Total Revenue', 'Rev: Labor', 'Rev: Job Parts', 'Rev: S-Jobs', 'Rev: Spare Parts', 
            'Total COGS', 'Total OpEx', 'EBITDA', 'EBITDA %']
    
    fmt = {'Year':'{:.0f}', 'EBITDA %':'{:.1%}'}
    for c in cols:
        if c not in fmt: fmt[c] = "${:,.0f}"
        
    st.dataframe(format_df(df[cols], fmt), use_container_width=True)

with tab2:
    st.markdown("### Resource Path")
    cols = ['Year', 'Techs', 'MEs', 'CEs', 'Progs', 'Locations', 'Sales Reps']
    fmt = {'Year':'{:.0f}', 'Techs':'{:.0f}', 'MEs':'{:.0f}', 'CEs':'{:.0f}', 'Progs':'{:.0f}', 'Locations':'{:.0f}', 'Sales Reps':'{:.0f}'}
    st.dataframe(format_df(df[cols], fmt), use_container_width=True)

with tab3:
    st.markdown("### Hiring & Operations")
    cols = ['Year', 'Total Hires', 'OpEx: Hiring', 'Eng FTE']
    fmt = {'Year':'{:.0f}', 'Total Hires':'{:.0f}', 'OpEx: Hiring':'${:,.0f}', 'Eng FTE':'{:.2f}'}
    st.dataframe(format_df(df[cols], fmt), use_container_width=True)
