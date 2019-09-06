import os
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
import base64
from sqlite3 import OperationalError

from hashlib import md5
from math import floor
from string import ascii_lowercase, ascii_uppercase, digits
from time import time, ctime

from db import DB
from settings import get_secret

app = Flask(__name__)
BASE_DIR = '/'

DEBUG = False
PORT = 5000

db = DB("pastebin.db")  # FIXME

SECRET_KEY = get_secret('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = get_secret('UPLOAD_FOLDER')
app.config['MAX_CONTENT_LENGTH'] = get_secret('MAX_CONTENT_MB')\
                                   * 1024 * 1024
host = get_secret('HOST')


def table_check():
    create_table = """
        CREATE TABLE file (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        link TEXT,
        md5sum TEXT NOT NULL,
        expire INTEGER NOT NULL
        );
        """
    try:
        db.query(create_table)
    except OperationalError:
        pass


table_check()  # FIXME


def toBase62(num, b=62):
    """ calculate Base62 """

    if b <= 0 or b > 62:
        return 0
    base = digits + ascii_lowercase + ascii_uppercase
    r = num % b
    res = base[r]
    q = floor(num / b)
    while q:
        r = q % b
        q = floor(q / b)
        res = base[int(r)] + res
    return res


def toBase10(num, b=62):
    """ reverse Base62 """

    base = digits + ascii_lowercase + ascii_uppercase
    limit = len(num)
    res = 0
    for i in range(limit):
        res = b * res + base.find(num[i])
    return res


def calc_md5(fname):
    """ calculate md5sum of the uploaded file """

    hash_md5 = md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def file_exists(md5sum):
    """ checks if the file exists in the database by md5sum """

    res = db.query('SELECT id FROM file WHERE md5sum = ?', [md5sum])
    if res.fetchone() is None:
        return False
    return True


def shorten_filename(fname, md5sum, expire):
    """ generates shortened filename """

    res = db.query("""
                   INSERT INTO file (filename, md5sum, expire)
                   VALUES (?,?,?)
                   """,
                   [base64.b64encode(fname.encode("UTF-8")), md5sum, expire])
    encoded_string = toBase62(res.lastrowid)

    db.query("UPDATE file SET link = '{link}' WHERE id = {id}".format(
        link=encoded_string, id=res.lastrowid
    ))
    return host + encoded_string


@app.route('/' + SECRET_KEY + '/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'no file part'

        file = request.files['file']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return 'no selected file'

        # process file and insert db record
        if file:
            # make tmp filename
            tmp_fname = str(int(time()))
            fname = secure_filename(file.filename)
            filename = os.path.join(app.config['UPLOAD_FOLDER'], tmp_fname)

            # save file to disk
            file.save(filename)

            # calculate md5sum
            md5sum = calc_md5(filename)

            new_fname = os.path.join(app.config['UPLOAD_FOLDER'], md5sum)

            # check if file exists by hash
            if file_exists(md5sum):
                os.remove(filename)
                res = db.query("""
                               SELECT link, expire FROM file
                               WHERE md5sum = ?
                               """, [md5sum])

                link, expire = res.fetchone()
                expire = ctime(int(expire))
                output = "File exists:\n" + host + str(link)
                output = output + "\nUntil: " + expire

                return output

            # rename tmp file
            os.rename(filename, new_fname)

            days = request.form.get('expire', 1)
            if days == '':
                days = 1
            else:
                days = int(days)

            # calculate expiration time
            from datetime import datetime, timedelta
            expire = int((datetime.now() + timedelta(days=days)).timestamp())

            return shorten_filename(fname, md5sum, expire)

    return 'upload file'


@app.route('/<string:short_fname>')
def redirect_short_fname(short_fname): 

    decoded = toBase10(short_fname)

    res = db.query('SELECT filename, md5sum FROM file WHERE id={id}',
                   format(int(decoded)))
    try:
        short = res.fetchone()
        if short is not None:
            fname = base64.b64decode(short[0])
        else:
            return 'link does not exist'
    except Exception as e:
        print(e)

    fname2 = str(fname, "utf-8")

    return send_file('uploads/' + short[1], attachment_filename=fname2,
                     as_attachment=True)


if __name__ == "__main__":
    # create db connection instance
    db = DB("pastebin.db")

    # checks whether database table is created or not
    table_check()

    # run app
    app.run(port=PORT, debug=DEBUG)
