#!/usr/bin/env python3

import os
from datetime import datetime
from db import DB


def remove_file(md5sum):
    os.remove(os.path.join('uploads', md5sum))
    db.query("DELETE FROM file WHERE md5sum = '{}'".format(md5sum))

    
def expired():
    res = db.query('SELECT md5sum FROM file WHERE expire > {}'.format(now))
    rows = res.fetchall()
    
    for row in rows:
        remove_file(row[0])
            
    return True


if __name__ == '__main__':
    now = int(datetime.now().timestamp())
    db = DB("pastebin.db")
    expired()
