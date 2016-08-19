# Footprint

Find out where your internet traffic is coming from. This app shows the locations of your incoming and outgoing internet traffic using open-source IP2LOCATION LITE database

## Features:

**1. Collect, record/log and display live internet IP packet traffic**

**2. Display logged internet IP packet traffic**

**3. Display geolocation info about internet traffic, including**
..* location info,
..* IP range,
..* data transfer amount,
..* IP protocols,
..* associated hostnames,
..* associated IP addresses,
..* and more


## How to start app:

**1. Install dependencies in requirement.txt:**
> ex)

> sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib

> sudo pip install virtualenv django djangorestframework psycopg2 futures dpkt pypcap

Then, install all dependencies in requirement.txt to virtualenv

**2. Change postgresql setting(/etc/postgresql/version/main/pg_hba.conf) to:**

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

**3. Download [IP2LOCATION database](https://lite.ip2location.com/database-ip-country-region-city-latitude-longitude) and place it in data/ip2location folder**

**4. Set 'project_path' and other environment dependent variables as you see fit in main.ini**

**5. Start app using script:**

> python start_app.py