⚡ EV Charger System Calculator

A Streamlit app designed to support planning and sizing of EV charging infrastructure in accordance with Australian Standards (AS/NZS 3000, 3008, 60947.2, 60898, 3439.1, and 60076).

🔧 Features
	•	Charger Config Input: Add AC (7kW/22kW) or DC (25–350kW) chargers
	•	Standards-Based Calculations:
	•	Breaker sizing
	•	Cable sizing based on AS/NZS 3008
	•	Derating using safety factors
	•	Main Switchboard (MSB) Sizing:
	•	Diversified load calculation
	•	Main breaker and busbar rating
	•	MSB dimensions based on common configurations
	•	Visual SLD Generation:
	•	Auto-generates Single Line Diagram (SLD) for all charger configurations
	•	Session State Memory: Keeps user inputs intact across app interactions

📘 How it Works
	1.	Add Chargers: Select type (AC/DC), size (kW), and quantity.
	2.	Calculator Engine:
	•	Computes current draw
	•	Applies safety and diversity factors
	•	Selects breakers and cables using AS/NZS standard values
	3.	MSB Sizing:
	•	Aggregates charger loads
	•	Applies diversity
	•	Selects MSB based on available configurations
	4.	SLD Visualisation:
	•	Renders a diagram using graphviz showing the transformer, MSB, breakers, and chargers
	•	Includes cable specs and relevant AS/NZS clauses

📐 Customisable Parameters

Available in the Calculation Parameters panel:
	•	Safety factor
	•	Diversity factor
	•	Charger efficiency (DC)
	•	Power factor
	•	AC & DC system voltages

✅ Standards Referenced
	•	AS/NZS 3000:2018 – Wiring Rules
	•	AS/NZS 3008.1.2:2017 – Cable current capacity
	•	AS/NZS 60898 / 60947.2 – Circuit breakers
	•	AS/NZS 3439.1 – Switchboard design
	•	AS/NZS 60076 – Transformer specs

⚠️ Disclaimer

This tool provides preliminary estimates and visualisation only.
Final designs must be verified by a licensed electrical engineer using up-to-date standards.
