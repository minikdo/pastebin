import sqlite3


class DB():
    def __init__(self, db):
        self.conn = sqlite3.connect(db, check_same_thread=False)
        self.cur = self.conn.cursor()

    def query(self, arg, *args):
        self.cur.execute(arg, *args)
        self.conn.commit()
        return self.cur

    def __del__(self):
        self.conn.close()
