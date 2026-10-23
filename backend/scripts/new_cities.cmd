@echo off
rem Ex-showroom prices + dealers for the major cities (manufacturer sites only). Hyderabad runs in daily_refresh.cmd.
cd /d "%~dp0.."
for %%C in ("Secunderabad" "Warangal" "Karimnagar" "Nizamabad" "Khammam" "Mysuru" "Coimbatore" "Madurai" "Nagpur" "Surat" "Thiruvananthapuram" "Bhopal" "Indore" "Patna" "Bhubaneswar" "Guwahati" "Panaji" "Dehradun" "Ranchi" "Raipur" "Shimla" "Ludhiana" "Srinagar" "Puducherry" "Port Blair" "Itanagar" "Daman" "Leh" "Kavaratti" "Shillong" "Imphal" "Aizawl" "Kohima" "Gangtok" "Agartala") do (
  echo === %%C %date% %time% >> "%~dp0..\multi_city.log"
  "C:\Users\saath\AppData\Local\Programs\Python\Python313\python.exe" -m onroad.ingest --city %%C >> "%~dp0..\multi_city.json" 2>> "%~dp0..\multi_city.log"
)
echo === done %date% %time% >> "%~dp0..\multi_city.log"
