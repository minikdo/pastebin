import os
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from sqlite3 import OperationalError

from hashlib import md5
from time import time, ctime
from urllib.parse import urljoin

from db import DB
from settings import (BASE_DIR, SECRET_KEY, UPLOAD_FOLDER,
                      MAX_CONTENT_MB, HOST, PORT)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_MB * 1024 * 1024

db = DB("pastebin.db")  # FIXME: for production


def table_check():
    """ create db table """

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


table_check()  # FIXME: for production


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


@app.route('/' + SECRET_KEY + '/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'no file part', 400  # HTTP Bad Request

        file = request.files['file']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return 'no selected file', 400  # HTTP Bad Request

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

            force = request.form.get('force', 0)
            force = bool(int(force))

            # check if file exists by hash and print out existing files
            if file_exists(md5sum) and not force:
                os.remove(filename)
                res = db.query("""
                               SELECT id, link, filename, expire FROM file
                               WHERE md5sum = ?
                               """, [md5sum])

                rows = res.fetchall()
                output = []

                for row in rows:
                    output.append((row[0], urljoin(HOST, row[1]), row[2],
                                   ctime(row[3])))

                from tabulate import tabulate
                headers = ['id', 'url', 'filename', 'expiration time']

                return f'{tabulate(output, headers=headers)}', 409  # Conflict

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

            # create url token
            from secrets import token_urlsafe
            link = token_urlsafe(8)

            res = db.query('''INSERT INTO file (filename, link, md5sum, expire)
                           VALUES (?,?,?,?)''',
                           [fname, link, md5sum, expire])

            return urljoin(HOST, link)

    return 'upload a file'


@app.route('/<string:link>')
def download_file(link):

    q = db.query('SELECT filename, md5sum FROM file WHERE link=?',
                 (link,))

    res = q.fetchone()

    if res is None:
        return '404: no file', 404, {'Content-Type': 'text/plain'}
    else:
        filename, md5sum = res

        return send_file(os.path.join(BASE_DIR, 'uploads', md5sum),
                         attachment_filename=filename,
                         as_attachment=True)


if __name__ == "__main__":
    # create db connection instance
    db = DB(os.path.join(BASE_DIR, "pastebin.db"))

    # checks whether database table is created or not
    table_check()

    # run app
    app.run(port=PORT, debug=True)
