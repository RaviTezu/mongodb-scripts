#!/usr/bin/python

##---- SCRIPT FOR TAKING MONGODB BACKUPS ----##

import os
import pymongo
import smtplib
import logging
import datetime
from ConfigParser import SafeConfigParser
from fabric.api import run, settings, execute, task, env

## config_data.ini file location, as it is in the same directory just the filename is enough. 
default_config_file = 'config_data.ini'
parser = SafeConfigParser()
parser.read(default_config_file)

#Parse the values
sshuser = parser.get('default', 'sshuser')
sshkey = parser.get('default', 'sshkey')
configdb_dbpath = parser.get('default', 'configdb_dbpath') 
mongodb_dbpath = parser.get('default', 'mongodb_dbpath')
dumppath = parser.get('default', 'dumppath')
logfile = parser.get('default', 'logfile')
mongos_host = parser.get('default', 'mongos_host')
mongos_port = parser.get('default', 'mongos_port')
mongos_configfile = parser.get('default', 'mongos_configfile')

##For storing selected secondary hosts for backup.
secondaries = []

##Code for logging
logger = logging.getLogger(sshuser)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(logfile)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Starting mongo backups script on %s", mongos_host)

##Mail sender/receiver list:
sender = "mongod@" + mongos_host
receivers = ['user1@example.com', 'user2@example.com']


##send a mail:
def sendmail():
    fh = open(logfile)
    message = "Subject: FAILED: MongoDB backup on one or more hosts" + "\n" + fh.read()
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receivers, message)
    except:
        logger.error("Unable to send email")


##connect to mongos host:
def mongos_connect(host, port):
    try:
        connection = pymongo.Connection(host, port)
        db = connection['config']
        collection = db['shards']
        shards = collection.find()
        return shards
    except Exception, e:
        logger.error("Oops! Unable to connect to %s on %d", host, port)
        logger.error(str(e))
        sendmail()
        exit(1)


##connect to mongo nodes
def isPrimary(mongodhost):
    host = mongodhost.split(':')[0]
    port = int(mongodhost.split(':')[1])
    try:
        connection = pymongo.Connection(host, port)
        db = connection['test']
        check = db.command('isMaster')
        is_primary = str((check['ismaster']))
        is_secondary = str((check['secondary']))
        if is_primary != "True" and is_secondary == "True":
            return host
        else:
            return ''
    except Exception, e:
        logger.error("Oops! Unable to connect to %s on %d", host, port)
        logger.error(str(e))
        sendmail()
        exit(1)


##get config dbs:
def getConfigs():
    if os.path.isfile(mongos_configfile):
        f = open(mongos_configfile)
        for line in f.readlines():
            if line.startswith('configdb'):
                return line.strip().split()[2].split(',')
        f.close()
    else:
        logger.error("%s file doesn't exist on %s", mongos_configfile, mongos_host)
        sendmail()
        exit(1)


##steps to be exexcuted on configdb/mongodb
def data_backup(prefix, data, out, dbtype):
    try:
        if not data[-1] == '/':
            data = data + '/'
        if not out[-1] == '/':
            out = out + '/'
        if dbtype == "configdb":
            dbservice = "/etc/init.d/mongodb-configsvr"
            prefix = "configdbdump" + prefix
            logger.info("Starting configdb backup on %s", env.host)
        else:
            dbservice = "/etc/init.d/mongod"
            prefix = "mongodbdump" + prefix
            logger.info("Starting mongodb backup on %s", env.host)
        logger.info("Stopping %s service on %s", dbservice.split('/')[3], env.host)
        run(dbservice + ' stop')
        run('mkdir -p ' + out + prefix)
        command = 'ls ' + data + '| egrep -v "journal|mongod.lock"'
        dbs = os.popen(command).read().split('\n')[:-1]
        for db in dbs:
            run('mongodump --journal --dbpath ' + data + db + ' --out ' + out +
                prefix)
        logger.info("Successfully completed %s backup on %s", dbtype, env.host)
        logger.info("Starting %s service on %s", dbservice.split('/')[3], env.host)
    except Exception, e:
        logger.error("%s backup failed on %s", dbtype, env.host)
    finally:
        run(dbservice + ' start')


##backup:
def backup(dblist, bkupdate, sshuser, sshkey, dbdir, dumpdir, db_type):
    with settings(parallel=True, user=sshuser, key_filename=sshkey):
        execute(data_backup, hosts=dblist, prefix=bkupdate,
                data=dbdir, out=dumpdir, dbtype=db_type)


##stop balancer
def stopBalancer():
    try:
        connection = pymongo.Connection(mongos_host, mongos_port)
        db = connection['config']
        collec = db['settings']
        state = str(collec.find_one({"_id": "balancer"})['stopped'])
        if state == "False":
            logger.info("Stopping balancer on %s", mongos_host)
            collec.update({"_id": "balancer"}, {"$set": {"stopped": True}})
        else:
            logger.warn("Balancer is already in stopped state on %s", mongos_host)
    except Exception, e:
        logger.error("Oops! Unable to stop balancer on %s", mongos_host)
        logger.error(str(e))
        sendmail()
        exit(1)


##start balancer
def startBalancer():
    try:
        connection = pymongo.Connection(mongos_host, mongos_port)
        db = connection['config']
        collec = db['settings']
        state = str(collec.find_one({"_id": "balancer"})['stopped'])
        if state == "True":
            logger.info("Starting balacer on %s", mongos_host)
            collec.update({"_id": "balancer"}, {"$set": {"stopped": False}})
        else:
            logger.info("Balancer is already in running state on %s", mongos_host)
    except Exception, e:
        logger.error("Oops! Unable to start balancer on %s", mongos_host)
        logger.error(str(e))
        sendmail()
        exit(1)


##grep replica sets from shards_info
def getReplicas(shards):
    replicas = {}
    for rs in shards:
        rs_name = rs['_id']
        rs_mems = rs['host'].split('/')[1]
        replicas[rs_name] = rs_mems
    return replicas


##prints replica sets:
def printReplicas(reps):
    for k, v in reps.iteritems():
        logger.info(k + " : " + v)


##select secondary nodes for backup
def getSecondary(rset):
    for host in rset.split(','):
        secondary = isPrimary(host)
        if secondary:
            secondaries.append(secondary)
            break


##main function:
def main():
    configdbs = getConfigs()
    shards_info = mongos_connect(mongos_host, mongos_port)
    rsets = getReplicas(shards_info)
    printReplicas(rsets)
    for rs in rsets.values():
        getSecondary(rs)
    logger.info("Selected secondary node(s) for backup: %s", secondaries)
    logger.info("Selected configdb node(s) for backup: %s", configdbs[0].split(':')[0])
    today = datetime.datetime.now()
    backup_date = str(today.strftime("%Y-%m-%d-%H:%M"))
    stopBalancer()
    try:
        #configdb backup
        dbtype = "configdb"
        backup(configdbs[0].split(':')[0], backup_date, sshuser, sshkey, configdb_dbpath, dumppath, dbtype)
        #mongodb backup
        dbtype = "mongodb"
        backup(secondaries, backup_date, sshuser, sshkey, mongodb_dbpath, dumppath, dbtype)
    finally:
        startBalancer()


if __name__ == '__main__':
    main()

