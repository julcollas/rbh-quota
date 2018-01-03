#!/usr/bin/env python

import argparse
import re
from sys import exit
from subprocess import Popen, PIPE
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
        '-a', '--alerts', required=False, action='store_true', help='Trigger mail on soft quota'
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
        '-c', '--copy', required=False, action='store', help='Recipient for mail copy'
    )
    parser.add_argument(
        '-w', '--webHost', required=False, action='store', help='Host name for the robinhood web interface'
    )
    parser.add_argument(
        '-t', '--fsType', required=False, action='store', help='Filesystem type'
    )
    parser.add_argument(
        '--verbose', required=False, action='store_true', help='Output steps detail to stdout'
    )
    parser.add_argument(
        '--dry-run', required=False, action='store_true', help='Executes command without sending mail or updating QUOTA table'
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

    if args.verbose:
        print("DB_HOST: %s" % DB_HOST)

    if args.user:
        DB_USER = args.user
    else:
        if config.db_user:
            DB_USER = config.db_user
        else:
            print 'ERROR: missing database user name from config file !'
            exit(1)

    if args.verbose:
        print("DB_USER: %s" % DB_USER)

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

    if args.verbose:
        print("DATABASE: %s" % DB)

    if args.fsType:
        FS_TYPE = args.fsType
    else:
        if config.fsType:
            FS_TYPE = config.fsType
        else:
            print 'ERROR: missing filesystem type from config file !'
            exit(1)

    if args.alerts:
        alerts_on = args.alerts
    else:
        if config.alerts:
            alerts_on = config.alerts
        else:
            alerts_on = False

    if args.verbose:
        print("ALERTS: %s" % alerts_on)

    if alerts_on:
        if args.domain:
            mail_domain = str(args.domain)
        else:
            if config.domain:
                mail_domain = str(config.domain)
            else:
                print 'ERROR: alerts activated but mail domain missing from config file !'
                exit(1)

        if args.verbose:
            print("MAIL DOMAIN: %s" % mail_domain)

        if args.server:
            smtp = args.server
        else:
            if config.server:
                smtp = config.server
            else:
                print 'ERROR: alerts activated but SMTP server missing from config file !'
                exit(1)

        if args.verbose:
            print("SMTP SERVER: %s" % smtp)

        if args.sender:
            sender = str(args.sender)
        else:
            if config.sender:
                sender = str(config.sender)

        if args.verbose:
            print("SENDER: %s" % sender)

        if args.copy:
            copy = str(args.copy)
        else:
            if config.copy:
                copy = str(config.copy)

        if args.verbose:
            print("CC: %s" % copy)

        if args.webHost:
            hostname = str(args.webHost)
        else:
            if config.webHost:
                hostname = str(config.webHost)

        if args.verbose:
            print("WEB HOST NAME: %s" % hostname)

    try:
        connection = MySQLdb.connect(DB_HOST, DB_USER, DB_PWD, DB)
        if args.verbose:
            print '\nConnecting to %s as %s@%s (using password:%s)' % (DB, DB_USER, DB_HOST, 'YES' if DB_PWD else 'NO')
    except MySQLdb.Error, e:
        print 'Error: Unable to connect to database\n', e[0], e[1]
        exit(1)
    else:
        db = connection.cursor()

    try:
        db.execute("""SELECT value FROM VARS WHERE varname='FS_Path'""")
        if args.verbose:
            print("\nexecute => SELECT value FROM VARS WHERE varname='FS_Path'")
    except MySQLdb.Error, e:
        print 'Error: Query failed to execute [Retrieving FS_PATH]\n', e[0], e[1]
        exit(1)
    else:
        fs_path = (db.fetchone())[0]
        if args.verbose:
            print 'fs_path: %s' % fs_path

    try:
        if not args.dry_run:
            db.execute("""DROP TABLE IF EXISTS QUOTA""")
        if args.verbose:
            print("\nexecute => DROP TABLE IF EXISTS QUOTA")
    except MySQLdb.Error, e:
        print 'Error: Query failed to execute [Drop QUOTA table]\n', e[0], e[1]
        exit(1)

    try:
        if not args.dry_run:
            db.execute("""CREATE TABLE `QUOTA`
                          (`owner` varchar(127) NOT NULL,
                          `softBlocks` bigint(20) unsigned DEFAULT '0',
                          `hardBlocks` bigint(20) unsigned DEFAULT '0',
                          `softInodes` bigint(20) unsigned DEFAULT '0',
                          `hardInodes` bigint(20) unsigned DEFAULT '0',
                          PRIMARY KEY (`owner`) )""")
        if args.verbose:
            print("\nexecute => CREATE TABLE `QUOTA`\n" +
                  "(`owner` varchar(127) NOT NULL,\n" +
                  "   `softBlocks` bigint(20) unsigned DEFAULT '0',\n" +
                  "   `hardBlocks` bigint(20) unsigned DEFAULT '0',\n" +
                  "   `softInodes` bigint(20) unsigned DEFAULT '0',\n" +
                  "   `hardInodes` bigint(20) unsigned DEFAULT '0',\n" +
                  "   PRIMARY KEY (`owner`) )")
    except MySQLdb.Error, e:
        print 'Error: Query failed to execute [Create QUOTA table]', e[0], e[1]
        exit(1)

#########################################
#        For lustre filesystem          #
#########################################

    if FS_TYPE == "lustre":
        try:
            db.execute("""SELECT DISTINCT(uid) FROM ACCT_STAT GROUP BY uid""")
            if args.verbose:
                print("\nexecute => SELECT DISTINCT(uid) FROM ACCT_STAT GROUP BY uid")
        except MySQLdb.Error, e:
            print 'Error: Query failed to execute [Retrieve uid]\n', e[0], e[1]
            exit(1)
        else:
            user = db.fetchall()
            if args.verbose:
                print(user)
            i = 0
            while (i < len(user)):

                p = Popen(["lfs", "quota", "-q", "-u", user[i][0], fs_path], stdout=PIPE)
                out = p.communicate()[0].replace('\n', ' ')
                if args.verbose:
                    print '=======================\nexecute => lfs quota -u %s %s' % (user[i][0], fs_path)
                if p.returncode != 0:
                    print 'Error: Command failed to execute [lfs quota]\n'
                    exit(1)

                if args.verbose:
                    print('\n%s' % out)

                values = [x.replace('*', '') for x in out.split()[1:]]

                if args.verbose:
                    print("[Owner] %s - [softBlocks] %s - [hardBlocks] %s - [softInodes] %s - [hardInodes] %s" % (user[i][0], values[1], values[2], values[5], values[6]))

                try:
                    if not args.dry_run:
                        db.execute("INSERT INTO QUOTA VALUES('%s', %s, %s, %s, %s)" % (user[i][0], values[1], values[2], values[5], values[6]))
                    if args.verbose:
                        print("\nexecute => INSERT INTO QUOTA VALUES('%s', %s, %s, %s, %s)\n" % (user[i][0], values[1], values[2], values[5], values[6]))
                except MySQLdb.Error, e:
                    print 'Error: Query failed to execute [Insert into QUOTA table]\n', e[0], e[1]
                    exit(1)

                if (alerts_on and int(values[1]) > 0 and int(values[0]) >= int(values[1])):
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
                    msg['CC'] = copy + '@' + mail_domain
                    if args.verbose:
                        print(msg)
                    server = smtplib.SMTP(smtp)
                    if not args.dry_run:
                        server.sendmail(sender + '@' + mail_domain, [msg['To']] + [msg['CC']], msg.as_string())
                    server.quit()

                if (alerts_on and int(values[5]) > 0 and int(values[4]) >= int(values[5])):
                    msg = MIMEText("Alert on " + fs_path +
                                   ":\n\nOwner = " + user[i][0] +
                                   "\nCurrent inodes used = " + values[4] +
                                   "\nSoft inode threshold = " + values[5] +
                                   "\nHard inode threshold = " + values[6] +
                                   "\n\nYou may be able to free some disk space by deleting unnecessary files." +
                                   "\nSee Robinhood web interface here: " + hostname + "/robinhood/?formUID=" + user[i][0] + "#")
                    msg['Subject'] = '[Warning] softInode quota reached'
                    msg['From'] = sender + '@' + mail_domain
                    msg['To'] = user[i][0] + '@' + mail_domain
                    msg['CC'] = copy + '@' + mail_domain
                    if args.verbose:
                        print(msg)
                    server = smtplib.SMTP(smtp)
                    if not args.dry_run:
                        server.sendmail(sender + '@' + mail_domain, [msg['To']] + [msg['CC']], msg.as_string())
                    server.quit()

                i += 1

#########################################
#         For ext4 filesystem           #
#########################################

    if FS_TYPE == "ext4":
        p = Popen(["repquota", "-u", fs_path], stdout=PIPE)
        out = p.communicate()[0]
        if args.verbose:
            print '=======================\nexecute => repquota -u %s' % fs_path

        if p.returncode != 0:
            print 'Error: Command failed to execute [repquota]\n'
            exit(1)

        if args.verbose:
            print('\n%s' % out)

        values = re.findall('([-a-zA-Z0-9_]+)\s+(?:\-|\+){2}\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9a-z]+)?' +
                            '\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+([0-9a-z]+))?(?:$|\s+)', out)

        if args.verbose:
            print values

        i = 0
        while (i < len(values)):
            try:
                if not args.dry_run:
                    db.execute("INSERT INTO QUOTA VALUES('%s', %s, %s, %s, %s)\n" % (values[i][0], values[i][2], values[i][3], values[i][6], values[i][7]))
                if args.verbose:
                    print("\nexecute => INSERT INTO QUOTA VALUES('%s', %s, %s, %s, %s)\n" % (values[i][0], values[i][2], values[i][3], values[i][6], values[i][7]))
            except MySQLdb.Error, e:
                    print 'Error: Query failed to execute [Insert into QUOTA table]\n', e[0], e[1]
                    exit(1)

            if (alerts_on and int(values[i][2]) > 0 and int(values[i][1]) >= int(values[i][2])):
                msg = MIMEText("Alert on " + fs_path +
                               ":\n\nOwner = " + values[i][0] +
                               "\nCurrent volume used = " + values[i][1] +
                               "\nSoft volume threshold = " + values[i][2] +
                               "\nHard volume threshold = " + values[i][3] +
                               "\n\nYou may be able to free some disk space by deleting unnecessary files." +
                               "\nSee Robinhood web interface here: " + hostname + "/robinhood/?formUID=" + values[i][0] + "#")
                msg['Subject'] = '[Warning] softBlock quota reached'
                msg['From'] = sender + '@' + mail_domain
                msg['To'] = values[i][0] + '@' + mail_domain
                msg['CC'] = copy + '@' + mail_domain
                if args.verbose:
                    print(msg)
                server = smtplib.SMTP(smtp)
                if not args.dry_run:
                    server.sendmail(sender + '@' + mail_domain, [msg['To']] + [msg['CC']], msg.as_string())
                server.quit()

            if (alerts_on and int(values[i][6]) > 0 and int(values[i][5]) >= int(values[i][6])):
                msg = MIMEText("Alert on " + fs_path +
                               ":\n\nOwner = " + values[i][0] +
                               "\nCurrent inodes used = " + values[i][5] +
                               "\nSoft inode threshold = " + values[i][6] +
                               "\nHard inode threshold = " + values[i][7] +
                               "\n\nYou may be able to free some disk space by deleting unnecessary files." +
                               "\nSee Robinhood web interface here: " + hostname + "/robinhood/?formUID=" + values[i][0] + "#")
                msg['Subject'] = '[Warning] softInode quota reached'
                msg['From'] = sender + '@' + mail_domain
                msg['To'] = values[i][0] + '@' + mail_domain
                msg['CC'] = copy + '@' + mail_domain
                if args.verbose:
                    print(msg)
                server = smtplib.SMTP(smtp)
                if not args.dry_run:
                    server.sendmail(sender + '@' + mail_domain, [msg['To']] + [msg['CC']], msg.as_string())
                server.quit()

            i += 1

#########################################
#          For xfs filesystem           #
#########################################

    if FS_TYPE == "xfs":
        p = Popen(["xfs_quota", "-x", "-c", "report -u -ib", fs_path], stdout=PIPE)
        out = p.communicate()[0]
        if args.verbose:
            print '=======================\nexecute => xfs_quota -x -c \'report -ib -u\' %s' % fs_path

        if p.returncode != 0:
            print 'Error: Command failed to execute [xfs_quota]\n'
            exit(1)

        if args.verbose:
            print('\n%s' % out)

        values = re.findall('([-a-zA-Z0-9_]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+\[(?:\-{8}|([0-9a-z\s]+)|\-\-none\-\-)]\s+(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+\[(?:\-{8}|([0-9a-z\s]+)|\-\-none\-\-)\]', out)

        if args.verbose:
            print values

        i = 0
        while (i < len(values)):
            try:
                if not args.dry_run:
                    db.execute("INSERT INTO QUOTA VALUES('%s', %s, %s, %s, %s)\n" % (values[i][0], values[i][2], values[i][3], values[i][6], values[i][7]))
                if args.verbose:
                    print("\nexecute => INSERT INTO QUOTA VALUES('%s', %s, %s, %s, %s)\n" % (values[i][0], values[i][2], values[i][3], values[i][6], values[i][7]))
            except MySQLdb.Error, e:
                    print 'Error: Query failed to execute [Insert into QUOTA table]\n', e[0], e[1]
                    exit(1)

            if (alerts_on and int(values[i][2]) > 0 and int(values[i][1]) >= int(values[i][2])):
                msg = MIMEText("Alert on " + fs_path +
                               ":\n\nOwner = " + values[i][0] +
                               "\nCurrent volume used = " + values[i][1] +
                               "\nSoft volume threshold = " + values[i][2] +
                               "\nHard volume threshold = " + values[i][3] +
                               "\n\nYou may be able to free some disk space by deleting unnecessary files." +
                               "\nSee Robinhood web interface here: " + hostname + "/robinhood/?formUID=" + values[i][0] + "#")
                msg['Subject'] = '[Warning] softBlock quota reached'
                msg['From'] = sender + '@' + mail_domain
                msg['To'] = values[i][0] + '@' + mail_domain
                msg['CC'] = copy + '@' + mail_domain
                if args.verbose:
                    print(msg)
                server = smtplib.SMTP(smtp)
                if not args.dry_run:
                    server.sendmail(sender + '@' + mail_domain, [msg['To']] + [msg['CC']], msg.as_string())
                server.quit()

            if (alerts_on and int(values[i][6]) > 0 and int(values[i][5]) >= int(values[i][6])):
                msg = MIMEText("Alert on " + fs_path +
                               ":\n\nOwner = " + values[i][0] +
                               "\nCurrent inodes used = " + values[i][5] +
                               "\nSoft inode threshold = " + values[i][6] +
                               "\nHard inode threshold = " + values[i][7] +
                               "\n\nYou may be able to free some disk space by deleting unnecessary files." +
                               "\nSee Robinhood web interface here: " + hostname + "/robinhood/?formUID=" + values[i][0] + "#")
                msg['Subject'] = '[Warning] softInode quota reached'
                msg['From'] = sender + '@' + mail_domain
                msg['To'] = values[i][0] + '@' + mail_domain
                msg['CC'] = copy + '@' + mail_domain
                if args.verbose:
                    print(msg)
                server = smtplib.SMTP(smtp)
                if not args.dry_run:
                    server.sendmail(sender + '@' + mail_domain, [msg['To']] + [msg['CC']], msg.as_string())
                server.quit()

            i += 1

    try:
        db.close()
        if args.verbose:
            print("\nClosing connection to MySQL database")
    except:
        print 'Error: Connection to database/carbon server failed to close'
        exit(1)
