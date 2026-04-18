"""Simulation runner page."""

from __future__ import annotations

import streamlit as st

from knoema.dsl import load_scenario

st.set_page_config(page_title="Simulation Runner", layout="wide")
st.title("Simulation Runner")

scenario_path = st.text_input("Scenario YAML", value="examples/scenarios/01_shopkeeper_winter_crime.yaml")
if st.button("Run deterministic local simulation"):
    scenario = load_scenario(scenario_path)
    logs = scenario.to_simulator().run(duration_days=scenario.duration_days)
    st.metric("Actions", len(logs))
    st.json([entry.to_json_dict() for entry in logs[:10]])
