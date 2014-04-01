#!/usr/bin/python

##---- SCRIPT TO DISPLAY MONGO CLUSTER STATUS ----##

import pymongo
import os
from ConfigParser import SafeConfigParser

##Get the terminal width, height
rows, columns = os.popen('stty size', 'r').read().split()

##connect to mongos host:
def mongos_connect(host, port):
    try:
        client = pymongo.MongoClient(host, port)
        db = client.config
        collection = db.shards
        shards = collection.find()
        return shards
    except Exception, e:
        print "Unable to connect to the mongo host"
        print e

##connect to mongod host:
def mongod_connect(host, port):
    

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
    print "\n" + "------------------ SHARDS INFORMATION ------------------".center(int(columns),'-') + "\n"
    for k, v in sorted(reps.iteritems()):
        print k + " : " + v + "\n"
    print "-"*int(columns) + "\n"

##main function:
def main():
    ## config_data.ini file location, as it is in the same directory just the filename is enough. 
    default_config_file = 'config_data.ini'
    parser = SafeConfigParser()
    parser.read(default_config_file)
    mongos_host = str(parser.get('default', 'mongos_host'))
    mongos_port = int(parser.get('default', 'mongos_port'))
    shards_info = mongos_connect(mongos_host, mongos_port)
    #get replica sets info.
    rsets = getReplicas(shards_info)
    printReplicas(rsets)
    for rs in rsets.values():
    


if __name__ == '__main__':
    main()

