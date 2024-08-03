import logging
import sqlite3
import sys, time
import socket
import json
from ipwhois import IPWhois

configData = {}
configFile = 'config\\config.json'


logger = logging.getLogger('resolveMain')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
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


def create_insert(eachIP, host_name, registrar,  creation_date, country):
    logger.debug(f'    INSERT  IP  {eachIP} Name {host_name}  Reg {registrar} Cr date {creation_date}  from {country} ')
    update_statement = "UPDATE t_ip SET name=?, registrar=?, creation_date=?, country=?  WHERE ip = ?"
    cursor.execute(update_statement, (host_name, registrar,  creation_date, country, eachIP,))
    conn.commit()

def get_name(currentIp):
    try:
        myName = socket.gethostbyaddr(currentIp)
        logger.debug("    RESOLVED " + myName[0])
        return myName[0]
    except socket.herror as err:
        logger.error("    Cannot resolve " + currentIp + " " + str(err))
        return 'host not found' 

def get_dns(currentIp):
    try:
        dm_info =  IPWhois(currentIp)
        res=dm_info.lookup_whois()
        logger.debug("   DNS info ok  " + res["nets"][0]['description'])
        #print(res)
        return [res["nets"][0]['description'],  res["nets"][0]['created'], res["nets"][0]['country'] ]
    except:
        logger.error("Cannot get DNS info " + currentIp)
        return ['', '', '' ]

def main():
    readConf()
    logger.info("Readed conf ")
    global conn
    global cursor
    database_url = configData["DBPATH"].replace("sqlite:///","")
    conn = sqlite3.connect(database_url, timeout=20)
    cursor = conn.cursor()
    while (1):
        time.sleep(configData["RESOLVE_SLEEP"])
        start = time.perf_counter()
        listIp = get_ip()
        for eachIP in listIp:
            logger.info(" Working on " + eachIP)
            host_name = get_name(eachIP)
            DNS_info = get_dns(eachIP)
            create_insert(eachIP, host_name, DNS_info[0],  DNS_info[1], DNS_info[2])
        conn.commit()
        finish = time.perf_counter()
        logger.info(f'Finished in {round(finish-start, 2)} second(s)')
        
    

if __name__ == '__main__':
    sys.exit(main())
