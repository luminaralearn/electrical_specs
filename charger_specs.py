import streamlit as st
import math
import pandas as pd
import graphviz
from datetime import datetime

# Initialize session state
def initialize_session_state():
    if 'chargers' not in st.session_state:
        st.session_state.chargers = []
    if 'design_date' not in st.session_state:
        st.session_state.design_date = datetime.now().strftime("%Y-%m-%d")
    if 'calculation_params' not in st.session_state:
        st.session_state.calculation_params = {
            'safety_factor': 1.25,
            'diversity_factor': 0.9,
            'dc_efficiency': 0.95,
            'power_factor': 0.95,
            'ac_voltage': 400,
            'dc_voltage': 500
        }

# Australian Standards Configuration
STANDARD_BREAKERS = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 
                     250, 315, 400, 500, 630, 800, 1000, 1200, 1600, 2000]

# Cable current capacity (AS/NZS 3008:2017)
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

# Common Australian MSB configurations
MSB_CONFIGS = [
    {"Amps": 100, "Dimensions": "300x200x150", "Busbar": 100},
    {"Amps": 200, "Dimensions": "400x250x200", "Busbar": 200},
    {"Amps": 400, "Dimensions": "600x300x250", "Busbar": 400},
    {"Amps": 600, "Dimensions": "800x400x300", "Busbar": 600},
    {"Amps": 800, "Dimensions": "1000x500x350", "Busbar": 800},
    {"Amps": 1000, "Dimensions": "1200x600x400", "Busbar": 1000},
    {"Amps": 1200, "Dimensions": "1500x700x450", "Busbar": 1200},
    {"Amps": 1600, "Dimensions": "1800x800x500", "Busbar": 1600},
    {"Amps": 2000, "Dimensions": "2000x1000x600", "Busbar": 2000},
    {"Amps": 2500, "Dimensions": "2200x1200x700", "Busbar": 2500},
    {"Amps": 3000, "Dimensions": "2500x1500x800", "Busbar": 3000}
]

def calculate_requirements(charger_type, capacity, quantity, params):
    if charger_type == "AC":
        if capacity == 7:  # Single-phase
            voltage = 230
            phase = "Single"
            cores = "2C"
            current = (capacity * 1000) / voltage
        else:  # Three-phase
            voltage = params['ac_voltage']
            phase = "Three"
            cores = "4C"
            current = (capacity * 1000) / (voltage * math.sqrt(3))
        ac_current = current
    else:  # DC
        voltage = params['dc_voltage']
        phase = "DC"
        cores = "2C"
        current = (capacity * 1000) / voltage
        ac_power = capacity / (params['dc_efficiency'] * params['power_factor'])
        ac_current = (ac_power * 1000) / (params['ac_voltage'] * math.sqrt(3))

    derated_current = current * params['safety_factor']
    derated_ac_current = ac_current * params['safety_factor']
    
    breaker_size = next((b for b in STANDARD_BREAKERS if b >= derated_current), None)
    if not breaker_size:
        return None

    cable_size = next((size for size, ampacity in sorted(CABLE_CAPACITY[cores].items()) 
                     if ampacity >= breaker_size), None)
    if not cable_size:
        return None

    if charger_type == "AC":
        if capacity == 7:
            breaker_spec = f"AS/NZS 60898, C-curve, {breaker_size}A, 240V AC, 1P"
        else:
            breaker_spec = f"AS/NZS 60898, C-curve, {breaker_size}A, {params['ac_voltage']}V AC, 3P"
    else:
        breaker_spec = f"AS/NZS 60947.2, {breaker_size}A, {voltage}V DC"

    return {
        "Voltage (V)": voltage,
        "Phase": phase,
        "Full Load Current (A)": round(current, 1),
        "Derated Current (A)": round(derated_current, 1),
        "AC Input Current (A)": round(ac_current, 1),
        "Derated AC Current (A)": round(derated_ac_current, 1),
        "Breaker Size (A)": breaker_size,
        "Breaker Specs": breaker_spec,
        "Cable Size (mm²)": cable_size,
        "Cable Type": f"{cores} PVC/XLPE Cu",
        "Cable Capacity (A)": CABLE_CAPACITY[cores][cable_size],
        "Cable Configuration": cores,
        "Power (kW)": capacity,
        "Charger Type": charger_type
    }

def calculate_msb(chargers, params):
    total_derated_ac_current = sum(
        charger["Derated AC Current (A)"] * charger["Quantity"] 
        for charger in chargers
    )
    total_power = sum(charger["Power (kW)"] * charger["Quantity"] for charger in chargers)
    
    diversified_current = total_derated_ac_current * params['diversity_factor']
    
    main_breaker = next((b for b in STANDARD_BREAKERS if b >= diversified_current), None)
    if not main_breaker:
        return None

    msb_config = next((msb for msb in MSB_CONFIGS if msb["Busbar"] >= diversified_current), None)
    if not msb_config:
        return None

    busbar_size = math.ceil(diversified_current / 100) * 100
    
    return {
        "Total Connected Load (kW)": round(total_power, 1),
        "Total Derated AC Current (A)": round(total_derated_ac_current, 1),
        "Diversification Factor": params['diversity_factor'],
        "Diversified Current (A)": round(diversified_current, 1),
        "Main Breaker Size (A)": main_breaker,
        "Recommended MSB Size (A)": msb_config["Amps"],
        "Busbar Rating (A)": busbar_size,
        "MSB Dimensions": msb_config["Dimensions"],
        "MSB Configuration": f"{msb_config['Amps']}A Main Switchboard"
    }

def generate_sld(chargers, msb_result, params):
    # Create the graph
    dot = graphviz.Digraph('EV_Charger_SLD', format='png')
    dot.attr(rankdir='LR', size='12,8', 
             fontname='Arial', fontsize='10',
             labelloc='t', label='EV CHARGER SINGLE LINE DIAGRAM\n(AS/NZS 3000 COMPLIANT)')
    
    # 1. Calculate transformer rating (AS/NZS 60076 compliant)
    total_kva = msb_result["Total Connected Load (kW)"] / params['power_factor']
    trafo_rating = max(math.ceil(total_kva / 100) * 100, 500)  # Minimum 500kVA for EV installations
    
    # 2. Transformer Node
    trafo_label = f'''<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">
        <TR><TD COLSPAN="2" BGCOLOR="#f0f0f0"><B>DISTRIBUTION TRANSFORMER</B></TD></TR>
        <TR><TD>Rating</TD><TD>{trafo_rating}kVA</TD></TR>
        <TR><TD>Voltage</TD><TD>11kV/415V ±5%</TD></TR>
        <TR><TD>Impedance</TD><TD>6% (AS/NZS 60076)</TD></TR>
        <TR><TD>Vector Group</TD><TD>Dyn11</TD></TR>
    </TABLE>>'''
    dot.node('TR', trafo_label, shape='plaintext')
    
    # 3. EV Distribution Board (AS/NZS 3439.1 compliant)
    evdb_label = f'''<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">
        <TR><TD COLSPAN="2" BGCOLOR="#f0f0f0"><B>EV DISTRIBUTION BOARD</B></TD></TR>
        <TR><TD>Incomer</TD><TD>{msb_result["Main Breaker Size (A)"]}A, 65kA SCCR</TD></TR>
        <TR><TD>Busbar</TD><TD>{msb_result["Busbar Rating (A)"]}A, Cu, 1A/mm²</TD></TR>
        <TR><TD>Protection</TD><TD>Type B RCD (AS/NZS 3000:2018 7.9.2)</TD></TR>
        <TR><TD>Standard</TD><TD>AS/NZS 3439.1 (Form 4B)</TD></TR>
    </TABLE>>'''
    dot.node('EVDB', evdb_label, shape='plaintext')
    
    # 4. Connection from Transformer to EVDB (AS/NZS 3008 compliant)
    cable_size = get_incomer_cable_size(msb_result)
    dot.edge('TR', 'EVDB', 
            label=f'415V 4Cx{cable_size}mm²\nPVC/SWA/PVC (AS/NZS 5000.1)\nCurrent Capacity: {CABLE_CAPACITY["4C"][cable_size]}A',
            fontsize='8')
    
    # 5. Individual charger circuits
    for i, charger in enumerate(chargers):
        breaker_id = f'CB_{i}'
        charger_id = f'CH_{i}'
        
        # Circuit Breaker (AS/NZS 60898 for AC, AS/NZS 60947.2 for DC)
        breaker_type = 'MCCB' if charger["Breaker Size (A)"] > 100 else 'MCB'
        breaker_standard = 'AS/NZS 60947.2' if charger["Charger Type"] == 'DC' else 'AS/NZS 60898'
        breaker_label = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
            <TR><TD>{breaker_type}</TD></TR>
            <TR><TD>{charger["Breaker Size (A)"]}A, 10kA</TD></TR>
            <TR><TD>{breaker_standard}</TD></TR>
        </TABLE>>'''
        dot.node(breaker_id, breaker_label, shape='none', width='0.75')
        
        # Charger
        charger_color = "#bbdefb" if charger["Charger Type"] == 'DC' else "#c8e6c9"
        charger_label = f'''<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0">
            <TR><TD>EV CHARGER {i+1}</TD></TR>
            <TR><TD>{charger["Power (kW)"]}kW {charger["Charger Type"]}</TD></TR>
            <TR><TD>{charger["Voltage (V)"]}V</TD></TR>
            <TR><TD>AS/NZS 3000:2018 7.9</TD></TR>
        </TABLE>>'''
        dot.node(charger_id, charger_label, shape='box', style='rounded,filled', fillcolor=charger_color)
        
        # Connections (AS/NZS 3008 compliant)
        dot.edge('EVDB', breaker_id, style='solid', arrowhead='none')
        cable_info = f'''{charger["Cable Size (mm²)"]}mm² {charger["Cable Type"]}
Current Capacity: {charger["Cable Capacity (A)"]}A
AS/NZS 3008.1.2'''
        dot.edge(breaker_id, charger_id, label=cable_info, fontsize='8')
    
    # Legend with standards reference
    legend = '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
        <TR><TD COLSPAN="2" BGCOLOR="#f0f0f0"><B>LEGEND & STANDARDS</B></TD></TR>
        <TR><TD>AC Charger</TD><TD BGCOLOR="#c8e6c9">■</TD></TR>
        <TR><TD>DC Charger</TD><TD BGCOLOR="#bbdefb">■</TD></TR>
        <TR><TD COLSPAN="2"><I>Design to AS/NZS 3000:2018 Wiring Rules</I></TD></TR>
        <TR><TD COLSPAN="2"><I>EV Charging: Clause 7.9</I></TD></TR>
    </TABLE>>'''
    dot.node('LEGEND', legend, shape='plaintext', pos='10,10!')
    
    return dot

def get_incomer_cable_size(msb_result):
    current = msb_result["Diversified Current (A)"]
    if current <= 250: return 120
    elif current <= 400: return 185
    elif current <= 600: return 300
    elif current <= 800: return 400
    else: return 500

def remove_charger(index):
    st.session_state.chargers.pop(index)
    st.rerun()

# Initialize Streamlit App
initialize_session_state()
st.set_page_config(layout="wide", page_title="EV Charger Calculator", page_icon="⚡")
st.title("⚡ EV Charger System Calculator")
st.subheader("Australian Market - AS/NZS Standards")

# Calculation Parameters Section
with st.expander("⚙️ Calculation Parameters", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.calculation_params['safety_factor'] = st.number_input(
            "Safety Factor (for continuous loads)", 
            min_value=1.0, max_value=2.0, value=1.25, step=0.05,
            help="AS/NZS 3000 Clause 2.5.7.2 recommends 125% for continuous loads"
        )
        st.session_state.calculation_params['diversity_factor'] = st.number_input(
            "Diversity Factor", 
            min_value=0.1, max_value=1.0, value=0.9, step=0.05,
            help="Factor applied to total load (AS/NZS 3000 Clause 2.2)"
        )
    with col2:
        st.session_state.calculation_params['dc_efficiency'] = st.number_input(
            "DC Charger Efficiency", 
            min_value=0.8, max_value=1.0, value=0.95, step=0.01,
            help="Typical efficiency of DC chargers (92-96%)"
        )
        st.session_state.calculation_params['power_factor'] = st.number_input(
            "Power Factor", 
            min_value=0.8, max_value=1.0, value=0.95, step=0.01,
            help="Power factor for AC-DC conversion"
        )
    
    col3, col4 = st.columns(2)
    with col3:
        st.session_state.calculation_params['ac_voltage'] = st.number_input(
            "AC System Voltage (V)", 
            min_value=100, max_value=500, value=400, step=10,
            help="Three-phase AC system voltage"
        )
    with col4:
        st.session_state.calculation_params['dc_voltage'] = st.number_input(
            "DC Charger Voltage (V)", 
            min_value=100, max_value=1000, value=500, step=50,
            help="DC charger output voltage"
        )

# Charger Input Section
with st.expander("➕ Add Chargers", expanded=True):
    col1, col2, col3, col4 = st.columns([2,2,2,1])
    with col1:
        charger_type = st.radio("Charger Type", ["AC", "DC"], key="type")
    with col2:
        if charger_type == "AC":
            capacity = st.selectbox("Capacity (kW)", [7, 22], key="capacity")
        else:
            capacity = st.selectbox("Capacity (kW)", [25, 50, 75, 100, 120, 150, 300, 350], key="capacity")
    with col3:
        quantity = 1
    with col4:
        st.write("")
        st.write("")
        if st.button("Add Charger", key="add"):
            result = calculate_requirements(charger_type, capacity, quantity, st.session_state.calculation_params)
            if result:
                st.session_state.chargers.append({
                    "Type": charger_type,
                    "Capacity (kW)": capacity,
                    "Quantity": quantity,
                    **result
                })
                st.rerun()
            else:
                st.error("Could not calculate for this configuration. Check parameters.")

if st.session_state.chargers:
    with st.expander("🔌 Configured Chargers", expanded=True):
        # Create columns for the table header
        headers = st.columns([1, 1, 1, 1, 1, 1, 1])
        headers[0].write("**#**")
        headers[1].write("**Type**")
        headers[2].write("**Capacity (kW)**")
        headers[3].write("**Qty**")
        headers[4].write("**EV Breaker (A)**")
        headers[5].write("**Cable (mm²)**")
        headers[6].write("**Actions**")
        
        # Display each charger in a row with a remove button
        for idx, charger in enumerate(st.session_state.chargers):
            cols = st.columns([1, 1, 1, 1, 1, 1, 1])
            cols[0].write(str(idx+1))
            cols[1].write(charger["Type"])
            cols[2].write(str(charger["Capacity (kW)"]))
            cols[3].write(str(charger["Quantity"]))
            cols[4].write(str(charger["Breaker Size (A)"]))
            cols[5].write(str(charger["Cable Size (mm²)"]))
            
            # Add remove button for each charger
            if cols[6].button("Remove", key=f"remove_{idx}"):
                st.session_state.chargers.pop(idx)
                st.rerun()
        
        # Clear all button
        if st.button("❌ Clear All Chargers", type="primary"):
            st.session_state.chargers = []
            st.rerun()

# Calculate and Display MSB Requirements
msb_result = None
if st.session_state.chargers:
    msb_result = calculate_msb(st.session_state.chargers, st.session_state.calculation_params)
    
    if msb_result:
        with st.expander("⚡ Main Switchboard (MSB) Requirements", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Connected Load", f"{msb_result['Total Connected Load (kW)']} kW")
                st.metric("Total Derated AC Current", f"{msb_result['Total Derated AC Current (A)']} A")
                st.metric("Diversified Current", f"{msb_result['Diversified Current (A)']} A")
            
            with col2:
                st.metric("MSB Main Breaker Size", f"{msb_result['Main Breaker Size (A)']} A")
                st.metric("Recommended MSB Size", f"{msb_result['Recommended MSB Size (A)']}A")
                st.metric("Busbar Rating", f"{msb_result['Busbar Rating (A)']}A")
            
            st.write(f"**MSB Dimensions:** {msb_result['MSB Dimensions']}")

        # Generate and Display SLD
        with st.expander("📐 Single Line Diagram (SLD)", expanded=True):
            # sld = generate_sld(st.session_state.chargers, msb_result)
            sld = generate_sld(st.session_state.chargers, msb_result, st.session_state.calculation_params)
            st.graphviz_chart(sld, use_container_width=True)
            
            st.caption("**Technical Notes:**")
            st.markdown(f"""
            - **Safety Factor:** {st.session_state.calculation_params['safety_factor']}x for continuous loads
            - **Diversity Factor:** {st.session_state.calculation_params['diversity_factor']} applied
            - **DC Charger Efficiency:** {st.session_state.calculation_params['dc_efficiency']*100}%
            - **Power Factor:** {st.session_state.calculation_params['power_factor']}
            - **AC System Voltage:** {st.session_state.calculation_params['ac_voltage']}V
            - **DC Charger Voltage:** {st.session_state.calculation_params['dc_voltage']}V
            """)
    else:
        st.error("MSB calculation failed. Total load may exceed standard configurations.")

# Footer
st.markdown("---")
st.caption(f"**Design Date:** {st.session_state.design_date}")
st.caption("""
**Disclaimer:** This calculator provides estimates based on Australian Standards.  
Actual installations must be designed by a qualified electrician. Always verify with current AS/NZS standards.
""")
