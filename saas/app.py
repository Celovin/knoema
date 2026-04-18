"""Research SaaS dashboard entry point."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Knoema Research", layout="wide")
    st.title("Knoema Research")
    st.write("Run, compare, inspect, and export reproducible agent simulation experiments.")
    st.page_link("pages/1_Simulation_Runner.py", label="Simulation Runner")
    st.page_link("pages/2_Experiment_Comparison.py", label="Experiment Comparison")
    st.page_link("pages/3_Memory_Inspector.py", label="Memory Inspector")
    st.page_link("pages/4_Relationship_Explorer.py", label="Relationship Explorer")
    st.page_link("pages/5_Cost_Budget.py", label="Cost Budget")
    st.page_link("pages/6_Export_Citations.py", label="Export Citations")


if __name__ == "__main__":
    main()
