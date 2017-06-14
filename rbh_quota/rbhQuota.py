#!/usr/bin/env python

import argparse
import re
from sys import exit
import subprocess
from email.mime.text import MIMEText
import smtplib
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
    parser.add_argument(
        '-a', '--alerts', required=False, action='store', help='Trigger mail on soft quota'
    )
    parser.add_argument(
        '-m', '--domain', required=False, action='store', help='User mail domain'
    )
    parser.add_argument(
        '-S', '--server', required=False, action='store', help='SMTP server name'
    )
    parser.add_argument(
        '-s', '--sender', required=False, action='store', help='Name used to send mail'
    )
    parser.add_argument(
        '-w', '--webHost', required=False, action='store', help='Host name for the robinhood web interface'
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

    if args.alerts:
        alerts_on = args.alerts
    else:
        if config.alerts:
            alerts_on = config.alerts
        else:
            alerts_on = False

    if alerts_on:
        if args.domain:
            mail_domain = args.domain
        else:
            if config.domain:
                mail_domain = config.domain
            else:
                print 'ERROR: alerts activated but mail domain missing from config file !'
                exit(1)

        if args.server:
            smtp = args.server
        else:
            if config.server:
                smtp = config.server
            else:
                print 'ERROR: alerts activated but SMTP server missing from config file !'
                exit(1)

        if args.sender:
            sender = args.sender
        else:
            if config.sender:
                sender = config.sender

        if args.webHost:
            hostname = args.webHost
        else:
            if config.webHost:
                hostname = config.webHost

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
        db.execute("""SELECT DISTINCT(uid), SUM(size), SUM(count) FROM ACCT_STAT GROUP BY uid""")
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
            except:
                print 'Error: Query failed to execute [Insert into QUOTA table]\n', e[0], e[1]
                exit(1)

            if (alerts_on and values[1] > 0 and user[i][1] >= values[1]):
                msg = MIMEText("Alert on " + fs_path +
                               ":\n\nOwner = " + user[i][0] +
                               "\nCurrent volume used = " + values[0] +
                               "\nSoft volume threshold = " + values[1] +
                               "\nHard volume threshold = " + values[2] +
                               "\n\nYou may be able to free some disk space by deleting unnecessary files." +
                               "\nSee Robinhood web interface here: " + hostname + "/robinhood/?formUID=" + user[i][0] + "#")
                msg['Subject'] = '[Warning] softBlock quota reached'
                msg['From'] = sender + '@' + mail_domain
                msg['To'] = user[i][0] + '@' + mail_domain
                server = smtplib.SMTP(smtp)
                server.sendmail(sender + '@' + mail_domain, user[i][0] + '@' + mail_domain, msg.as_string())
                server.quit()

            if (alerts_on and values[5] > 0 and user[i][1] >= values[5]):
                msg = MIMEText("Alert on " + fs_path +
                               ":\n\nOwner = " + user[i][0] +
                               "\nCurrent inodes used = " + values[0] +
                               "\nSoft inode threshold = " + values[1] +
                               "\nHard inode threshold = " + values[2] +
                               "\n\nYou may be able to free some disk space by deleting unnecessary files." +
                               "\nSee Robinhood web interface here: " + hostname + "/robinhood/?formUID=" + user[i][0] + "#")
                msg['Subject'] = '[Warning] softBlock quota reached'
                msg['From'] = sender + '@' + mail_domain
                msg['To'] = user[i][0] + '@' + mail_domain
                server = smtplib.SMTP(smtp)
                server.sendmail(sender + '@' + mail_domain, user[i][0] + '@' + mail_domain, msg.as_string())
                server.quit()

            i += 1

    try:
        db.close()
    except:
        print 'Error: Connection to database/carbon server failed to close'
        exit(1)
