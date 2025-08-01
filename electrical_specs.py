import streamlit as st
import math
import pandas as pd

# Australian Standards Configuration
VOLTAGE = {
    "AC": {7: 230, 22: 400},
    "DC": {25: 500, 50: 500, 75: 500, 100: 500, 120: 500, 150: 500, 300: 750, 350: 750}
}

# Extended standard breaker sizes for large DC chargers
STANDARD_BREAKERS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 
                     250, 315, 400, 500, 630, 800, 1000, 1200, 1600, 2000]

# Cable current capacity (AS/NZS 3008:2017) - PVC insulated copper conductors
CABLE_CAPACITY = {
    "1C": {1.5: 17.5, 2.5: 23, 4: 30, 6: 39, 10: 53, 16: 70, 25: 92, 35: 115, 
           50: 142, 70: 179, 95: 217, 120: 254, 150: 292, 185: 336, 240: 392, 
           300: 451, 400: 527, 500: 600, 630: 696},
    "2C": {1.5: 15, 2.5: 20, 4: 26, 6: 34, 10: 46, 16: 61, 25: 80, 35: 99, 
           50: 123, 70: 155, 95: 189, 120: 221, 150: 255, 185: 292, 240: 352, 
           300: 409, 400: 489, 500: 569, 630: 674},
    "3C": {1.5: 13.5, 2.5: 17.5, 4: 23, 6: 30, 10: 40, 16: 53, 25: 70, 35: 87, 
           50: 108, 70: 136, 95: 166, 120: 194, 150: 225, 185: 260, 240: 310, 
           300: 360, 400: 429, 500: 495, 630: 588},
    "4C": {1.5: 12, 2.5: 16, 4: 21, 6: 27, 10: 37, 16: 49, 25: 64, 35: 80, 
           50: 99, 70: 125, 95: 152, 120: 178, 150: 207, 185: 240, 240: 287, 
           300: 334, 400: 400, 500: 464, 630: 555}
}

# Common Australian MSB configurations (AS/NZS 3439)
MSB_CONFIGS = [
    {"Amps": 100, "Dimensions (mm)": "300x200x150", "Busbar (A)": 100},
    {"Amps": 200, "Dimensions (mm)": "400x250x200", "Busbar (A)": 200},
    {"Amps": 400, "Dimensions (mm)": "600x300x250", "Busbar (A)": 400},
    {"Amps": 600, "Dimensions (mm)": "800x400x300", "Busbar (A)": 600},
    {"Amps": 800, "Dimensions (mm)": "1000x500x350", "Busbar (A)": 800},
    {"Amps": 1000, "Dimensions (mm)": "1200x600x400", "Busbar (A)": 1000},
    {"Amps": 1200, "Dimensions (mm)": "1500x700x450", "Busbar (A)": 1200},
    {"Amps": 1600, "Dimensions (mm)": "1800x800x500", "Busbar (A)": 1600},
    {"Amps": 2000, "Dimensions (mm)": "2000x1000x600", "Busbar (A)": 2000},
    {"Amps": 2500, "Dimensions (mm)": "2200x1200x700", "Busbar (A)": 2500},
    {"Amps": 3000, "Dimensions (mm)": "2500x1500x800", "Busbar (A)": 3000}
]

# Function to calculate electrical requirements
def calculate_requirements(charger_type, capacity, quantity):
    # Determine configuration
    if charger_type == "AC":
        if capacity == 7:  # Single-phase
            voltage = VOLTAGE["AC"][7]
            phase = "Single"
            cores = "2C"  # Active + Neutral
            current = (capacity * 1000) / voltage
        else:  # 22 kW - Three-phase
            voltage = VOLTAGE["AC"][22]
            phase = "Three"
            cores = "4C"  # 3 Phase + Neutral
            current = (capacity * 1000) / (voltage * math.sqrt(3))
            
        # For MSB calculations, AC chargers use AC current directly
        ac_current = current
        
    else:  # DC
        voltage = VOLTAGE["DC"][capacity]
        phase = "DC"
        cores = "2C"  # Positive + Negative
        current = (capacity * 1000) / voltage
        
        # For MSB calculations, convert DC power to AC input
        # Assumptions: 95% efficiency, 0.95 power factor
        ac_power = capacity / (0.95 * 0.95)
        ac_current = (ac_power * 1000) / (400 * math.sqrt(3))  # 400V 3-phase input
    
    # Apply 125% safety factor for continuous loads (AS/NZS 3000)
    derated_current = current * 1.25
    derated_ac_current = ac_current * 1.25
    
    # Find appropriate breaker size
    breaker_size = next((b for b in STANDARD_BREAKERS if b >= derated_current), None)
    
    if not breaker_size:
        return None
    
    # Determine cable size
    cable_type = cores
    cable_size = None
    cable_capacity = 0
    
    # Find smallest cable that can handle the breaker size
    for size, ampacity in sorted(CABLE_CAPACITY[cable_type].items()):
        if ampacity >= breaker_size:
            cable_size = size
            cable_capacity = ampacity
            break
    
    if not cable_size:
        return None
    
    # Determine breaker specs
    if charger_type == "AC":
        if capacity == 7:
            breaker_spec = f"AS/NZS 60898, C-curve, {breaker_size}A, 240V AC, 1P"
        else:
            breaker_spec = f"AS/NZS 60898, C-curve, {breaker_size}A, 415V AC, 3P"
    else:
        breaker_spec = f"AS/NZS 60947.2, {breaker_size}A, {voltage}V DC"
    
    return {
        "Voltage (V)": voltage,
        "Phase": phase,
        "Full Load Current (A)": round(current, 1),
        "Derated Current (A)": round(derated_current, 1),
        "AC Input Current (A)": round(ac_current, 1) if charger_type == "DC" else round(current, 1),
        "Derated AC Current (A)": round(derated_ac_current, 1) if charger_type == "DC" else round(derated_current, 1),
        "Breaker Size (A)": breaker_size,
        "Breaker Specs": breaker_spec,
        "Cable Size": f"{cable_size} mm²",
        "Cable Type": f"{cable_type} PVC/XLPE Cu",
        "Cable Capacity (A)": cable_capacity,
        "Cable Configuration": cores,
        "Power (kW)": capacity,
        "Charger Type": charger_type
    }

# Function to calculate MSB requirements
def calculate_msb(chargers):
    total_derated_ac_current = 0
    total_power = 0
    
    for charger in chargers:
        # For MSB calculation, use derated AC current
        # For DC chargers, this is the AC input current after derating
        # For AC chargers, it's the derated AC current
        current_per_charger = charger["Derated AC Current (A)"]
        total_derated_ac_current += current_per_charger * charger["Quantity"]
        total_power += charger["Power (kW)"] * charger["Quantity"]
    
    # Apply diversity factor (AS/NZS 3000 Clause 2.2)
    # For EV chargers, diversity is typically 0.8-1.0 (conservative 0.9)
    diversity_factor = 0.9
    diversified_current = total_derated_ac_current * diversity_factor
    
    # Find appropriate main breaker size
    main_breaker = next((b for b in STANDARD_BREAKERS if b >= diversified_current), None)
    
    if not main_breaker:
        return None
    
    # Find suitable MSB configuration
    msb_config = next((msb for msb in MSB_CONFIGS if msb["Busbar (A)"] >= diversified_current), None)
    
    if not msb_config:
        return None
    
    # Calculate busbar size (based on derated current)
    busbar_size = math.ceil(diversified_current / 100) * 100
    
    return {
        "Total Connected Load (kW)": round(total_power, 1),
        "Total Derated AC Current (A)": round(total_derated_ac_current, 1),
        "Diversification Factor": diversity_factor,
        "Diversified Current (A)": round(diversified_current, 1),
        "Main Breaker Size (A)": main_breaker,
        "Recommended MSB Size (A)": msb_config["Amps"],
        "Busbar Rating (A)": busbar_size,
        "MSB Dimensions": msb_config["Dimensions (mm)"],
        "MSB Configuration": f"{msb_config['Amps']}A Main Switchboard"
    }

# Streamlit UI
st.title("⚡ EV Charger & MSB Calculator")
st.subheader("Australian Market - AS/NZS Standards")

# Initialize session state for chargers
if 'chargers' not in st.session_state:
    st.session_state.chargers = []

# Charger input section
st.header("Add Chargers")
col1, col2, col3, col4 = st.columns([2,2,2,1])
with col1:
    charger_type = st.radio("Charger Type", ["AC", "DC"], key="type")
with col2:
    if charger_type == "AC":
        capacity = st.selectbox("Capacity (kW)", [7, 22], key="capacity")
    else:
        capacity = st.selectbox("Capacity (kW)", [25, 50, 75, 100, 120, 150, 300, 350], key="capacity")
with col3:
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1, key="qty")
with col4:
    st.write("")
    st.write("")
    if st.button("Add Charger", key="add"):
        result = calculate_requirements(charger_type, capacity, quantity)
        if result:
            st.session_state.chargers.append({
                "Type": charger_type,
                "Capacity (kW)": capacity,
                "Quantity": quantity,
                **result
            })
        else:
            st.error("Could not calculate for this configuration. Check parameters.")

# Display added chargers
if st.session_state.chargers:
    st.subheader("Configured Chargers")
    
    # Create simplified display table
    display_data = []
    for idx, charger in enumerate(st.session_state.chargers):
        display_data.append({
            "Charger": f"Charger {idx+1}",
            "Type": charger["Type"],
            "Capacity (kW)": charger["Capacity (kW)"],
            "Qty": charger["Quantity"],
            "Breaker (A)": charger["Breaker Size (A)"],
            "Cable": charger["Cable Size"]
        })
    
    st.dataframe(pd.DataFrame(display_data))
    
    # Add clear button
    if st.button("Clear All Chargers"):
        st.session_state.chargers = []
        st.experimental_rerun()

# Calculate MSB requirements
if st.session_state.chargers:
    st.header("Main Switchboard (MSB) Requirements")
    msb_result = calculate_msb(st.session_state.chargers)
    
    if msb_result:
        # Display MSB specs
        st.subheader("MSB Specifications")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Connected Load", f"{msb_result['Total Connected Load (kW)']} kW")
            st.metric("Total Derated AC Current", f"{msb_result['Total Derated AC Current (A)']} A")
            st.metric("Diversified Current", f"{msb_result['Diversified Current (A)']} A")
        
        with col2:
            st.metric("Main Breaker Size", f"{msb_result['Main Breaker Size (A)']} A")
            st.metric("Recommended MSB", f"{msb_result['Recommended MSB Size (A)']}A")
            st.metric("Busbar Rating", f"{msb_result['Busbar Rating (A)']}A")
        
        st.write(f"**MSB Dimensions:** {msb_result['MSB Dimensions']}")
        st.write(f"**MSB Configuration:** {msb_result['MSB Configuration']}")
        
        # Display technical notes
        st.subheader("Technical Notes (AS/NZS Standards):")
        st.write("- **Safety Factor:** 125% for continuous loads (AS/NZS 3000 Clause 2.5.7.2)")
        st.write("- **Diversity Factor:** 0.9 applied (AS/NZS 3000 Clause 2.2)")
        st.write("- **DC Charger AC Input:** Calculated with 95% efficiency and 0.95 power factor")
        st.write("- **MSB Standards:** AS/NZS 3439 for low-voltage switchgear assemblies")
        st.write("- **Busbar Rating:** Based on 1A/mm² current density for copper busbars")
    else:
        st.error("MSB calculation failed. Total load may exceed standard configurations. Consider:")
        st.write("- Using higher voltage systems")
        st.write("- Splitting load across multiple MSBs")
        st.write("- Consulting a specialist for custom solutions")

# Australian Market Considerations
st.markdown("---")
st.subheader("Australian Market Specifications")
st.write("""
**Main Switchboards (AS/NZS 3439):**
- Standard configurations: 100A, 200A, 400A, 600A, 800A, 1000A, 1200A, 1600A, 2000A, 2500A, 3000A
- Dimensions: 400x250x200mm (200A) to 2500x1500x800mm (3000A)
- Busbar material: Copper (1A/mm² current density)
- IP rating: IP2X or IP4X for indoor installations

**High-Power DC Charger Considerations:**
- 100kW+ chargers require 3-phase 400V AC input
- Typical efficiency: 92-96% (95% assumed)
- Power factor: 0.95-0.99 (0.95 assumed)
- AC input current = (DC Power / (Efficiency × Power Factor)) / (√3 × AC Voltage)
- 100kW DC charger ≈ 152A AC input at 400V (before derating)

**Cable Sizing (AS/NZS 3008:2017):**
- V-90 (XLPE) or V-75 (PVC) insulated cables
- Reference Method C (enclosed in conduit on a wall)
- Ambient temperature: 40°C
- Maximum conductor temperature: 75°C (PVC), 90°C (XLPE)

**Protection Devices:**
- AC chargers: RCD protection required (Type A or B per AS/NZS 3000:2018)
- DC chargers: Specialized DC protection (AS/NZS 60947.2)
- Main breaker: AS/NZS 60898 or AS/NZS 60947.2

**Installation Requirements:**
- Compliance with AS/NZS 3000 Wiring Rules
- AS/NZS 3000:2018 Section 7.9 for EV charging installations
- Isolation and emergency stop provisions
- Load management systems for multiple chargers
""")

# Footer
st.markdown("---")
st.caption("**Disclaimer:** This calculator provides estimates based on Australian Standards. "
           "Actual installations must be designed by a qualified electrician considering site-specific conditions, "
           "voltage drop calculations, and local regulations. Always verify with current AS/NZS standards documents.")