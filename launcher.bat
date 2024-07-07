cd C:\Users\erwan\Documents\GIT_PERSO\scruteNet\ 
start /B C:\Users\erwan\Documents\GIT_PERSO\scruteNet\venv\Scripts\python.exe  scrute.py

start /B C:\Users\erwan\Documents\GIT_PERSO\scruteNet\venv\Scripts\python.exe  monitor.py 

start /B C:\Users\erwan\Documents\GIT_PERSO\scruteNet\venv\Scripts\python.exe  resolve.py 

cd C:\Users\erwan\Documents\GIT_PERSO\scruteNet\web
set FLASK_APP=SQLookRunner
start /B C:\Users\erwan\Documents\GIT_PERSO\scruteNet\venv\Scripts\flask.exe run
