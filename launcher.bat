set path=C:\Users\erwan\Documents\GIT_PERSO\scruteNet
start /B %path%\venv\Scripts\python.exe scrute.py

start /B %path%\venv\Scripts\python.exe monitor.py 

start /B %path%\venv\Scripts\python.exe resolve.py 

cd %path%\web
set FLASK_APP=SQLookRunner
start /B %path%\venv\Scripts\flask.exe run
