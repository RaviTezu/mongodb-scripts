#!/usr/bin/python

##---- SCRIPT TO DISPLAY MONGO CLUSTER STATUS ----##

import pymongo
import os
import sys
from time import sleep
from ConfigParser import SafeConfigParser

##Get the terminal width, height
rows, columns = os.popen('stty size', 'r').read().split()

##Colors
Red = '\033[31m'
Green = '\033[32m'
Yellow = '\033[33m'
Blue = '\033[34m'
Cyan = '\033[36m'
RedB = '\033[41m'
GreenB = '\033[42m'
YellowB = '\033[43m'
BlueB = '\033[44m'
CyanB = '\033[46m'
WhiteB = '\033[47m'
end = '\033[0m'

##HEALTH CHECK
health = []


##connect to mongos host:
def mongos_connect(host, port):
    try:
        client = pymongo.Connection(host, port)
        db = client.config
        collection = db.shards
        shards = collection.find()
        return shards
    except Exception:
        pass


##connect to mongod host:
def mongod_connect(host, port):
    try:
        client = pymongo.Connection(host, port)
        db = client.admin
        cmd = db.command('replSetGetStatus')
        return cmd
    except Exception, e:
        print "Unable to connect to the mongo host"
        print e


##get Shards info:
def getShards(shards):
    shs = {}
    for rs in shards:
        rs_name = rs['_id']
        rs_mems = rs['host'].split('/')[1]
        shs[rs_name] = rs_mems
    return shs


##prints Shards:
def printShards(sh_info, html):
    print "\n" + Cyan + "------------------ SHARDS INFORMATION ------------------".center(int(columns), '-') + end + "\n"
    html.write("-------------------------------------------------------------- SHARDS INFORMATION -------------------------------------------------------------- <br> \n")
    for k, v in sorted(sh_info.iteritems()):
        print Red + k + end + " : " + v + "\n"
        html.write(k + " : " + v +"\n")
    


##get Replica info:
def getReplicas(rsets, html):
    print "\n" + Cyan + "------------------ REPLICA SETS INFORMATION ------------------".center(int(columns), '-') + end + "\n"
    html.write("<br>----------------------------------------------------------- REPLICA SETS INFORMATION ----------------------------------------------------------- \n")
    sync = {}
    for k, v in sorted(rsets.iteritems()):
        rss = {}
        print k + ":"
        html.write(k + ": \n" )
        for host in v.split(','):
            h, p = host.split(':')
            info = {}
            info = mongod_connect(h, int(p))
            if info != None:
                if 'syncingTo' in info:
                    sync[host] = info['syncingTo']
            elif'errmsg' in info['members'][0]:
                sync[host] = info['members'][0]['errmsg']
            else:
                sync[host] = host
                for x in (info['members']):
                    rss[x['name']] = x['stateStr']
                max1 = max(len(x) for x in rss)
        for k1, v1 in sorted(rss.iteritems()):
            if v1 == "PRIMARY":
                state = GreenB + v1 + end
            elif v1 == "SECONDARY":
                state = CyanB + v1 + end
            elif v1 == "ARBITER":
                state = YellowB + v1 + end
            else:
                state = RedB + v1 + end
                health.append(k1.split(':')[0])
            print Red + '{0:<45}'.format(k1.split(':')[0]) + " : " + end + '{0:<35}'.format(state) + Cyan + "SyncingTo :" + sync.get(k1, "---") + end
            html.write('{0:<45}'.format(k1.split(':')[0]) + " : "   + '{0:<35}'.format(v1) + "SyncingTo :" + sync.get(k1, "---")+ "\n")  
        print "\n"
        html.write("<br>")


##main function:
def main():
    ## config_data.ini file location, as it is in the same directory
    ## just the filename is enough.
    default_config_file = 'config_data2.ini'
    parser = SafeConfigParser()
    parser.read(default_config_file)
    mongos_host = str(parser.get('default', 'mongos_host'))
    mongos_port = int(parser.get('default', 'mongos_port'))
    html_file   = str(parser.get('default', 'html_file'))
    html = open(html_file,'wb') 
    html.write("<html><body><pre>")
    shards_info = mongos_connect(mongos_host, mongos_port)
    shards = getShards(shards_info)
    printShards(shards, html)
    getReplicas(shards, html)
    if len(health) > 0:
        print "CLUSTER HEALTH: Degraded "
        html.write("CLUSTER HEALTH: Degraded \n")
        print "\n" + "The following hosts needs some Attention: "+ "\n" + BlueB + ", ".join(health) + end + "\n"
        html.write("The following hosts needs some Attention: " + ", ".join(health) + "\n")
    else:
        print "CLUSTER HEALTH: OK"
        html.write("CLUSTER HEALTH: OK \n")
    print "\n" + Cyan + "-"*int(columns) + end + "\n"
    html.write("------------------------------------------------------------------------------------------------------------------------------------------------ \n")
    html.write("</pre></body></html>")
    html.close()


if __name__ == '__main__':
    main()

