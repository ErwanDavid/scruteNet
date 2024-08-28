set path=C:\Users\erwan\Documents\GIT_PERSO\scruteNet
cd %path%\
set config=.\config\config.json

start /B %path%\venv\Scripts\python.exe scrute.py %config%

start /B %path%\venv\Scripts\python.exe monitor.py  %config%

start /B %path%\venv\Scripts\python.exe resolve.py  %config%

cd %path%\web
set FLASK_APP=SQLookRunner
start /B %path%\venv\Scripts\flask.exe run
