# Footprint

Find out where your internet traffic is coming from. This app shows the locations of your incoming and outgoing internet traffic using open-source IP2LOCATION LITE database

## How to start app:

**Install dependencies:**

> sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib

> sudo pip install virtualenv django djangorestframework psycopg2 futures dpkt pypcap

> install all dependencies in requirement.txt to virtualenv

**Change postgresql setting:**

change '/etc/postgresql/(version)/main/pg_hba.conf' file

<pre>
  # Database administrative login by Unix domain socket
  local   all             postgres                                trust

  # TYPE  DATABASE        USER            ADDRESS                 METHOD

  # "local" is for Unix domain socket connections only
  local   all             all                                     md5
  # IPv4 local connections:
  host    all             all             127.0.0.1/32            md5
  # IPv6 local connections:
  host    all             all             ::1/128                 md5
</pre>

**Download [IP2LOCATION database](https://lite.ip2location.com/database-ip-country-region-city-latitude-longitude) and place it in data/ip2location folder**

**Set 'project_path' in main.ini**

**Start app using script**

$ python start_app.py