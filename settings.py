import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # noqa

with open('secrets.json') as f:
    """ parse configuration file """
    secrets = json.loads(f.read())

    def get_secret(setting, secrets=secrets):
        """ get the secret variable or return explicit exception. """
        try:
            return secrets[setting]
        except KeyError:
            error_msg = 'Set the {0} environment variable'.format(setting)
            print(error_msg)
