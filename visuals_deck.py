import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

st.set_page_config(page_title="Executive Visuals Deck (Final)", layout="wide")

st.title("📸 Presentation Visuals Generator")
st.markdown("Charts calibrated to **$2.5M Target Scenario**.")

# ==========================================
# 1. HARDCODED SCENARIO INPUTS
# ==========================================
# 2025 ACTUALS
act_rev_labor = 900000
act_rev_parts = 425000
act_rev_sjob = 750000
act_rev_spares = 110000
act_total_rev = act_rev_labor + act_rev_parts + act_rev_sjob + act_rev_spares # $2.185M

# 2026 TARGETS
tm_service_target = 1650000
s_job_target = 700000
spares_target = 150000
total_target = tm_service_target + s_job_target + spares_target # $2.50M

# TALENT SETTINGS
g_base = 75000
r_base = 130000
bill_rate = 210
utilization_pct = 75

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.header("🖼️ Chart Dimensions")
    st.info("Adjust these to fit your slide.")
    c_width = st.slider("Chart Width (Inches)", 4, 15, 8) 
    c_height = st.slider("Chart Height (Inches)", 3, 10, 5)

# ==========================================
# CHART 1: REVENUE BRIDGE (WATERFALL)
# ==========================================
st.header("Slide 1: The 'Revenue Bridge' (Waterfall)")
st.caption(f"Bridge from 2025 Actuals (${act_total_rev/1e6:.2f}M) to 2026 Target (${total_target/1e6:.2f}M)")

# Calculate Deltas
service_2025 = act_rev_labor + act_rev_parts
delta_service = tm_service_target - service_2025 # Growth
delta_sjob = s_job_target - act_rev_sjob         # Shrinkage
delta_spares = spares_target - act_rev_spares    # Growth

wf_data = {
    'Category': ['2025 Actuals', 'Service Growth', 'S-Job Adjustment', 'Parts/Spares', '2026 Target'],
    'Value': [act_total_rev, delta_service, delta_sjob, delta_spares, 0.0],
    'Type': ['Base', 'Add', 'Add', 'Add', 'Total']
}
df_wf = pd.DataFrame(wf_data)

# Logic for Total Bar
df_wf['cumsum'] = df_wf['Value'].cumsum()
df_wf.loc[4, 'Value'] = total_target 

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
        # Growth Bar (Green), Shrink Bar (Red)
        color = '#4caf50' if val >= 0 else '#d32f2f' 
        ax1.bar(cat, val, bottom=bottom if val >= 0 else bottom + val, color=color, edgecolor='black', width=0.6)
        bottom += val

ax1.set_ylabel('Revenue ($)')
ax1.set_title('Growth Bridge: 2025 to 2026')
ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax1.axhline(0, color='black', linewidth=1)
ax1.grid(axis='y', linestyle='--', alpha=0.5)

# Value Labels
for p in ax1.patches:
    width, height = p.get_width(), p.get_height()
    x, y = p.get_xy()
    if abs(height) > 0:
        # Format label (M or k)
        val = height
        if val > 1000000: lbl = f'${val/1e6:.2f}M'
        else: lbl = f'${val/1e3:.0f}k'
        
        # Position adjustments for negative bars
        pos_y = y + height/2
        ax1.text(x+width/2, pos_y, lbl, ha='center', va='center', color='white', fontweight='bold', fontsize=10)

st.pyplot(fig1)

st.divider()

# ==========================================
# CHART 2: THE CASH FLOW J-CURVE
# ==========================================
st.header("Slide 2: The 'Training Trap' (J-Curve)")
st.caption("Cumulative Cash Flow: Green ($75k) vs. Rebadge ($130k) over Year 1.")

months = list(range(1, 13))
# Monthly Rev Capacity @ 75% Util
monthly_rev_cap = (2080 * bill_rate * (utilization_pct/100)) / 12 

# GREEN
green_monthly_cost = (g_base * 1.11 + 23000) / 12
green_cf = []
cum_g = 0
for m in months:
    ramp = min(m/12, 1.0) # 12 month ramp
    cash = (monthly_rev_cap * ramp) - green_monthly_cost
    cum_g += cash
    green_cf.append(cum_g)

# REBADGE
reb_monthly_cost = (r_base * 1.11 + 23000) / 12
reb_cf = []
cum_r = 0
for m in months:
    ramp = min(m/1, 1.0) # 1 month ramp
    cash = (monthly_rev_cap * ramp) - reb_monthly_cost
    cum_r += cash
    reb_cf.append(cum_r)

fig2, ax2 = plt.subplots(figsize=(c_width, c_height))
ax2.plot(months, green_cf, label='Green Tech', color='#f44336', linewidth=3, linestyle='--')
ax2.plot(months, reb_cf, label='Rebadge Tech', color='#4caf50', linewidth=4)
ax2.axhline(0, color='black', linewidth=1)

# Annotate the trap
min_val = min(green_cf)
min_idx = green_cf.index(min_val)
ax2.annotate('Cash Hole', xy=(min_idx+1, min_val), xytext=(min_idx+1, min_val-20000),
             arrowprops=dict(facecolor='red', shrink=0.05), color='red', ha='center', fontweight='bold')

ax2.set_ylabel('Cumulative Cash Contribution ($)')
ax2.set_xlabel('Months after Hire')
ax2.set_title('Time to ROI: Green vs. Rebadge')
ax2.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax2.legend()
ax2.grid(True, alpha=0.3)
st.pyplot(fig2)

st.divider()

# ==========================================
# CHART 3: THE CSP MARGIN STEP
# ==========================================
st.header("Slide 3: The Margin Step-Up")
st.caption("Visualizing the instant impact of CSP Status on Parts Profitability.")

fig3, ax3 = plt.subplots(figsize=(c_width, c_height))
margin_months = list(range(1, 13))
margin_vals = [10 if m < 6 else 30 for m in margin_months] # Jump to 30%
ax3.step(margin_months, margin_vals, where='post', linewidth=4, color='#9c27b0')
ax3.fill_between(margin_months, margin_vals, step="post", alpha=0.2, color='#9c27b0')
ax3.set_ylim(0, 35)
ax3.set_ylabel('Parts Gross Margin %')
ax3.set_xlabel('FY26 Month')
ax3.set_title('Impact of Fanuc CSP Certification')
ax3.yaxis.set_major_formatter(mtick.PercentFormatter(100))
ax3.annotate('CSP Activation\n(Margin 3x)', xy=(6, 30), xytext=(3, 32),
             arrowprops=dict(facecolor='black', shrink=0.05), fontsize=10, fontweight='bold')
st.pyplot(fig3)

st.divider()

# ==========================================
# CHART 4: REVENUE MOMENTUM (STACKED AREA)
# ==========================================
st.header("Slide 4: FY26 Momentum (Stacked Area)")
st.caption("Quarterly Revenue Run-Rate summing to $2.5M Target.")

quarters = ['Q1', 'Q2', 'Q3', 'Q4']

# Distribute to sum to Targets
# Service ($1.65M) -> Ramping up
q_serv = [380000, 400000, 420000, 450000] 
# S-Jobs ($700k) -> Stable/Lumpy
q_sjob = [150000, 200000, 150000, 200000]
# Spares ($150k) -> Flat
q_spar = [35000, 35000, 40000, 40000]

fig4, ax4 = plt.subplots(figsize=(c_width, c_height))
ax4.stackplot(quarters, q_serv, q_sjob, q_spar, 
              labels=['Service (Labor+Parts)', 'S-Projects', 'Spare Parts'],
              colors=['#1565c0', '#ffb74d', '#81c784'], alpha=0.9)

ax4.set_ylabel('Quarterly Revenue ($)')
ax4.set_title('2026 Revenue Composition Plan')
ax4.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax4.legend(loc='upper left', fontsize='small')
ax4.grid(axis='y', linestyle='--', alpha=0.3)
st.pyplot(fig4)
