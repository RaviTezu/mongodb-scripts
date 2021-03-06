mongodb-scripts
===============

A Collection of mongodb python scripts

Please check the folders in the repo for scripts:

1. mongo-cluster-backup :-
==============================================================
*For taking mongodb cluster backups*
- Connects to mongos host, Collects the configdb hosts and replica sets information(for mongodb hosts). 
- Selects one configdb from the configdb set and one secondary mongodb host from each replica set. 
- Stops the balancer on the monogos host.
- Connects to the selected configdb host, stops the configdb service and runs the mongodbdump for config dbs. Starts the configdb service back once the mongodbdump is completed.
- Connects to all the selected secondary monogdb hosts *simultaneously*(Fabric parallel mode) and stops the mongodb service on the hosts and runs the mongodbdump. Once mongodbdump is completed, starts the monogodb service back. 
- Starts the balancer on the mongos host.

2. mongo-status :-
==============================================================
*For displaying the cluster status*
- Connects to mongos host and collects the shards info. by running sh.status().
- Displays the hosts in shards, and the replicasets.[Plan to include db names and shard key info. in future]
- Connects to replica set members and gets the current state of each host. 
- Displays the status for each replica member. [Node name - Current state - SyncingTo]
- Display the Cluster status. "Needs Attention"/"OK". 
- There's a mogostatus_webcheck sub directory which can provide you with a web url for checking the mongocluster status from your browser.
