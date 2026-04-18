"""Memory inspector page."""

from __future__ import annotations

import streamlit as st

from saas.services.experiment_store import load_experiment_jsonl, memory_inspector_rows

st.set_page_config(page_title="Memory Inspector", layout="wide")
st.title("Memory Inspector")

path = st.text_input("Experiment JSONL", value="experiments/50_agent_village/results/sim_log.jsonl")
if st.button("Inspect memory proxies"):
    rows = load_experiment_jsonl(path)
    st.dataframe(memory_inspector_rows(rows))
