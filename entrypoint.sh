#!/bin/sh

streamlit run streamlit_app.py --server.port=${PORT:-8080} --server.address=0.0.0.0