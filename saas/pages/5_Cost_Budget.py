"""Cost budget page."""

from __future__ import annotations

import streamlit as st

from saas.components.token_meter import estimate_token_budget
from saas.services.experiment_store import load_experiment_jsonl

st.set_page_config(page_title="Cost Budget", layout="wide")
st.title("Cost Budget")

path = st.text_input("Experiment JSONL", value="experiments/50_agent_village/results/sim_log.jsonl")
prompt_rate = st.number_input("Prompt rate per 1M tokens", value=1.0)
completion_rate = st.number_input("Completion rate per 1M tokens", value=3.0)
if st.button("Estimate budget"):
    rows = load_experiment_jsonl(path)
    st.json(
        estimate_token_budget(
            rows,
            prompt_rate_per_million=prompt_rate,
            completion_rate_per_million=completion_rate,
        )
    )
