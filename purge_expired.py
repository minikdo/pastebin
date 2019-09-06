#!/usr/bin/env python3

import os
from datetime import datetime
from settings import BASE_DIR
from db import DB


def remove_file(md5sum):
    try:
        os.remove(os.path.join('uploads', md5sum))
    except FileNotFoundError as e:
        print(e)
    finally:
        db.query("DELETE FROM file WHERE md5sum = '{}'".format(md5sum))

    
def expired():
    res = db.query('SELECT md5sum FROM file WHERE expire < {}'.format(now))
    rows = res.fetchall()
    
    for row in rows:
        print(row[0])
        remove_file(row[0])
            
    return True


if __name__ == '__main__':
    now = int(datetime.now().timestamp())
    db = DB(os.path.join(BASE_DIR, "pastebin.db"))
    expired()
