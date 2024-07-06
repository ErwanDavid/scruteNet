import logging
import sqlite3
import socket                   # get host name
import psutil                   # cpu usage
import time                    # sleep, timestamp
from datetime import datetime
import sys                       # sensor cmd
import json                     #parse json sensor output


# create logger
logger = logging.getLogger('scruteMain')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

conn = sqlite3.connect("DBs/db_connection.sqlite3", timeout=20)
cursor = conn.cursor()

nbr_disk = 2

def create_table(hostname):
    list_field_crTable = ['tm datetime','cpu float', 'mem float']
    for diskID in range(0, nbr_disk):
        list_field_crTable.append('hdd_' + str(diskID))
    list_str_crTable = ",".join(list_field_crTable)
    sql_crTable = "CREATE TABLE IF NOT EXISTS {}  ( {} )".format(hostname, list_str_crTable)
    logger.debug(sql_crTable)
    cursor.execute(sql_crTable)

def get_cpu_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    return cpu_usage

def get_free_mem():
    memory_stats = psutil.virtual_memory()
    #print(memory_stats)
    free_mem =  memory_stats.percent
    return free_mem

def get_disk_free(disk_id):
    #try:
        #print("disk_id", str(disk_id))
        disk_info = psutil.disk_partitions()
        free_info = []
        name_info = []
        for disk in disk_info:
            #print(disk)
            if disk.fstype == "xfs" or disk.fstype == "btrfs" or disk.fstype == "ext4" or disk.fstype == "vfat"  or disk.fstype == "exFAT" or disk.fstype == "NTFS":
                if 'boot' not in disk.mountpoint :
                    free_info.append(psutil.disk_usage(disk.mountpoint).percent)
                    name_info.append(disk.mountpoint)
        #print(free_info)
        clean_name = name_info[disk_id].replace('/','-').replace('\\','').replace(':','')
        if clean_name == '-':
            clean_name = 'root'
        return clean_name, free_info[disk_id]
    #except:
    #    return False, False

def insert_monitoring(hostname, cpu_usage, free_mem, hdd_array):
    sql_insert = "INSERT INTO {} (tm, cpu, mem, hdd_0, hdd_1) VALUES (CURRENT_TIMESTAMP,?,?,?,?);".format(hostname)
    logger.debug(f'Insert {sql_insert}')
    cursor.execute(sql_insert, (cpu_usage, free_mem,hdd_array[0],hdd_array[1],))

def main():
    hostname = "hw_{}_{}".format(socket.gethostname(),datetime.now().strftime("%Y%m"))
    hostname = hostname.replace('-','')
    create_table(hostname)
    while (1):
        start = time.perf_counter()
        cpu_usage = get_cpu_usage()
        logger.debug(f'CPU usage  {cpu_usage}')
        free_mem = get_free_mem()
        logger.debug(f'MEM usage  {free_mem}')
        hdd_array = []
        for diskID in range(0, nbr_disk):
            current_disk, freespace = get_disk_free(diskID)
            hdd_array.append(freespace)
        logger.debug(f'HDD usage  {hdd_array}')
        insert_monitoring(hostname, cpu_usage, free_mem, hdd_array)
        conn.commit()
        finish = time.perf_counter()
        logger.info(f'Finished in {round(finish-start, 2)} second(s) cpu usage : {cpu_usage}')
        time.sleep(30)
        

if __name__ == '__main__':
    sys.exit(main())