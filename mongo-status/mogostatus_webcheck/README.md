Mongo cluster status script (web support): 
===============================================

**Note: Please refer to the requirements.txt file before using this script**

- This script extends the funtionality of the mongo-status.py by providing a web url.
- This script has been successfully tested with the module versions mentioned in the requirements.txt file. 
- Check config_data.ini and put in your mongos hostname and port number. 
- Feel free to open issues, if you feel a particular area in the script requires more improvement. 
- This scirpt needs apache to be running and a .conf for allowing the access to webstatus page. 
- Example .conf file: 
```
user@machine01:/etc/httpd/conf.d $ cat mongostatus.conf
Alias /mongostatus /var/www/mongostatus

<Directory "/var/www/mongostatus">
   Options Indexes FollowSymLinks
   AllowOverride None
   Order allow,deny
   Allow from all
</Directory>
```
-  You can use a cron to run this script:


This is [alpha](http://www.3am.pair.com/beta.html) quality software and released under [MIT](http://opensource.org/licenses/MIT) license

