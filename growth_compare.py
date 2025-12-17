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
    .rebadge-box {background-color: #fff3e0; padding: 15px; border-radius: 10px; border-left: 5px solid #ff9800;}
    .risk-metric {font-size: 24px; font-weight: bold;}
    .margin-good {color: green; font-weight: bold;}
    .margin-bad {color: red; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Talent Strategy: Green vs. Rebadge")
st.markdown("Comparing **Standard Hiring** (Lower cost, slow ramp) vs. **Rebadging** (High cost, instant revenue).")

# ==========================================
# 1. SIDEBAR INPUTS
# ==========================================

with st.sidebar:
    st.header("1. Baseline")
    base_rev_2025 = st.number_input("2025 Start Revenue ($)", value=1500000, step=100000, format="%d")
    
    # UPDATED DEFAULT: 12%
    base_growth_pct = st.slider("Base Biz Organic Growth %", 0, 20, 12)
    
    st.divider()
    
    st.header("2. Revenue Economics")
    # UPDATED DEFAULT: $438,000
    rev_per_tech = st.number_input("Max Revenue per Tech ($)", value=438000, step=10000)
    parts_ratio = 0.175 # Hardcoded approx based on prev discussion
    
    st.divider()
    
    st.header("3. Scenario Inputs (Apples to Apples)")
    
    # Unified Slider
    hires_per_year = st.slider("Hires Per Year (Both Scenarios)", 1, 6, 2, help="We hire the same number of people in both models.")
    
    st.markdown("---")
    st.caption("🐢 **Scenario A: Green Techs**")
    
    # UPDATED DEFAULT: $75,000
    green_cost = st.number_input("Green Start Cost ($)", value=75000, step=5000)
    
    # UPDATED DEFAULT: 12 Months
    green_ramp = st.slider("Green Ramp Up (Months)", 0, 18, 12)
    
    # NEW: REALITY CHECK
    green_raise_yr3 = st.checkbox("Apply Market Raise in Year 3?", value=True, help="If checked, Green tech cost jumps to $120k after 2 years so they don't quit.")
    
    st.markdown("---")
    st.caption("🐇 **Scenario B: Rebadge Techs**")
    rebadge_cost = st.number_input("Rebadge Cost ($)", value=130000, step=5000)
    rebadge_ramp = st.slider("Rebadge Ramp (Months)", 0, 12, 1)

# ==========================================
# 2. CALCULATION ENGINE
# ==========================================

def run_comparison():
    months = list(range(1, 49)) # 4 Years (2026-2029)
    base_monthly = base_rev_2025 / 12
    tech_parts_cost = rev_per_tech * parts_ratio
    
    # -- SCENARIO A: STANDARD ORGANIC --
    org_data = []
    cum_green_hires = 0
    
    for m in months:
        # Hiring Logic: Spread evenly
        interval = 12 / hires_per_year
        if (m-1) % interval == 0:
            cum_green_hires += 1
            
        # Base Growth
        year_idx = (m-1) // 12
        growth_factor = (1 + (base_growth_pct/100)) ** year_idx
        rev_base = base_monthly * growth_factor
        
        hire_rev_total = 0
        hire_cost_total = 0
        hire_parts_cost = 0
        
        for h in range(cum_green_hires):
            start_month = (h * interval) + 1
            months_employed = m - start_month
            
            if months_employed >= 0:
                # COST LOGIC: Do they get a raise?
                current_cost = green_cost
                if green_raise_yr3 and months_employed > 24:
                    current_cost = 120000 # Market correction raise
                
                hire_cost_total += (current_cost / 12)
                
                # REVENUE LOGIC: Ramp
                pct = 1.0
                if months_employed < green_ramp:
                    pct = months_employed / max(1, green_ramp)
                
                hire_rev_total += (rev_per_tech / 12) * pct
                hire_parts_cost += (tech_parts_cost / 12) * pct
                
        total_rev = rev_base + hire_rev_total
        total_cost = (rev_base * 0.6) + hire_cost_total + hire_parts_cost
        ebitda = total_rev - total_cost
        
        org_data.append({"Month": m, "Revenue": total_rev, "EBITDA": ebitda})
        
    # -- SCENARIO B: REBADGE --
    reb_data = []
    cum_reb_hires = 0
    
    for m in months:
        # Same Hiring Interval
        interval = 12 / hires_per_year
        if (m-1) % interval == 0:
            cum_reb_hires += 1
            
        year_idx = (m-1) // 12
        growth_factor = (1 + (base_growth_pct/100)) ** year_idx
        rev_base = base_monthly * growth_factor
        
        hire_rev_total = 0
        hire_cost_total = 0
        hire_parts_cost = 0
        
        for h in range(cum_reb_hires):
            start_month = (h * interval) + 1
            months_employed = m - start_month
            
            if months_employed >= 0:
                hire_cost_total += (rebadge_cost / 12)
                
                # REBADGE RAMP (Faster)
                pct = 1.0
                if months_employed < rebadge_ramp:
                    pct = months_employed / max(1, rebadge_ramp)
                
                hire_rev_total += (rev_per_tech / 12) * pct
                hire_parts_cost += (tech_parts_cost / 12) * pct
        
        total_rev = rev_base + hire_rev_total
        total_cost = (rev_base * 0.6) + hire_cost_total + hire_parts_cost
        ebitda = total_rev - total_cost
        
        reb_data.append({"Month": m, "Revenue": total_rev, "EBITDA": ebitda})
        
    return pd.DataFrame(org_data), pd.DataFrame(reb_data)

df_org, df_reb = run_comparison()

# Totals (Year 4 Run Rate)
last_org = df_org.iloc[-1]
last_reb = df_reb.iloc[-1]

rr_org_rev = last_org['Revenue'] * 12
rr_reb_rev = last_reb['Revenue'] * 12
rr_org_ebitda = last_org['EBITDA'] * 12
rr_reb_ebitda = last_reb['EBITDA'] * 12

# Cumulative Cash (The Real Winner Metric)
cash_org = df_org['EBITDA'].sum()
cash_reb = df_reb['EBITDA'].sum()

# Margins
marg_org = (rr_org_ebitda / rr_org_rev) * 100
marg_reb = (rr_reb_ebitda / rr_reb_rev) * 100

# ==========================================
# 3. DASHBOARD
# ==========================================

c1, c2 = st.columns(2)

with c1:
    st.markdown(f"""
    <div class='org-box'>
    <h3>🐢 Scenario A: Green Techs</h3>
    <p><b>{hires_per_year}</b> hires/yr. <b>{green_ramp}</b> month ramp.</p>
    <hr>
    <span class='risk-metric'>${rr_org_rev/1000000:.1f}M</span> 2029 Revenue<br>
    <span class='risk-metric'>${rr_org_ebitda/1000000:.1f}M</span> 2029 EBITDA<br>
    <b>Margin:</b> {marg_org:.1f}%<br><br>
    <span style='font-size:20px'>🏦 <b>Total Cash Banked:</b> ${cash_org/1000000:.2f}M</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    delta_cash = cash_reb - cash_org
    st.markdown(f"""
    <div class='rebadge-box'>
    <h3>🐇 Scenario B: Rebadge Techs</h3>
    <p><b>{hires_per_year}</b> hires/yr. <b>{rebadge_ramp}</b> month ramp.</p>
    <hr>
    <span class='risk-metric'>${rr_reb_rev/1000000:.1f}M</span> 2029 Revenue<br>
    <span class='risk-metric'>${rr_reb_ebitda/1000000:.1f}M</span> 2029 EBITDA<br>
    <b>Margin:</b> {marg_reb:.1f}%<br><br>
    <span style='font-size:20px'>🏦 <b>Total Cash Banked:</b> ${cash_reb/1000000:.2f}M</span><br>
    <span style='color:green; font-weight:bold'>(+${delta_cash/1000:.0f}k more cash)</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# CHARTS
c_chart1, c_chart2 = st.columns(2)

with c_chart1:
    st.subheader("Cumulative Cash (EBITDA)")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(df_org['Month'], df_org['EBITDA'].cumsum(), label='Green', color='#2196f3', linewidth=2)
    ax1.plot(df_reb['Month'], df_reb['EBITDA'].cumsum(), label='Rebadge', color='#ff9800', linewidth=3)
    ax1.fill_between(df_reb['Month'], df_org['EBITDA'].cumsum(), df_reb['EBITDA'].cumsum(), color='#ff9800', alpha=0.1)
    
    ax1.set_xlabel('Months (2026-2029)')
    ax1.set_ylabel('Total Cash Generated ($)')
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax1.legend()
    st.pyplot(fig1)

with c_chart2:
    st.subheader("Monthly EBITDA Trend")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(df_org['Month'], df_org['EBITDA'], label='Green', color='#2196f3', alpha=0.6)
    ax2.plot(df_reb['Month'], df_reb['EBITDA'], label='Rebadge', color='#ff9800', linewidth=3)
    
    ax2.set_xlabel('Months (2026-2029)')
    ax2.set_ylabel('Monthly EBITDA ($)')
    ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax2.legend()
    st.pyplot(fig2)

st.info("💡 **The Insight:** Even if the Green Tech margin % catches up in Year 4, look at the **'Total Cash Banked'**. The Rebadge strategy generates significantly more cash over the 4-year period because you never suffered through the 'Training Dip'.")
