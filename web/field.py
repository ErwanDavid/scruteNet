import sqlite3

class Field:
    def __init__(self, connectionObj, table, name, fieldType, nullable):
        self.conn = connectionObj
        self.table = table
        self.name = name
        self.fieldType = str(fieldType).lower()
        self.nullable = nullable

    def reveal(self):
        self.detailStr = ''
        if self.fieldType != 'INTEGER':
            sql_detail = "select " + self.name + ", count(1) from " + self.table + " group by " +  self.name + " order by 2 desc limit 4"
            count = self.conn.execute(sql_detail).fetchall()
            count=[item[0] for item in count]
            self.detailStr = str(count)
        else:
            sql_min = "select min(" + self.name + ") from " + self.table
            min = self.conn.execute(sql_min).fetchall()
            self.detailStr = str(min)


