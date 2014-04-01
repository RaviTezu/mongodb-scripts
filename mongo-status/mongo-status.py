#!/usr/bin/python

##---- SCRIPT TO DISPLAY MONGO CLUSTER STATUS ----##

import pymongo
from ConfigParser import SafeConfigParser

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

##main function:
def main():
    ## config_data.ini file location, as it is in the same directory just the filename is enough. 
    default_config_file = 'config_data.ini'
    parser = SafeConfigParser()
    parser.read(default_config_file)
    mongos_host = parser.get('default', 'mongos_host')
    mongos_port = parser.get('default', 'mongos_port')
    shards_info = mongos_connect(mongos_host, mongos_port)
    print shards_info


if __name__ == '__main__':
    main()

