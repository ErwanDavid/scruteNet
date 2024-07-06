import psutil
import sys
import socket
import sqlite3
import time
from datetime import datetime
import logging

# create logger
logger = logging.getLogger('scruteMain')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

conn = sqlite3.connect("DBs/db_connection.sqlite3", timeout=20)
cursor = conn.cursor()

map_psutil_sql = {}
map_psutil_sql[0] = "fd"
map_psutil_sql[1] = "familly"
map_psutil_sql[2] = "type"
map_psutil_sql[3] = "laddr"
map_psutil_sql[4] = "raddr"
map_psutil_sql[5] = "statut"
map_psutil_sql[6] = "pid"

list_field = ['fd', 'familly', 'type', 'laddr', 'raddr', 'lip', 'lpo', 'rip', 'rpo', 'statut', 'pid','pname', 'seens_nbr', 'seens_last']
list_field_crTable = ['fd integer', 'familly', 'type', 'laddr', 'raddr', 'lip', 'lpo integer', 'rip', 'rpo integer', 'statut', 'pid integer', 'pname', 'seens_nbr integer', 'seens_last datetime']
list_str = ",".join(list_field)
list_str_crTable = ",".join(list_field_crTable)

def create_table(hostname):
    sql_crTable = "CREATE TABLE IF NOT EXISTS t_" + hostname + " (" +  list_str_crTable
    sql_crTable = sql_crTable +  ", CONSTRAINT pk_" + hostname + " PRIMARY KEY (lip, lpo, rip, rpo));"
    logger.info(sql_crTable)
    cursor.execute(sql_crTable)

def create_table_ip():
    sql_crTable = "CREATE TABLE IF NOT EXISTS t_ip (ip,name, CONSTRAINT pk_ip PRIMARY KEY (ip));"
    logger.debug(sql_crTable)
    cursor.execute(sql_crTable)

def upsert_sql(connDict, hostname):
    to_db = []
    to_db_srt = ''
    for item in list_field:
        to_db.append(connDict[item])
        to_db_srt += str(connDict[item]) + ' '
    sql_insert = "INSERT INTO  t_" + hostname + " (" + list_str + ")  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT (lip, lpo, rip, rpo) DO UPDATE SET seens_nbr=seens_nbr+1, seens_last=excluded.seens_last;"
    logger.debug(sql_insert + to_db_srt )
    cursor.execute(sql_insert, to_db)

def upsert_sql_ip(connDict):
    for currentIp in (connDict['rip'],connDict['lip']):
        sql_insert = "INSERT INTO t_ip (ip) VALUES (?) ON CONFLICT (ip) DO NOTHING;"
        logger.debug(sql_insert + currentIp)
        cursor.execute(sql_insert, (currentIp,))

def manage_connection(connection, hostname):
    connDict={}
    for myId in range(len(connection)):
        if map_psutil_sql[myId] in 'laddr':
            connDict[map_psutil_sql[myId]] = str(connection[myId])
            connDict['lip'] = connection[myId][0]
            connDict['lpo'] = connection[myId][1]

        elif map_psutil_sql[myId] in 'raddr':
            connDict[map_psutil_sql[myId]] = str(connection[myId])
            if len(connection[myId]) > 1:
                connDict['rip'] = connection[myId][0]
                connDict['rpo'] = connection[myId][1]
            else:
                connDict['rip'] = ''
                connDict['rpo'] = ''
        elif map_psutil_sql[myId] in 'pid':
            connDict[map_psutil_sql[myId]] = connection[myId]
            try:
                process = psutil.Process(connection[myId])
                process_name = process.name()
                connDict['pname'] = process_name
            except:
                connDict['pname'] = 'unknown'
        else:
            #logger.debug(str(connection[myId]) + " type " + str(type(connection[myId])))
            if type(connection[myId]) == int or type(connection[myId]) == str :
                connDict[map_psutil_sql[myId]] = connection[myId]
            else:
                connDict[map_psutil_sql[myId]] = str(connection[myId])
    connDict['seens_nbr'] =1
    connDict['seens_last'] = datetime.now()
    upsert_sql_ip(connDict)
    upsert_sql(connDict, hostname)

def main():
    hostname = "{}_{}".format(socket.gethostname(),datetime.now().strftime("%Y%m"))
    hostname = hostname.replace('-','')
    create_table(hostname)
    create_table_ip()
    while (1):
        start = time.perf_counter()
        list_con = psutil.net_connections(kind='all')
        logger.info("Work on a list of " + str(len(list_con)))
        for connection in list_con :
            manage_connection(connection,hostname)
        conn.commit()
        finish = time.perf_counter()
        logger.info(f'Finished in {round(finish-start, 2)} second(s)')
        time.sleep(10)
        

if __name__ == '__main__':
    sys.exit(main())






