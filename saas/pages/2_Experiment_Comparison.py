"""Experiment comparison page."""

from __future__ import annotations

import streamlit as st

from saas.services.experiment_store import compare_experiments, load_experiment_jsonl
from saas.services.replay import ab_timeline

st.set_page_config(page_title="Experiment Comparison", layout="wide")
st.title("Experiment Comparison")

left_path = st.text_input("Experiment A JSONL", value="experiments/50_agent_village/results/sim_log.jsonl")
right_path = st.text_input("Experiment B JSONL", value="experiments/50_agent_village/results/sim_log.jsonl")
if st.button("Compare experiments"):
    left = load_experiment_jsonl(left_path)
    right = load_experiment_jsonl(right_path)
    comparison = compare_experiments(left, right)
    st.json(comparison)
    st.dataframe(ab_timeline(left, right))
