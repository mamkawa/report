@echo off
cd /d "C:\Users\81901\cursor\仕事\釣銭予測\ATM_master"
set PYTHONIOENCODING=utf-8
call .venv\Scripts\activate.bat
streamlit run dashboard.py --server.port=8501
pause 