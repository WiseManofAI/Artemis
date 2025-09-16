#!/usr/bin/env bash
# simple helper to run backend + frontend locally (Unix)
uvicorn backend.main:app --reload --port 8000 &
streamlit run frontend/streamlit_app.py --server.port 8501
