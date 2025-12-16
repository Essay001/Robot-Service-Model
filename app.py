import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

st.set_page_config(page_title="Strategic Exit Model (Updated)", layout="wide")

st.title(" 🚀 Strategic Exit Model: The 5-Year P&L")
st.markdown("Forecasting the path to a **$7.5M Exit** using precise burden logic.")

# ==========================================
# SIDEBAR - INPUTS
# ==========================================
with st.sidebar:
    st.header("1. Current State (2025)")
    current_rev = st.number_input("Current Revenue ($)", value=1500000, step=100000)
    current_ebitda = st.number_input("Current EBITDA ($)", value=225000, step=10000)
    
    st.divider()
    
    st.header("2. Growth Assumptions")
    organic_growth = st.slider("Organic Growth %", 5, 30, 15)
    
    st.divider()
    
    st.header("3. Labor & Burden (New!)")
    st.info("Cost = Base + 11% Tax + $23k Ins.")
    
    # Tech Inputs
    tech_base_salary = st.number_input("Avg Tech Base Salary ($)", value=90000, step=5000)
    tech_count_start = st.number_input("Starting Tech Count", value=6)
    hires_per_year = st.slider("Net New Techs / Year", 1, 5, 2)
    
    # Engineer Inputs
    engineer_base = st.number_input("Central Engineer Base ($)", value=130000)
    engineer_trigger = st.number_input("S-Job Rev Trigger ($)", value=1200000)
    
    st.divider()
    
    st.header("4. Acquisition (Optional)")
    acq_year = st.selectbox("Acquisition Year", ["None", "2026", "2027", "2028"])
    acq_rev = st.number_input("Target Revenue ($)", value=1500000)
    acq_margin = st.slider("Target EBITDA Margin %", 5, 30, 15)

# ==========================================
# BURDEN CALCULATOR FUNCTION
# ==========================================
def calculate_burdened_cost(base_salary):
    # Formula: Base + (Base * 11%) + $23,000 Health/Ins
    return base_salary + (base_salary * 0.11) + 23000

# ==========================================
# CALCULATION ENGINE
# ==========================================
years = [2025, 2026, 2027, 2028, 2029]
data = []

# Initialize
rev = current_rev
ebitda = current_ebitda
tech_count = tech_count_start
engineer_hired = False

for year in years:
    # 1. Revenue Growth
    if year > 2025:
        rev = rev * (1 + (organic_growth/100))
        
    # 2. Acquisition Bump
    acq_impact = 0
    acq_ebitda_impact = 0
    if str(year) == acq_year:
        acq_impact = acq_rev
        rev += acq_impact
        # Acquired EBITDA
        acq_ebitda_impact = acq_rev * (acq_margin/100)
        
    # 3. Cost Calculations
    # Update Headcount
    if year > 2025:
        tech_count += hires_per_year
        
    # Tech Labor Cost (Burdened)
    tech_burdened = calculate_burdened_cost(tech_base_salary)
    total_tech_cost = tech_count * tech_burdened
    
    # Central Engineer Logic
    # Assume S-Jobs are ~25% of total revenue for trigger check
    s_job_proxy = rev * 0.25
    eng_cost = 0
    if s_job_proxy >= engineer_trigger or engineer_hired:
        engineer_hired = True
        eng_cost = calculate_burdened_cost(engineer_base)
    
    # 4. Gross Margin & Overhead (Simplified Model)
    # Assume Material/Other COGS is 20% of Revenue
    cogs_materials = rev * 0.20
    # Gross Profit
    gp = rev - cogs_materials - total_tech_cost - eng_cost
    
    # SG&A (Overhead) - grows slowly
    # Base overhead estimate derived from 2025 start
    if year == 2025:
        # Back into overhead: Rev - COGS - Labor - EBITDA = Overhead
        overhead = rev - cogs_materials - total_tech_cost - eng_cost - current_ebitda
    else:
        overhead = overhead * 1.05 # 5% inflation
        
    # 5. EBITDA
    # If acquisition happened, we add its EBITDA directly, assuming integration
    operating_ebitda = gp - overhead
    if str(year) == acq_year:
        # In transition year, maybe we pay integration costs?
        pass 
        
    final_ebitda = operating_ebitda # + acq_ebitda_impact is implicit in Revenue growth if we modeled it fully detailed
    
    # RE-CALC ADJUSTMENT: For this simple view, let's stick to Margin % logic for the core, 
    # but specific logic for the new Labor Burden.
    
    # Let's force the EBITDA to respect the new Labor costs
    final_ebitda = rev - cogs_materials - total_tech_cost - eng_cost - overhead
    
    data.append({
        "Year": year,
        "Revenue": rev,
        "EBITDA": final_ebitda,
        "Tech_Count": tech_count,
        "Eng_Hired": "Yes" if engineer_hired else "No",
        "Tech_Cost_Total": total_tech_cost
    })

df = pd.DataFrame(data)

# ==========================================
# DASHBOARD
# ==========================================
c1, c2, c3 = st.columns(3)
exit_ebitda = df.iloc[-1]['EBITDA']
exit_val = exit_ebitda * 6.5 # Multiple

with c1:
    st.metric("2029 Revenue", f"${df.iloc[-1]['Revenue']/1000000:.1f}M")
with c2:
    st.metric("2029 EBITDA", f"${exit_ebitda/1000000:.1f}M")
with c3:
    st.metric("Est. Exit Value (6.5x)", f"${exit_val/1000000:.1f}M")

st.divider()

st.subheader("Financial Forecast")
st.dataframe(df.style.format({"Revenue": "${:,.0f}", "EBITDA": "${:,.0f}", "Tech_Cost_Total": "${:,.0f}"}))

st.caption(f"**Burden Logic Used:** Base + 11% Tax + $23k Insurance.")
st.caption(f"Example Tech: ${tech_base_salary:,.0f} Base -> **${calculate_burdened_cost(tech_base_salary):,.0f} Burdened**")
