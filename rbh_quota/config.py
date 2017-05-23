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