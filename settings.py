import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # noqa

try:
    with open(os.path.join(BASE_DIR, 'secrets.json')) as f:
        """ parse configuration file """
        secrets = json.loads(f.read())

except FileNotFoundError:
    print('secrets.json not found')
    sys.exit(1)


def get_secret(setting, secrets=secrets):
    """ get the secret variable or return explicit exception. """
    try:
        return secrets[setting]
    except KeyError:
        error_msg = 'Set the {0} environment variable'.format(setting)
        print(error_msg)
        sys.exit(1)


SECRET_KEY = get_secret('SECRET_KEY')
HOST = get_secret('HOST') or "http://localhost:5000"
UPLOAD_FOLDER = os.path.join(BASE_DIR, get_secret('UPLOAD_FOLDER'))
MAX_CONTENT_MB = get_secret('MAX_CONTENT_MB')

# development
PORT = 5000
