import psutil, socket
from datetime import datetime

map_psutil_sql = {}
map_psutil_sql[0] = "fd"
map_psutil_sql[1] = "familly"
map_psutil_sql[2] = "type"
map_psutil_sql[3] = "laddr"
map_psutil_sql[4] = "raddr"
map_psutil_sql[5] = "statut"
map_psutil_sql[6] = "pid"
hostname = "{}_{}".format(socket.gethostname(),datetime.now().strftime("%Y%m"))
hostname = hostname.replace('-','')


def manage_connection(connection, hostname):
    connDict={}
    print("COMM", connection)
    for myId in range(len(connection)):
        print("  cur id", myId, len(connection))
        if connection[myId]:
            if map_psutil_sql[myId] in 'laddr':
                print("     map_psutil_sql", map_psutil_sql[myId])
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
            if 'statut' not in connDict.keys() :
                connDict['statut'] = '???'
            if 'pid' not in connDict.keys() :
                connDict['pid'] = '???'
                connDict['pname'] = '???'
    print(connDict)
    print("\n\n")


list_con = psutil.net_connections(kind='all')
for connection in list_con :
        manage_connection(connection,hostname)