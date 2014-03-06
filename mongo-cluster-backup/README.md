Mongo cluster backup script: 
============================

**Note: Please refer to the requirements.txt file before using this script**

- This script has been successfully tested with the module versions mentioned in the requirements.txt file. 
- *pymongo.Connection()* is replaced with *mongo_client* in the newer versions of [pymongo](http://api.mongodb.org/python/current/api/pymongo/).
- "Fabric" dumps all the output to the stdout, so make sure to redirect to it to a file.  
- This script uses the localhost mailagent to send mail on failure.
- The config_data.ini file has one section([default]), and the script by get the options from the default section only. You can add more sections to it if you need. 

This is [alpha](http://www.3am.pair.com/beta.html) quality software and released under [MIT](http://opensource.org/licenses/MIT) license.
