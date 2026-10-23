@echo off
rem Daily OnRoad refresh: re-reads every brand adapter (manufacturer sites only) for Hyderabad; price rows are written only on change.
cd /d "%~dp0.."
"C:\Users\saath\AppData\Local\Programs\Python\Python313\python.exe" -m onroad.ingest --city Hyderabad >> "%~dp0..\refresh.log" 2>&1
"C:\Users\saath\AppData\Local\Programs\Python\Python313\python.exe" -m onroad.loan_rates >> "%~dp0..\refresh.log" 2>&1
"C:\Users\saath\AppData\Local\Programs\Python\Python313\python.exe" -m onroad.fill_images >> "%~dp0..\refresh.log" 2>&1
