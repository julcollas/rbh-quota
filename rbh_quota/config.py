#!/usr/bin/env python
import ConfigParser
from os.path import expanduser

Config = ConfigParser.ConfigParser()
Config.read(expanduser('~/.rbh-quota.ini'))

try:
    db_host = Config.get('rbh-quota_api', 'db_host')
except:
    db_host = ''

try:
    db_user = Config.get('rbh-quota_api', 'db_user')
except:
    db_user = ''

try:
    db_pwd = Config.get('rbh-quota_api', 'db_pwd')
except:
    db_pwd = ''

try:
    db = Config.get('rbh-quota_api', 'db')
except:
    db = ''

try:
    alerts = Config.get('rbh-quota_api', 'alerts')
except:
    alerts = False

try:
    domain = Config.get('rbh-quota_api', 'domain')
except:
    domain = ''

try:
    server = Config.get('rbh-quota_api', 'smtp_server')
except:
    server = ''

try:
    sender = Config.get('rbh-quota_api', 'sender')
except:
    sender = 'rbh-quota'

try:
    webHost = Config.get('rbh-quota_api', 'webHost')
except:
    webHost = socket.gethostname()
