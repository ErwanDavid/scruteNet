# Tools for ip connection inspection

## Components
### scrute.py file
insert in sqlite DB current ip connection + distinct list of ip + the pid of the connected program, use an upsert to count the time an ip is seen

### resovle.py file
get dns name + whois info for distinct ip & insert into DB

### monitor.py file
added hw monitor (cpu/hdd/ram info)

### Web/ folder
Allow to browse the created DBs

## Install

You need to create a virtual env, called 'venv' in the root of the repo.
`python -m venv ./venv `

Activate it :
`./venv/bin/activate`
or
`.\venv\Script\activate`

You need to install in this venv some modules

```
pip install flask
pip install sqlalchemy
pip install psutil
pip install exifread
pip install pikepdf
pip install eyed3
pip install magika
pip install python-docx
```


## Run

### Windows
Update the launcher & the config file (in ./config) & launch the .bat file

### Linux



Todo : compiler eg https://nuitka.net/user-documentation/user-manual.html
https://stackoverflow.com/questions/5458048/how-can-i-make-a-python-script-standalone-executable-to-run-without-any-dependen
