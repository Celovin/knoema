"""Relationship explorer page."""

from __future__ import annotations

import streamlit as st

from saas.components.graph_viz import build_relationship_graph
from saas.services.experiment_store import load_experiment_jsonl, relationship_graph_rows

st.set_page_config(page_title="Relationship Explorer", layout="wide")
st.title("Relationship Explorer")

path = st.text_input("Experiment JSONL", value="experiments/50_agent_village/results/sim_log.jsonl")
if st.button("Build relationship graph"):
    rows = load_experiment_jsonl(path)
    st.dataframe(relationship_graph_rows(rows))
    st.json(build_relationship_graph(rows))
