import logging
import sqlite3
import sys, time
import socket

logger = logging.getLogger('resolveMain')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

conn = sqlite3.connect("DBs/db_connection.sqlite3", timeout=20)
cursor = conn.cursor()

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
        except socket.herror as err:
            logger.error("Cannot resolve " + item + " " + str(err))
            insert_sql(item, 'host not found')
            conn.commit()

def main():
    while (1):
        start = time.perf_counter()
        listIp = get_ip()
        logger.info("Size {}".format(len(listIp)))
        get_name(listIp)
        conn.commit()
        finish = time.perf_counter()
        logger.info(f'Finished in {round(finish-start, 2)} second(s)')
        time.sleep(60)
    

if __name__ == '__main__':
    sys.exit(main())

""" select h.rip, h.seens_nbr, h.seens_last, i1.name
from t_minipc_20240407 h, t_ip i1
where h.rip = i1.ip and i1.name is not null
order by h.seens_nbr desc """