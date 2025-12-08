import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Growth Strategy Comparison", layout="wide")

st.markdown("""
<style>
    .org-box {background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #2196f3;}
    .ma-box {background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #4caf50;}
    .risk-metric {font-size: 24px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ The 3-Year Horizon: Organic vs. M&A")
st.markdown("Comparing the **Linear Grind** of organic hiring vs. the **Step-Function** of acquisition over a 36-month period.")

# ==========================================
# 1. SIDEBAR INPUTS
# ==========================================

with st.sidebar:
    st.header("1. Baseline")
    base_rev_2025 = st.number_input("2025 Start Revenue ($)", value=1500000, step=100000, format="%d")
    # NEW SLIDER
    sjob_mix_pct = st.slider("S-Job Demand (% of Total Rev)", 10, 50, 20, help="How much of our revenue SHOULD be S-Jobs if we had capacity?")
    
    st.divider()
    
    st.header("2. Scenario A: Organic Grind")
    st.info("Linear hiring. Hard to scale fast.")
    hires_per_year = st.slider("New Techs Hired / Year", 1, 6, 3)
    ramp_months = st.slider("Ramp Up Time (Months)", 0, 12, 6)
    
    # THE OPS CONSTRAINT
    organic_sjob_cap = st.number_input("Max Organic S-Job ($/yr)", value=500000, step=50000, help="We hit a ceiling without our own Engineer.")

    st.divider()

    st.header("3. Scenario B: M&A Scale")
    st.info("Buying capacity & fixing it.")
    acq_month = st.slider("Acquisition Month", 1, 12, 3)
    acq_annual_rev = st.number_input("Acquired Revenue ($)", value=1200000, step=100000)
    acq_cost = st.number_input("One-Time Integration Cost", value=75000)
    
    # THE SCALE UNLOCK
    ma_sjob_cap = st.number_input("S-Job Unlock ($/yr)", value=1500000, step=100000, help="With volume, we hire a dedicated Engineer and uncap growth.")
    
    # SYNERGY
    st.markdown("**The Turnaround**")
    initial_margin = st.slider("Acquired Margin (Day 1)", 5, 30, 15, help="They run inefficiently when we buy them.")
    target_margin = st.slider("Target Margin (Year 2)", 20, 50, 35, help="We apply our Ops/Pricing to fix them.")

# ==========================================
# 2. CALCULATION ENGINE
# ==========================================

def run_comparison():
    months = list(range(1, 37)) # 3 Years
    
    # -- SCENARIO A: ORGANIC --
    org_data = []
    
    # Base Monthly Run Rate
    base_monthly = base_rev_2025 / 12
    tech_rev_mo = 35000 # Fully ramped tech revenue
    tech_cost_mo = 6000 # Fully burdened cost
    
    cumulative_hires = 0
    
    for m in months:
        # Hiring Logic: Hire 'hires_per_year' every Jan (Month 1, 13, 25)
        year_idx = (m-1) // 12
        if (m-1) % 12 == 0: 
            cumulative_hires += hires_per_year
            
        # Revenue Calculation
        rev = base_monthly * (1.05 ** year_idx) # Base grows 5% naturally
        
        # New Hires Revenue
        ramp_factor = 1.0
        if (m - (year_idx*12)) <= ramp_months:
            ramp_factor = 0.4 # 40% efficiency during ramp
            
        rev_from_hires = (cumulative_hires * tech_rev_mo) * ramp_factor
        rev += rev_from_hires
        
        # S-Job Constraint (The Ceiling)
        # Use the dynamic slider percentage now
        implied_sjob = rev * (sjob_mix_pct / 100)
        monthly_cap = organic_sjob_cap / 12
        
        capped_sjob_loss = 0
        if implied_sjob > monthly_cap:
            capped_sjob_loss = (implied_sjob - monthly_cap)
            rev -= capped_sjob_loss # We lose that revenue
            
        # Costs
        cost_base = rev * 0.60 # Standard 40% margin on base
        cost_hires = cumulative_hires * tech_cost_mo
        
        ebitda = rev - cost_base - cost_hires
        
        org_data.append({"Month": m, "Revenue": rev, "EBITDA": ebitda, "Lost_Rev": capped_sjob_loss})
        
    # -- SCENARIO B: M&A --
    ma_data = []
    
    for m in months:
        year_idx = (m-1) // 12
        
        rev = base_monthly * (1.05 ** year_idx)
        
        # Acquisition Impact
        acq_rev_monthly = 0
        if m >= acq_month:
            acq_rev_monthly = acq_annual_rev / 12
            if m > 12: acq_rev_monthly *= 1.10
            if m > 24: acq_rev_monthly *= 1.10
            rev += acq_rev_monthly
            
        # S-Job Unlock
        implied_sjob = rev * (sjob_mix_pct / 100)
        monthly_cap_ma = ma_sjob_cap / 12
        
        if implied_sjob > monthly_cap_ma:
            rev -= (implied_sjob - monthly_cap_ma)
            
        # Costs & Synergy
        cost_base = (base_monthly * (1.05 ** year_idx)) * 0.60
        cost_acq = 0
        if m >= acq_month:
            months_owned = m - acq_month
            if months_owned < 12:
                margin = initial_margin / 100
            else:
                margin = target_margin / 100
            cost_acq = acq_rev_monthly * (1 - margin)
            
        integration = acq_cost if m == acq_month else 0
        ebitda = rev - cost_base - cost_acq - integration
        
        ma_data.append({"Month": m, "Revenue": rev, "EBITDA": ebitda})
        
    return pd.DataFrame(org_data), pd.DataFrame(ma_data)

df_org, df_ma = run_comparison()

# Totals
total_org_rev = df_org['Revenue'].sum()
total_ma_rev = df_ma['Revenue'].sum()
total_org_ebitda = df_org['EBITDA'].sum()
total_ma_ebitda = df_ma['EBITDA'].sum()
total_lost_sjob = df_org['Lost_Rev'].sum()

# ==========================================
# 3. DASHBOARD
# ==========================================

c1, c2 = st.columns(2)

with c1:
    st.markdown(f"""
    <div class='org-box'>
    <h3>🚜 Scenario A: Organic (3 Years)</h3>
    <span class='risk-metric'>${total_org_rev:,.0f}</span> Revenue<br>
    <span class='risk-metric'>${total_org_ebitda:,.0f}</span> EBITDA<br>
    <br>
    <b>The Pain Point:</b><br>
    We lost <b style='color:red'>${total_lost_sjob:,.0f}</b> in S-Job revenue because we hit the Ops Constraint ceiling.
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='ma-box'>
    <h3>🚀 Scenario B: M&A (3 Years)</h3>
    <span class='risk-metric'>${total_ma_rev:,.0f}</span> Revenue<br>
    <span class='risk-metric'>${total_ma_ebitda:,.0f}</span> EBITDA<br>
    <br>
    <b>The Advantage:</b><br>
    The combined volume allowed us to hire a dedicated Engineer, capturing the S-Job upside.
    </div>
    """, unsafe_allow_html=True)

st.divider()

# CHARTS
c_chart1, c_chart2 = st.columns(2)

with c_chart1:
    st.subheader("Revenue Separation (Cumulative)")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(df_org['Month'], df_org['Revenue'].cumsum(), label='Organic', color='#2196f3', linewidth=2)
    ax1.plot(df_ma['Month'], df_ma['Revenue'].cumsum(), label='M&A', color='#4caf50', linewidth=3)
    ax1.fill_between(df_ma['Month'], df_org['Revenue'].cumsum(), df_ma['Revenue'].cumsum(), color='#4caf50', alpha=0.1)
    
    ax1.set_xlabel('Months (3 Years)')
    ax1.set_ylabel('Cum. Revenue ($)')
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax1.legend()
    st.pyplot(fig1)

with c_chart2:
    st.subheader("EBITDA Comparison (Quarterly)")
    # Group by Quarter
    df_org['Qtr'] = ((df_org['Month']-1)//3) + 1
    df_ma['Qtr'] = ((df_ma['Month']-1)//3) + 1
    
    q_org = df_org.groupby('Qtr')['EBITDA'].sum()
    q_ma = df_ma.groupby('Qtr')['EBITDA'].sum()
    
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.bar(q_org.index, q_org, label='Organic', color='#2196f3', alpha=0.6)
    ax2.plot(q_ma.index, q_ma, label='M&A', color='#4caf50', linewidth=3, marker='o')
    
    ax2.set_xlabel('Quarters (1-12)')
    ax2.set_ylabel('EBITDA ($)')
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax2.legend()
    st.pyplot(fig2)

st.info("💡 **Try it:** Increase 'S-Job Demand (%)' to 30% or 40% to see the Organic Model hit the ceiling faster.")
