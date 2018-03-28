Usage
-----

```Text
This script creates a backup of a Wordpress Blog instance.

It generates a compressed tar archive containing a dump
of the wordpress database and a copy of the wordpress filesystem.

positional arguments:
  path                 path to wordpress instance

optional arguments:
  -h, --help           show this help message and exit
  -v, --verbose        enable log messages
  -d, --debug          enable debug messages
  -q, --quiet          do not print status messages
  --dry                perform dry run: do not store or delete any archives
  --database           backup wordpress database
  --filesystem         backup wordpress filesystem
  --thinning STRATEGY  thin out backups at targets (except local target) using
                       the specified strategy

database backup options:

  --db NAME            name for wordpress db
  --dbhost HOST        hostname for wordpress db
  --dbport PORT        portnumber for wordpress db
  --dbuser USER        username for wordpress db
  --dbpass PASS        password for wordpress db
  --dbprefix PREFIX    prefix for table names in wordpress db

local target:
  options for storing the backup archive on local filesystem

  --attic [DIR]        local directory to store backup archive

s3 target:
  options for copying the backup archive to a s3 service

  --s3 HOST            host for s3 server
  --s3accesskey KEY    access key for s3 server
  --s3secretkey KEY    secret key for s3 server
  --s3bucket BUCKET    bucket at s3 server

report options:

  --mail-from MAIL     sender address for report mails
  --mail-to-admin      send report to wordpress administrator
  --mail-to MAIL       recipient address for report mails

This script will try to load the wordpress configuration file at
the given path and read the database configuration for the given
wordpress instance from that file.

The database parameters from the configuration file can be overwritten
by specifing the correspondent command line options.
```

Requirements
------------

  * Python 3
  * PyMySQL (MIT) - https://github.com/PyMySQL/PyMySQL
  * boto (MIT) - https://github.com/boto/boto
  * dateutil (BSD) - https://github.com/dateutil/dateutil
  * humanfriendly (MIT) - https://github.com/xolox/python-humanfriendly
  * coloredlogs (MIT) - https://github.com/xolox/python-coloredlogs
