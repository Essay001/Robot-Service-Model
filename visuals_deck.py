import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

st.set_page_config(page_title="Executive Visuals Deck", layout="wide")

st.title("📸 Presentation Visuals Generator")
st.markdown("Use the **sidebar sliders** to adjust the chart size for your PowerPoint slides.")

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.header("🖼️ Chart Dimensions")
    st.info("Adjust these to fit your slide.")
    # Default set to (6, 4) which is standard for PPT
    c_width = st.slider("Chart Width (Inches)", 4, 15, 6) 
    c_height = st.slider("Chart Height (Inches)", 3, 10, 4)

# ==========================================
# CHART 1: REVENUE BRIDGE (WATERFALL)
# ==========================================
st.header("Slide 1: The 'Revenue Bridge' (Waterfall)")
st.caption("Explaining how we get from FY25 to the FY26 Target.")

# Data for Waterfall
wf_data = {
    'Category': ['FY25 Baseline', '+ Rebadge Labor', '+ Parts Growth', '+ CSP Margin Impact', '+ S-Job Optimization', 'FY26 Target'],
    'Value': [1.5, 0.85, 0.05, 0.08, 0.12, 0.0], # Values in Millions
    'Type': ['Base', 'Add', 'Add', 'Add', 'Add', 'Total']
}
df_wf = pd.DataFrame(wf_data)

# Calculate Start/End points for bars
df_wf['cumsum'] = df_wf['Value'].cumsum()
df_wf.loc[df_wf.index[-1], 'Value'] = df_wf.loc[df_wf.index[-2], 'cumsum'] # Set Total
df_wf.loc[df_wf.index[-1], 'cumsum'] = df_wf.loc[df_wf.index[-1], 'Value']

# Plotting - Uses Sidebar Dimensions
fig1, ax1 = plt.subplots(figsize=(c_width, c_height))
bottom = 0
colors = []

for i, row in df_wf.iterrows():
    if row['Type'] == 'Base' or row['Type'] == 'Total':
        ax1.bar(row['Category'], row['Value'], color='#2196f3', edgecolor='black')
        bottom = row['Value']
    else:
        ax1.bar(row['Category'], row['Value'], bottom=bottom, color='#4caf50', edgecolor='black')
        bottom += row['Value']

# Labels and Formatting
ax1.set_ylabel('Revenue ($ Millions)')
ax1.set_title('FY26 Revenue Bridge: Building the Target')
ax1.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:.1f}M'))
plt.xticks(rotation=45, ha='right') # Angled text for better fit
ax1.grid(axis='y', linestyle='--', alpha=0.5)

st.pyplot(fig1)

st.divider()

# ==========================================
# CHART 2: THE CASH FLOW J-CURVE
# ==========================================
st.header("Slide 2: The 'Training Trap' (J-Curve)")
st.caption("Cumulative Cash Flow: Rebadge (Expert) vs. Green (Trainee) over Year 1.")

# Simulation Data
months = list(range(1, 13))

# Green Tech: Cost $7.5k/mo ($90k/yr). Rev ramps from 0 to $28k/mo over 9 months.
green_cost = [7500] * 12
green_rev = []
for m in months:
    ramp = min(m/9, 1.0)
    green_rev.append(28000 * ramp)
green_cash = np.array(green_rev) - np.array(green_cost)
green_cum = np.cumsum(green_cash)

# Rebadge Tech: Cost $14k/mo ($170k/yr). Rev is $37k/mo immediately.
reb_cost = [14000] * 12
reb_rev = [37500] * 12 # Flat, immediate
reb_cash = np.array(reb_rev) - np.array(reb_cost)
reb_cum = np.cumsum(reb_cash)

fig2, ax2 = plt.subplots(figsize=(c_width, c_height))

# Plot Lines
ax2.plot(months, green_cum, label='Green Tech (Junior)', color='#f44336', linewidth=3, linestyle='--')
ax2.plot(months, reb_cum, label='Rebadge Tech (Expert)', color='#4caf50', linewidth=4)

# Zero Line
ax2.axhline(0, color='black', linewidth=1)

# Annotations (Adjusted position for smaller chart)
ax2.annotate('Training Trap\n(Negative Cash)', xy=(4, -15000), xytext=(4, -90000),
             arrowprops=dict(facecolor='red', shrink=0.05), color='red', ha='center', fontsize=9)

ax2.set_ylabel('Cumulative Cash Generated ($)')
ax2.set_xlabel('Months in FY26')
ax2.set_title('Cumulative Cash Flow Impact (Per Hire)')
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
margin_vals = [10 if m < 6 else 25 for m in margin_months] # Step at month 6

ax3.step(margin_months, margin_vals, where='post', linewidth=4, color='#9c27b0')
ax3.fill_between(margin_months, margin_vals, step="post", alpha=0.2, color='#9c27b0')

# Labels
ax3.set_ylim(0, 35)
ax3.set_ylabel('Parts Gross Margin %')
ax3.set_xlabel('FY26 Month')
ax3.set_title('Impact of Fanuc CSP Certification')
ax3.yaxis.set_major_formatter(mtick.PercentFormatter(100))

# Annotation
ax3.annotate('CSP Activation\n(Profit +150%)', xy=(6, 25), xytext=(3, 30),
             arrowprops=dict(facecolor='black', shrink=0.05), fontsize=10, fontweight='bold')

st.pyplot(fig3)

st.divider()

# ==========================================
# CHART 4: REVENUE MOMENTUM (STACKED AREA)
# ==========================================
st.header("Slide 4: FY26 Momentum (Stacked Area)")
st.caption("Quarterly Revenue Run-Rate by Source.")

# Mock Quarterly Data
quarters = ['Q1', 'Q2', 'Q3', 'Q4']
base = [350000, 355000, 360000, 365000] # Steady Base
parts = [30000, 35000, 55000, 60000] # CSP kicks in Q3
labor = [110000, 115000, 220000, 230000] # Hire 1 in Q1, Hire 2 in Q3
sjobs = [40000, 50000, 70000, 90000] # Growing S-Jobs

fig4, ax4 = plt.subplots(figsize=(c_width, c_height))

ax4.stackplot(quarters, base, parts, labor, sjobs, 
              labels=['Base Break/Fix', 'Spare Parts (CSP)', 'Rebadge Labor', 'S-Projects'],
              colors=['#bdbdbd', '#e1bee7', '#ff9800', '#2196f3'], alpha=0.8)

ax4.set_ylabel('Quarterly Revenue ($)')
ax4.set_title('FY26 Revenue Composition & Growth')
ax4.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
ax4.legend(loc='upper left', fontsize='small')
ax4.grid(axis='y', linestyle='--', alpha=0.3)

st.pyplot(fig4)
