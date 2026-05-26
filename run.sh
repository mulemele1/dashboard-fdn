#!/bin/bash
cd /home/escalen2/dashboard-fdn.escaleno.co.mz
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.enableCORS false --server.enableXsrfProtection false --server.headless true
