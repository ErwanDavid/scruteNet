import datawrapper as dv
from field import Field
import locale

locale.setlocale(locale.LC_ALL, '') 

class Table:
    def __init__(self, databaseUrl, name, type):
        self.conn = dv.getConnection(databaseUrl)
        self.engine = dv.getEngine(databaseUrl)
        self.name = name
        self.type = type.upper()

    def getSize(self):
        self.count = dv.getTableSize(self.conn, self.name)

    def getTopRecord(self):
        self.topRecord = dv.gettopRecord(self.conn, self.name, 200)

    def listField(self):
        self.listfield = dv.getTableField(self.conn, self.engine, self.name)
        