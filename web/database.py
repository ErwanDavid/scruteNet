from table import Table
import datawrapper as dv


class Database:
    def __init__(self, databaseUrl):
        self.conn = dv.getConnection(databaseUrl)

    def listHardware(self):
        self.hardware = dv.getlistHardware(self.conn)

    def listNetwork(self):
        self.network = dv.getlistNetwork(self.conn)
