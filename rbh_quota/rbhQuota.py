#!/usr/bin/env python

import argparse
import re
from sys import exit
import subprocess
from rbh_quota import config
import MySQLdb


def insert():

    parser = argparse.ArgumentParser(description='Creates a QUOTA table in MySQL database and fills it with the Lustre filesystem quotas')
    parser.add_argument(
        '-H', '--host', required=False, action='store', help='Database host name'
    )
    parser.add_argument(
        '-u', '--user', required=False, action='store', help='Database user name'
    )
    parser.add_argument(
        '-x', '--password', required=False, action='store', help='Database password'
    )
    parser.add_argument(
        '-d', '--database', required=False, action='store', help='Database name'
    )

    args = parser.parse_args()

    if args.host:
        DB_HOST = args.host
    else:
        if config.db_host:
            DB_HOST = config.db_host
        else:
            print 'ERROR: missing database host name from config file !'
            exit(1)

    if args.user:
        DB_USER = args.user
    else:
        if config.db_user:
            DB_USER = config.db_user
        else:
            print 'ERROR: missing database user name from config file !'
            exit(1)

    if args.password:
        DB_PWD = args.password
    else:
        if config.db_pwd:
            DB_PWD = config.db_pwd
        else:
            print 'ERROR: missing database password from config file !'
            exit(1)

    if args.database:
        DB = args.database
    else:
        if config.db:
            DB = config.db
        else:
            print 'ERROR: missing database from config file !'
            exit(1)

    try:
        connection = MySQLdb.connect(DB_HOST, DB_USER, DB_PWD, DB)
    except:
        print 'Error: Unable to connect'
        exit(1)
    else:
        db = connection.cursor()

    try:
        db.execute("""SELECT value FROM VARS WHERE varname='FS_Path'""")
    except:
        print 'Error: Query failed to execute'
        exit(1)
    else:
        fs_path = (db.fetchone())[0]

    try:
        db.execute("""DROP TABLE IF EXISTS QUOTA""")
    except:
        print 'Error: Query failed to execute'
        exit(1)

    try:
        db.execute("""CREATE TABLE `QUOTA`
                      (`uid` varchar(127) NOT NULL,
                      `softBlocks` bigint(20) unsigned DEFAULT '0',
                      `hardBlocks` bigint(20) unsigned DEFAULT '0',
                      `softInodes` bigint(20) unsigned DEFAULT '0',
                      `hardInodes` bigint(20) unsigned DEFAULT '0',
                      PRIMARY KEY (`uid`) )""")
    except:
        print 'Error: Query failed to execute'
        exit(1)

    try:
        db.execute("""SELECT DISTINCT(uid) FROM ACCT_STAT""")
    except:
        print 'Error: Query failed to execute'
        exit(1)
    else:
        user = db.fetchone()
        while (user):
            p = subprocess.Popen(["/usr/bin/lfs", "quota", "-u", user[0], fs_path], stdout=subprocess.PIPE)
	    out = p.communicate()[0].replace('\n', ' ')
	    values = re.findall('\s[\d]+\s(?!\(uid)', out)
            #values = re.split("[\s]+", out)
	    print(values)
            #db.execute("INSERT INTO QUOTA VALUES(" + values[0] + ", " + values[1] + ", " + values[2] + ", " + values[3] + ", " + values[4] + ", " + values[5] + ")")
            user = db.fetchone()

    try:
        db.close()
    except:
        print 'Error: Connection to database/carbon server failed to close'
        exit(1)