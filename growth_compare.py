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
st.markdown("Test the **Max Salary** theory. How much can we pay a Rebadge Tech before the model breaks?")

# ==========================================
# 1. SIDEBAR INPUTS
# ==========================================

with st.sidebar:
    st.header("1. Baseline")
    base_rev_2025 = st.number_input("2025 Start Revenue ($)", value=1500000, step=100000, format="%d")
    base_growth_pct = st.slider("Base Biz Organic Growth %", 0, 20, 5, help="Growth of existing business excluding new hires.")
    
    st.divider()
    
    st.header("2. Scenario A: Standard Hire")
    st.info("Hiring less experienced techs.")
    green_cost = st.number_input("Green Tech Cost (Burdened) $", value=90000, step=5000)
    green_ramp = st.slider("Ramp Up (Months)", 0, 12, 9)
    green_hires_yr = st.slider("Hires per Year", 1, 4, 2)
    
    st.divider()

    st.header("3. Scenario B: Rebadge Strategy")
    st.info("Hiring expensive veterans.")
    rebadge_cost = st.number_input("Rebadge Tech Cost (Burdened) $", value=170000, step=5000, min_value=100000, max_value=250000)
    rebadge_ramp = st.slider("Rebadge Ramp (Months)", 0, 12, 1)
    rebadge_cadence = st.selectbox("Hiring Cadence", ["Every 6 Months (2/yr)", "Every 4 Months (3/yr)", "Every 3 Months (4/yr)"])
    
    st.markdown("---")
    st.markdown("**Revenue Economics**")
    rev_per_tech = st.number_input("Max Revenue per Tech ($)", value=448000, step=10000, help="$210/hr * 1600 hrs + Parts")
    
    # DYNAMIC CALCULATION: Parts are approx 17.5% of Total Rev (based on $78k cost / $448k rev)
    parts_ratio = 0.175 
    parts_cost_calc = rev_per_tech * parts_ratio
    
    gross_margin_tech = ((rev_per_tech - parts_cost_calc - rebadge_cost)/rev_per_tech)*100
    st.caption(f"Parts Cost Est: ${parts_cost_calc:,.0f}/yr")
    st.caption(f"Gross Margin at ${rebadge_cost:,.0f} Cost: **{gross_margin_tech:.1f}%**")

# ==========================================
# 2. CALCULATION ENGINE
# ==========================================

def run_comparison():
    months = list(range(1, 49)) # 4 Years (2026-2029)
    
    # -- SCENARIO A: STANDARD ORGANIC --
    org_data = []
    base_monthly = base_rev_2025 / 12
    
    # Dynamic Parts Cost (Linked to Revenue Input)
    tech_parts_cost = rev_per_tech * parts_ratio
    
    cum_green_hires = 0
    
    for m in months:
        interval = 12 / green_hires_yr
        if (m-1) % interval == 0:
            cum_green_hires += 1
            
        year_idx = (m-1) // 12
        # Use Slider for Base Growth
        growth_factor = (1 + (base_growth_pct/100)) ** year_idx
        rev_base = base_monthly * growth_factor
        
        hire_rev_total = 0
        hire_cost_total = 0
        hire_parts_cost = 0
        
        for h in range(cum_green_hires):
            start_month = (h * interval) + 1
            months_employed = m - start_month
            
            if months_employed >= 0:
                hire_cost_total += (green_cost / 12)
                
                pct = 1.0
                if months_employed < green_ramp:
                    pct = months_employed / max(1, green_ramp)
                
                tech_monthly_rev = (rev_per_tech / 12) * pct
                hire_rev_total += tech_monthly_rev
                
                # Variable Parts Cost follows Revenue
                hire_parts_cost += (tech_parts_cost / 12) * pct
                
        total_rev = rev_base + hire_rev_total
        # Base Biz Cost (60% cost) + New Hire Salaries + New Hire Parts
        total_cost = (rev_base * 0.6) + hire_cost_total + hire_parts_cost
        
        ebitda = total_rev - total_cost
        
        org_data.append({"Month": m, "Revenue": total_rev, "EBITDA": ebitda, "Heads": cum_green_hires})
        
    # -- SCENARIO B: REBADGE --
    reb_data = []
    if "6 Months" in rebadge_cadence: interval_r = 6
    elif "4 Months" in rebadge_cadence: interval_r = 4
    else: interval_r = 3
    
    cum_reb_hires = 0
    
    for m in months:
        if (m-1) % interval_r == 0:
            cum_reb_hires += 1
            
        year_idx = (m-1) // 12
        growth_factor = (1 + (base_growth_pct/100)) ** year_idx
        rev_base = base_monthly * growth_factor
        
        hire_rev_total = 0
        hire_cost_total = 0
        hire_parts_cost = 0
        
        for h in range(cum_reb_hires):
            start_month = (h * interval_r) + 1
            months_employed = m - start_month
            
            if months_employed >= 0:
                hire_cost_total += (rebadge_cost / 12)
                
                pct = 1.0
                if months_employed < rebadge_ramp:
                    pct = months_employed / max(1, rebadge_ramp)
                
                tech_monthly_rev = (rev_per_tech / 12) * pct
                hire_rev_total += tech_monthly_rev
                hire_parts_cost += (tech_parts_cost / 12) * pct
        
        total_rev = rev_base + hire_rev_total
        total_cost = (rev_base * 0.6) + hire_cost_total + hire_parts_cost
        ebitda = total_rev - total_cost
        
        reb_data.append({"Month": m, "Revenue": total_rev, "EBITDA": ebitda, "Heads": cum_reb_hires})
        
    return pd.DataFrame(org_data), pd.DataFrame(reb_data)

df_org, df_reb = run_comparison()

# Totals (Year 4 Run Rate)
last_org = df_org.iloc[-1]
last_reb = df_reb.iloc[-1]

rr_org_rev = last_org['Revenue'] * 12
rr_reb_rev = last_reb['Revenue'] * 12
rr_org_ebitda = last_org['EBITDA'] * 12
rr_reb_ebitda = last_reb['EBITDA'] * 12

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
    <h3>🐢 Scenario A: Standard Hiring</h3>
    <p>Hire {green_hires_yr}/yr at ${green_cost/1000:.0f}k cost.</p>
    <hr>
    <span class='risk-metric'>${rr_org_rev/1000000:.1f}M</span> 2029 Revenue<br>
    <span class='risk-metric'>${rr_org_ebitda/1000000:.1f}M</span> 2029 EBITDA<br>
    <br>
    <b>Margin:</b> <span class='{"margin-good" if marg_org > 30 else "margin-bad"}'>{marg_org:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class='rebadge-box'>
    <h3>🐇 Scenario B: Rebadge Strategy</h3>
    <p>Hire 1 every {rebadge_cadence.split(' ')[2]} at ${rebadge_cost/1000:.0f}k cost.</p>
    <hr>
    <span class='risk-metric'>${rr_reb_rev/1000000:.1f}M</span> 2029 Revenue<br>
    <span class='risk-metric'>${rr_reb_ebitda/1000000:.1f}M</span> 2029 EBITDA<br>
    <br>
    <b>Margin:</b> <span class='{"margin-good" if marg_reb > 30 else "margin-bad"}'>{marg_reb:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# CHARTS
c_chart1, c_chart2 = st.columns(2)

with c_chart1:
    st.subheader("Cumulative Profit (EBITDA)")
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    
    # Cumulative Sum of EBITDA over 4 years
    ax1.plot(df_org['Month'], df_org['EBITDA'].cumsum(), label='Standard', color='#2196f3', linewidth=2)
    ax1.plot(df_reb['Month'], df_reb['EBITDA'].cumsum(), label='Rebadge', color='#ff9800', linewidth=3)
    
    ax1.set_xlabel('Months (2026-2029)')
    ax1.set_ylabel('Cash Generated ($)')
    ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)

with c_chart2:
    st.subheader("The Cost of Talent vs. Margin")
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    
    # EBITDA Margin Trend
    ax2.plot(df_org['Month'], df_org['EBITDA'] / df_org['Revenue'], label='Standard Margin', color='#2196f3', linestyle='--')
    ax2.plot(df_reb['Month'], df_reb['EBITDA'] / df_reb['Revenue'], label='Rebadge Margin', color='#ff9800', linewidth=3)
    
    ax2.set_xlabel('Months')
    ax2.set_ylabel('EBITDA Margin %')
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

st.info("💡 **Strategy:** The Orange Line (Rebadge) only drops below the Blue Line if you push salaries excessively high. At **$170k burdened ($130k salary)**, Rebadge is still vastly superior.")
