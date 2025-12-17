import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

st.set_page_config(page_title="Executive Visuals Deck (Live Data)", layout="wide")

st.title("📸 Presentation Visuals Generator")
st.markdown("These charts are linked directly to your **Exit Model Scenario** settings.")

# ==========================================
# 1. HARDCODED SCENARIO SETTINGS (From Export)
# ==========================================
# --- 2025 BASELINE ---
act_rev_labor = 900000
act_rev_parts = 425000
act_rev_sjob = 750000
act_rev_spares = 110000
act_total_rev = act_rev_labor + act_rev_parts + act_rev_sjob + act_rev_spares # 2.185M

# --- 2026 TARGETS ---
tm_service_base = 1750000 # Service Target
s_job_base = 750000       # S-Job Target
spares_base = 150000      # Spares Target
target_total_rev = tm_service_base + s_job_base + spares_base

# --- MARGIN & SPLIT ---
labor_split_pct = 75
bill_rate = 210
utilization_pct = 75
mix_mat_pct = 60
mix_lab_pct = 100 - mix_mat_pct # Calculated

# --- TALENT ---
g_base = 75000
r_base = 130000
g_ramp_months = 12 # implied by 50% yr1 factor
r_ramp_months = 1  # implied by 92% yr1 factor

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.header("🖼️ Chart Dimensions")
    st.info("Adjust these to fit your slide.")
    c_width = st.slider("Chart Width (Inches)", 4, 15, 8) 
    c_height = st.slider("Chart Height (Inches)", 3, 10, 5)

# ==========================================
# CHART 1: REVENUE BRIDGE (WATERFALL) - ACTUAL DATA
# ==========================================
st.header("Slide 1: The 'Revenue Bridge' (Waterfall)")
st.caption(f"Bridge from 2025 Actuals (${act_total_rev/1e6:.2f}M) to 2026 Target (${target_total_rev/1e6:.2f}M)")

# Calculate Deltas
# Service Growth
service_2025 = act_rev_labor + act_rev_parts
delta_service = tm_service_base - service_2025

# S-Job Growth
delta_sjob = s_job_base - act_rev_sjob

# Spares Growth
delta_spares = spares_base - act_rev_spares

wf_data = {
    'Category': ['2025 Actuals', 'Service Growth', 'S-Job Delta', 'Parts/Spares Growth', '2026 Target'],
    'Value': [act_total_rev, delta_service, delta_sjob, delta_spares, 0.0],
    'Type': ['Base', 'Add', 'Add', 'Add', 'Total']
}
df_wf = pd.DataFrame(wf_data)

# Waterfall Logic
df_wf['cumsum'] = df_wf['Value'].cumsum()
df_wf.loc[4, 'Value'] = target_total_rev # Explicitly set total bar height

fig1, ax1 = plt.subplots(figsize=(c_width, c_height))
bottom = 0

for i, row in df_wf.iterrows():
    val = row['Value']
    cat = row['Category']
    
    if row['Type'] == 'Base':
        ax1.bar(cat, val, color='#1565c0', edgecolor='black', width=0.6)
        bottom = val
    elif row['Type'] == 'Total':
        ax1.bar(cat, val, color='#1565c0', edgecolor='black', width=0.6)
    else:
        # Growth Bar
        color = '#4caf50' if val >= 0 else '#f44336' # Green if pos, Red if neg
        ax1.bar(cat, val, bottom=bottom, color=color, edgecolor='black', width=0.6)
        bottom += val

# Formatting
ax1.set_ylabel('Revenue ($)')
ax1.set_title('Growth Bridge: 2025 to 2026')
ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
plt.xticks(rotation=0)
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# Labels
for p in ax1.patches:
    width, height = p.get_width(), p.get_height()
    x, y = p.get_xy()
    if abs(height) > 0:
        label_val = height
        # If it's a total/base bar, use the height (y+height is top). If add, use height.
        # Simplification for visibility:
        ax1.text(x+width/2, y+height/2, '${:,.0f}k'.format(height/1000), 
                 ha='center', va='center', color='white', fontweight='bold', fontsize=9)

st.pyplot(fig1)

st.divider()

# ==========================================
# CHART 2: THE CASH FLOW J-CURVE (LIVE CALC)
# ==========================================
st.header("Slide 2: The 'Training Trap' (J-Curve)")
st.caption("Cumulative Cash Flow: Comparing your actual Talent Settings.")

months = list(range(1, 13))

# Monthly Revenue Potential (Full Utilization)
# Rev per tech = 2080 * 210 * 75% = $327,600 / 12 = $27,300/mo
monthly_rev_cap = (2080 * bill_rate * (utilization_pct/100)) / 12 

# GREEN SCENARIO
green_monthly_cost = (g_base * 1.11 + 23000) / 12
green_cash_flow = []
cum_g = 0
for m in months:
    # Ramp Logic: Linear ramp over 12 months
    ramp = min(m / g_ramp_months, 1.0)
    rev = monthly_rev_cap * ramp
    cash = rev - green_monthly_cost
    cum_g += cash
    green_cash_flow.append(cum_g)

# REBADGE SCENARIO
rebadge_monthly_cost = (r_base * 1.11 + 23000) / 12
rebadge_cash_flow = []
cum_r = 0
for m in months:
    # Ramp Logic: Instant (1 month)
    ramp = min(m / r_ramp_months, 1.0)
    rev = monthly_rev_cap * ramp
    cash = rev - rebadge_monthly_cost
    cum_r += cash
    rebadge_cash_flow.append(cum_r)

fig2, ax2 = plt.subplots(figsize=(c_width, c_height))
ax2.plot(months, green_cash_flow, label=f'Green (${g_base/1000:.0f}k)', color='#f44336', linewidth=3, linestyle='--')
ax2.plot(months, rebadge_cash_flow, label=f'Rebadge (${r_base/1000:.0f}k)', color='#4caf50', linewidth=4)
ax2.axhline(0, color='black', linewidth=1)

ax2.set_ylabel('Cumulative Cash Contribution ($)')
ax2.set_xlabel('Months after Hire')
ax2.set_title('ROI Speed: Green vs. Rebadge')
ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax2.legend()
ax2.grid(True, alpha=0.3)

st.pyplot(fig2)

st.divider()

# ==========================================
# CHART 3: REVENUE MOMENTUM (STACKED AREA)
# ==========================================
st.header("Slide 3: 2026 Quarterly Revenue Mix")
st.caption("Visualizing the composition of the $2.65M Target.")

quarters = ['Q1', 'Q2', 'Q3', 'Q4']

# Distribute Targets across quarters (Simple Step Up Growth Curve)
# Service Labor ($1.75M * 75% = $1.31M)
q_labor = [300000, 320000, 340000, 352500] # Approx sums to 1.31M
# Service Parts ($1.75M * 25% = $437k)
q_parts = [100000, 105000, 110000, 122500] # Approx sums to 437k
# S-Jobs ($750k) - Lumpy? Let's smooth it.
q_sjobs = [150000, 175000, 200000, 225000] # Sums to 750k
# Spares ($150k)
q_spares = [30000, 35000, 40000, 45000]    # Sums to 150k

fig4, ax4 = plt.subplots(figsize=(c_width, c_height))
ax4.stackplot(quarters, q_labor, q_parts, q_sjobs, q_spares, 
              labels=['Service Labor', 'Job Parts', 'S-Projects', 'Spare Parts'],
              colors=['#1565c0', '#64b5f6', '#ffb74d', '#81c784'], alpha=0.9)

ax4.set_ylabel('Quarterly Revenue ($)')
ax4.set_title('2026 Revenue Composition Plan')
ax4.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax4.legend(loc='upper left', fontsize='small')
ax4.grid(axis='y', linestyle='--', alpha=0.3)

st.pyplot(fig4)
