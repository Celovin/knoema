"""Citation export page."""

from __future__ import annotations

import streamlit as st

from saas.services.experiment_store import citation_bundle

st.set_page_config(page_title="Export Citations", layout="wide")
st.title("Export Citations")

title = st.text_input("Artifact title", value="Luvoire Research Experiment")
author = st.text_input("Author", value="Celovin")
year = st.number_input("Year", value=2026, step=1)
bundle = citation_bundle(title=title, author=author, year=int(year))
st.code(bundle["bibtex"], language="bibtex")
st.write(bundle["apa"])
