import sqlite3
p='D:/ExplainNet/explainnet.db'
conn=sqlite3.connect(p)
cur=conn.cursor()
cur.execute('PRAGMA table_info(sentiments)')
cols=cur.fetchall()
print('columns in',p)
for c in cols:
    print(c)
conn.close()
