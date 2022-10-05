import os

BASE_DIR = os.path.dirname(__file__)

SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'forum.db'))
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "&^t=$4p$i+u2nn^@43v0dt4ek93=t3i)7wvatm$@_&!&dhwx(("