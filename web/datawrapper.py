from sqlalchemy import create_engine, text, inspect, MetaData, func, select, Table
from field import Field

def getEngine(dburl):
    return create_engine(dburl)
     
def getConnection(dburl):
    dbEngine=create_engine(dburl)
    return dbEngine.connect()

def getlistHardware(dbConn):
    insp = inspect(dbConn) 
    getTableHW = insp.get_table_names()
    tableArrHW = []
    for currTable in getTableHW:
         if 'hw_' in currTable:
              tableArrHW.append(currTable)
    return tableArrHW

def getlistNetwork(dbConn):
    insp = inspect(dbConn) 
    getTableNET = insp.get_table_names() + insp.get_view_names()
    tableArrNET = []
    for currTable in getTableNET:
         if 't_' in currTable:
              tableArrNET.append(currTable)
    return tableArrNET

def getTableSize(dbConn, tableName):
    query = select(func.count("*")).select_from(text(tableName))
    #query = select(tableName)
    print(query)
    exe = dbConn.execute(query)
    row_count = exe.scalar()
    return row_count

def getTableField(dbConn, dbEngine, tableName):
        metadata_obj = MetaData()
        listFildObj = []
        metadata = Table(tableName, metadata_obj, autoload_with=dbEngine)
        for myCol in metadata.columns:
             listFildObj.append(Field(dbConn,tableName, myCol.name, myCol.type, myCol.nullable))
        return listFildObj

def gettopRecord(dbConn, tableName, limit):
    if 'hw_' in tableName :
         orderBy = "tm desc"
    else:
         orderBy = "seens_nbr desc"
    query = text("select * from {} order by {} limit {}".format(tableName, orderBy, str(limit)))
    print(query)
    return  dbConn.execute(query)
     
