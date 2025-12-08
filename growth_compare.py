import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Growth Strategy Comparison", layout="wide")

st.markdown("""
<style>
    .org-box {background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3;}
    .ma-box {background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50;}
    .risk-metric {font-size: 24px; font-weight: bold;}
    .delta-pos {color: green; font-weight: bold;}
    .delta-neg {color: red; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ The Growth Dilemma: Organic vs. M&A")
st.markdown("Compare the financial and operational reality of **Scaling Organically** (hiring fast) versus **Scaling via Acquisition** (buying capacity).")

# ==========================================
# 1. SIDEBAR INPUTS
# ==========================================

with st.sidebar:
    st.header("1. Shared Assumptions")
    base_rev_2025 = st.number_input("2025 Baseline Rev ($)", value=1500000, step=100000, format="%d")
    target_rev_2026 = st.number_input("2026 Revenue Goal ($)", value=2500000, step=100000, format="%d")
    
    st.divider()
    
    st.header("2. Scenario A: Organic Grind")
    st.info("Hiring new techs to hit the number.")
    hires_needed = st.slider("New Techs needed", 1, 5, 3)
    ramp_months = st.slider("Tech Ramp Up (Months)", 0, 12, 6, help="Months before a new hire is fully billable.")
    training_efficiency = st.slider("Training Efficiency %", 0, 100, 40, help="Productivity during ramp period.")
    
    st.markdown("---")
    st.markdown("**The 'Ops Constraint'**")
    st.caption("Without a dedicated engineer (which we can't afford yet), S-Job revenue is capped because Ops pulls resources back.")
    organic_sjob_cap = st.number_input("Max Organic S-Job Rev ($)", value=500000, step=50000, help="The ceiling on projects without a dedicated lead.")

    st.divider()

    st.header("3. Scenario B: M&A Scale")
    st.info("Buying a small integrator.")
    acq_month = st.slider("Acquisition Month (2026)", 1, 12, 3)
    acq_annual_rev = st.number_input("Target Annual Revenue ($)", value=1200000, step=100000)
    acq_cost = st.number_input("Acquisition Integration Cost ($)", value=50000, help="One-time legal/integration hit.")
    
    st.markdown("---")
    st.markdown("**The 'Scale Unlock'**")
    st.caption("Combined volume justifies a Central Engineer, uncapping S-Job growth.")
    ma_sjob_cap = st.number_input("New S-Job Potential ($)", value=1500000, step=100000)

# ==========================================
# 2. CALCULATION ENGINE
# ==========================================

def run_comparison():
    # Setup Monthly Timeline for 2026
    months = list(range(1, 13))
    
    # -- SCENARIO A: ORGANIC --
    org_data = []
    org_cum_rev = 0
    org_cum_cost = 0
    
    # Base Monthly Run Rate (from 2025)
    base_monthly = base_rev_2025 / 12
    
    # Costs
    tech_salary_mo = 7000 / 1.3 # ~$65k salary + burden
    
    for m in months:
        # Base Revenue
        rev = base_monthly
        
        # New Hires Revenue
        # They start Month 1. Are they ramped?
        if m <= ramp_months:
            # Training Mode
            hire_rev = (hires_needed * 35000) * (training_efficiency/100) # Full cap is ~$35k/mo
        else:
            # Ramped Mode
            hire_rev = (hires_needed * 35000) * 0.9 # 90% utilization
            
        rev += hire_rev
        
        # S-Job Constraint Check
        # Assume 20% of revenue is S-Job. Is it capped?
        implied_sjob = rev * 0.20
        monthly_cap = organic_sjob_cap / 12
        if implied_sjob > monthly_cap:
            rev -= (implied_sjob - monthly_cap) # Clip the revenue
            
        # Costs
        # We pay full salary from Day 1
        cost_labor = (hires_needed * tech_salary_mo) + (base_monthly * 0.6) # Base costs
        
        ebitda = rev - cost_labor
        
        org_data.append({
            "Month": m,
            "Revenue": rev,
            "EBITDA": ebitda,
            "Scenario": "Organic"
        })
        
    # -- SCENARIO B: M&A --
    ma_data = []
    
    for m in months:
        # Base Revenue
        rev = base_monthly
        
        # Acquisition Impact
        if m >= acq_month:
            acq_rev = acq_annual_rev / 12
            rev += acq_rev
            
            # S-Job Unlock
            # We assume we capture more S-Job work because we have capacity
            # Bonus 10% growth on top due to synergy
            rev = rev * 1.05 
            
        # Costs
        # Base Cost
        cost = base_monthly * 0.6
        
        # Acq Cost (Assume acquired company runs at break-even initially due to cleanup)
        if m >= acq_month:
            cost += (acq_annual_rev / 12) * 0.85 # 15% EBITDA margin acquired
            
        # Integration Hit
        if m == acq_month:
            cost += acq_cost
            
        ebitda = rev - cost
        
        ma_data.append({
            "Month": m,
            "Revenue": rev,
            "EBITDA": ebitda,
            "Scenario": "M&A"
        })
        
    return pd.DataFrame(org_data), pd.DataFrame(ma_data)

df_org, df_ma = run_comparison()

# Totals
total_org_rev = df_org['Revenue'].sum()
total_ma_rev = df_ma['Revenue'].sum()
total_org_ebitda = df_org['EBITDA'].sum()
total_ma_ebitda = df_ma['EBITDA'].sum()

# ==========================================
# 3. DASHBOARD
# ==========================================

c1, c2 = st.columns(2)

with c1:
    st.markdown(f"""
    <div class='org-box'>
    <h3>🚜 Scenario A: Organic Grind</h3>
    <p>Hire {hires_needed} Techs immediately. Fight for Ops resources.</p>
    <hr>
    <span class='risk-metric'>${total_org_rev:,.0f}</span> Revenue<br>
    <span class='risk-metric'>${total_org_ebitda:,.0f}</span> EBITDA<br>
    <br>
    <b>🚨 The Risks:</b>
    <ul>
    <li><b>Training Drag:</b> {ramp_months} months of low margin.</li>
    <li><b>Ops Ceiling:</b> S-Jobs capped at ${organic_sjob_cap:,.0f}.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='ma-box'>
    <h3>🚀 Scenario B: M&A Scale</h3>
    <p>Acquire Month {acq_month}. Instant Capacity. Dedicated Engineer.</p>
    <hr>
    <span class='risk-metric'>${total_ma_rev:,.0f}</span> Revenue<br>
    <span class='risk-metric'>${total_ma_ebitda:,.0f}</span> EBITDA<br>
    <br>
    <b>✅ The Arbitrage:</b>
    <ul>
    <li><b>Instant Revenue:</b> Day 1 billing from acquired book.</li>
    <li><b>Unlocked S-Jobs:</b> Volume justifies Central Engineer.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# CHARTS
c_chart1, c_chart2 = st.columns(2)

with c_chart1:
    st.subheader("Monthly Revenue Trajectory")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(df_org['Month'], df_org['Revenue'], label='Organic', color='#2196f3', linewidth=3, marker='o')
    ax1.plot(df_ma['Month'], df_ma['Revenue'], label='M&A', color='#4caf50', linewidth=3, marker='o')
    ax1.set_xlabel('Month (2026)')
    ax1.set_ylabel('Revenue ($)')
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)

with c_chart2:
    st.subheader("Cumulative EBITDA (The Cash Reality)")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    # Cumulative Sum
    ax2.plot(df_org['Month'], df_org['EBITDA'].cumsum(), label='Organic', color='#2196f3', linewidth=3)
    ax2.plot(df_ma['Month'], df_ma['EBITDA'].cumsum(), label='M&A', color='#4caf50', linewidth=3)
    ax2.set_xlabel('Month (2026)')
    ax2.set_ylabel('Cumulative EBITDA ($)')
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

st.divider()

st.subheader("The Verdict")
diff_rev = total_ma_rev - total_org_rev
diff_ebit = total_ma_ebitda - total_org_ebitda

st.markdown(f"""
By pursuing **M&A** instead of Organic growth in Year 1:
* You generate **${diff_rev:,.0f}** more Top Line Revenue.
* You preserve **${diff_ebit:,.0f}** in EBITDA (avoiding the "Training J-Curve").
* **Most Importantly:** You unlock the volume required to hire the Central Engineer, solving the "Ops Constraint" permanently.
""")
