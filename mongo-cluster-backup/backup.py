#!/usr/bin/python

##---- SCRIPT FOR TAKING MONGODB CLUSTER BACKUP ----##

import pymongo
import os
import os.path
import datetime
from fabric.api import run, settings, execute, task, env

##connect to mongos host: 
def mongos_connect(host, port):
    try:
        connection = pymongo.Connection(host, port)
        db = connection['config']
        collection = db['shards']
        shards = collection.find()
        return shards
    except Exception, e:
        print "Oops! There was an error. Try again..."
        print e


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
        print "Oops! There was an error. Try again..."
        print e

##get config dbs:
def getConfigs():
    configFile = '/etc/mongos.conf'
    if os.path.isfile(configFile):
        f = open(configFile)
        for line in f.readlines():
            if line.startswith('configdb'):
                return line.strip().split()[2].split(',')
        f.close()
    else:
        print "mongos.conf doesn't exist"

#steps to be exexcuted on configdb/mongodb
def data_backup(prefix, data, out, dbtype):
    print "Starting backup for "+ env.host+"..."
    if not data[-1]=='/':
        data = data + '/'
    if not out[-1]=='/':
        out = out + '/'
    if type == "configdb":
        port = '27019'
        dbservice = "/etc/init.d/mongodb-configsvr"
        prefix = "configdbdump" + prefix
    else:
        port = '27017'
        dbservice = "/etc/init.d/mongod"
        prefix = "mongodbdump" + prefix
    #stopping service
    #run('sudo ' +dbservice + ' stop') 
    run(dbservice + ' stop') 
    #run('sudo mkdir ' + out + prefix)
    run('mkdir -p ' + out + prefix)
    command = 'ls ' + data + '| egrep -v "journal|mongod.lock"'
    dbs = os.popen(command).read().split('\n')[:-1]
    for db in dbs:
        run('mongodump --journal --dbpath ' + data + db +' --out ' + out + prefix)
    
    #run('sudo ' +dbservice + ' start')
    run(dbservice + ' start')
    #tar and gzip the backup :P

##backup:
def backup(dblist, bkupdate, sshuser, sshkey, dbdir, dumpdir, dbtype):
    with settings(parallel=True, user=sshuser, key_filename=sshkey):
        execute(data_backup, hosts=dblist, prefix=bkupdate,
                data=dbdir, out=dumpdir, dbtype=dbtype)

##stop balancer
def stopBalancer():
    try:
        connection = pymongo.Connection('localhost', 27020)
        db = connection['config']
        collec = db['settings']
        state = str(collec.find_one({"_id":"balancer"})['stopped'])
        if state == "False":
            collec.update({"_id":"balancer"},{"$set":{"stopped" : True}})
        else: 
            print "Balancer is in stopped state"
    except Exception, e:
        print "Oops! There was an error. Try again..."
        print e

##start balancer
def startBalancer():
    try:
        connection = pymongo.Connection('localhost', 27020)
        db = connection['config']
        collec = db['settings']
        state = str(collec.find_one({"_id":"balancer"})['stopped'])
        if state == "True":
            collec.update({"_id":"balancer"},{"$set":{"stopped" : False}})
        else: 
            print "Balancer is already running.."
    except Exception, e:
        print "Oops! There was an error. Try again..."
        print e

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
    for k,v in reps.iteritems():
        print k +" : "+v

##get secondary nodes from each replica set
secondaries = []
def getSecondary(rset):
    for host in rset.split(','):
        secondary = isPrimary(host)
        if secondary:
           secondaries.append(secondary)
           break
    

## main function:  
def main():
    #get the mongos info here and connect to mongos for shards info.
    #For now, I'm using localhost and 27020
    #sshuser, sshkey, dbpath, dumppath has to be initialized here. 
    sshuser   = 'mongod'
    sshkey    = '/var/lib/mongo/.ssh/identity'
    dumppath  = '/var/tmp/mongo-backups/'
    configdbs = getConfigs()
    shards_info = mongos_connect('localhost', 27020)
    rsets = getReplicas(shards_info)
    printReplicas(rsets)
    for rs in rsets.values():
        getSecondary(rs)
    #print secondaries 
    #print "Selected secondaries for backup: ", secondaries
    #print "Configdb for backup: ", configdbs[0].split(':')[0]
    #configdbs -- config dbs list
    #secondaries -- secondary node list
    today = datetime.datetime.now()
    backup_date = str(today.strftime("%Y-%m-%d-%H:%M"))
    #configdb backup
    stopBalancer()
    dbtype = "configdb"
    dbpath = "/var/lib/mongodb-config"
    backup(configdbs[0].split(':')[0], backup_date, sshuser, sshkey, dbpath, dumppath, dbtype)
    #mongodb backup
    type = "mongodb"
    dbpath = "/var/lib/mongodb"
    backup(secondaries, backup_date, sshuser, sshkey, dbpath, dumppath, dbtype)
    startBalancer()

if __name__ == '__main__':
    main()

