# Tools for ip connection inspection


## Install

You need to create a virtual env, called for example 'venv'.
For example at the root of the repo:
`python -m venv ./venv `

Activate it :
`source ./venv/bin/activate`
or
`.\venv\Scripts\activate`

You need to install in this venv some modules

```
pip install dash
pip install psutil
pip install pandas
pip install ipwhois
```

## Run
python ./analyseConn.py



## Possible issue
https://learn.microsoft.com/fr-fr/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.5
You may need to activate PS scripts : 
Set-ExecutionPolicy -ExecutionPolicy Unrestricted
