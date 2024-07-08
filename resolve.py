import logging
import sqlite3
import sys, time
import socket
import json

configData = {}
configFile = 'config\\config.json'


logger = logging.getLogger('resolveMain')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def readConf():
    global configData
    with open(configFile, 'r') as f:
        configData = json.load(f)


def insert_sql(ip, name):
    update_statement = "UPDATE t_ip SET name=? WHERE ip = ?"
    #logger.debug("update_statement " + update_statement + " name " + name  + " ip " + ip)
    cursor.execute(update_statement, (name, ip,))
    conn.commit()

def get_ip():
    listIp = []
    cursor.execute("select distinct ip from t_ip where name is null")
    rows = cursor.fetchall()
    for row in rows:
        if len(row[0]) > 1:
            listIp.append(row[0])
    return listIp

def get_name(listIp):
    for item in listIp:
        try:
            myName = socket.gethostbyaddr(item)
            #logger.debug(item + " RESOLVED " + myName[0])
            logger.debug(" RESOLVED " + myName[0])
            insert_sql(item, myName[0])
            conn.commit()
        except socket.herror as err:
            logger.error("Cannot resolve " + item + " " + str(err))
            insert_sql(item, 'host not found')

def main():
    readConf()
    global conn
    global cursor
    conn = sqlite3.connect(configData["DBFILE"], timeout=20)
    cursor = conn.cursor()
    while (1):
        time.sleep(configData["RESOLVE_SLEEP"])
        start = time.perf_counter()
        listIp = get_ip()
        logger.info("Size {}".format(len(listIp)))
        get_name(listIp)
        conn.commit()
        finish = time.perf_counter()
        logger.info(f'Finished in {round(finish-start, 2)} second(s)')
        
    

if __name__ == '__main__':
    sys.exit(main())
