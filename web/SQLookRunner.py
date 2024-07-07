from database import Database
from table import Table
import sys, json
import sqlite3

from flask import Flask, render_template, url_for
app = Flask(__name__)

app.logger.setLevel('DEBUG')

res = app.config.from_file("config/config.json", load=json.load)
databaseUrl = app.config["DBPATH"]
app.logger.info('DBPATH in use %s',databaseUrl)

@app.route("/")
def showDatabaseInfo():
    app.logger.info('Open database %s',databaseUrl)
    currDB = Database(databaseUrl)
    app.logger.debug('List tables %s',databaseUrl)
    currDB.listHardware()
    currDB.listNetwork()
    return render_template('database.html', databaseInfo=databaseUrl,listHW=currDB.hardware, \
                listNET=currDB.network)

@app.route("/table/<objType>/<objName>")
def showTableInfo(objType=None,objName=None):
    app.logger.info('Get info %s',objName)
    if objType =='table':
        currTable = Table(databaseUrl, objName,'table')
    else:
        currTable = Table(databaseUrl, objName,'view')
    currTable.getSize()
    currTable.listField()
    app.logger.debug('Get info done %s',objName)
    return render_template('table.html', databaseInfo=databaseUrl,tableName=currTable.name, \
                countLine=currTable.count, objType=currTable.type, listField=currTable.listfield)

""" @app.route("/detail/<objType>/<objName>")
def showTableDetail(objType=None,objName=None):
    app.logger.info('Get details %s',objName)
    if objType =='table':
        currTable = Table(databaseUrl, objName,'table')
    else:
        currTable = Table(databaseUrl, objName,'view')
    currTable.listField()
    currTable.getTopRecord()
    app.logger.debug('Get details done %s',objName)
    return render_template('detail.html', databaseInfo=databaseUrl,tableName=currTable.name, \
                topRecod=currTable.topRecord, listField=currTable.listfield) """



@app.route("/detail/<objType>/<objName>")
def showTableDetail(objType=None,objName=None):
    app.logger.info('Get details %s',objName)
    if objType =='table':
        currTable = Table(databaseUrl, objName,'table')
    else:
        currTable = Table(databaseUrl, objName,'view')
    currTable.listField()
    currTable.getSize()
    currTable.getTopRecord()
    app.logger.debug('Get details done %s',objName)
    return render_template('detail.html', databaseInfo=databaseUrl,tableName=currTable.name, \
                countLine=currTable.count,topRecod=currTable.topRecord, listField=currTable.listfield, objType=currTable.type)
