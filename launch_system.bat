@echo off
echo Starting KYC System Launcher...
cd /d "C:\Users\Antonio\OneDrive\Desktop\Know Your Customer"
set PYTHONPATH=C:\Users\Antonio\OneDrive\Desktop\Know Your Customer
python -m streamlit run simple_launcher.py --server.port 8514
pause
