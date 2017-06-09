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
    except MySQLdb.Error, e:
        print 'Error: Unable to connect to database\n', e[0], e[1]
        exit(1)
    else:
        db = connection.cursor()

    try:
        db.execute("""SELECT value FROM VARS WHERE varname='FS_Path'""")
    except MySQLdb.Error, e:
        print 'Error: Query failed to execute [Retrieving FS_PATH]\n', e[0], e[1]
        exit(1)
    else:
        fs_path = (db.fetchone())[0]

    try:
        db.execute("""DROP TABLE IF EXISTS QUOTA""")
    except MySQLdb.Error, e:
        print 'Error: Query failed to execute [Drop QUOTA table]\n', e[0], e[1]
        exit(1)

    try:
        db.execute("""CREATE TABLE `QUOTA`
                      (`owner` varchar(127) NOT NULL,
                      `softBlocks` bigint(20) unsigned DEFAULT '0',
                      `hardBlocks` bigint(20) unsigned DEFAULT '0',
                      `softInodes` bigint(20) unsigned DEFAULT '0',
                      `hardInodes` bigint(20) unsigned DEFAULT '0',
                      PRIMARY KEY (`owner`) )""")
    except MySQLdb.Error, e:
        print 'Error: Query failed to execute [Create QUOTA table]', e[0], e[1]
        exit(1)

    try:
        db.execute("""SELECT DISTINCT(uid) FROM ACCT_STAT""")
    except MySQLdb.Error, e:
        print 'Error: Query failed to execute [Retrieve uid]\n', e[0], e[1]
        exit(1)
    else:
        user = db.fetchall()
        i = 0
        while (i < len(user)):
            p = subprocess.Popen(["lfs", "quota", "-u", user[i][0], fs_path], stdout=subprocess.PIPE)
            out = p.communicate()[0].replace('\n', ' ')
            values = re.findall('([\d]+|\-)\s(?![(]uid)', out)
	    try:
                db.execute("INSERT INTO QUOTA VALUES('" + user[i][0] +
                           "', " + values[1] + ", " + values[2] +
                           ", " + values[5] + ", " + values[6] + ")")
	    except MySQLdb.Error, e:
		print 'Error: Query failed to execute [Insert into QUOTA table]\n', e[0], e[1]
        	exit(1)

            i += 1

    try:
        db.close()
    except:
        print 'Error: Connection to database/carbon server failed to close'
        exit(1)
