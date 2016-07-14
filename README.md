# footprint

install dependencies

1. sudo apt-get install python-pip python-dev libpq-dev postgresql postgresql-contrib
2. sudo pip install virtualenv django djangorestframework psycopg2 futures dpkt pypcap
3. install all dependencies in requirement.txt to virtualenv

change postgresql setting

1. change '/etc/postgresql/(version)/main/pg_hba.conf' file

    # Database administrative login by Unix domain socket
    local   all             postgres                                trust

    # TYPE  DATABASE        USER            ADDRESS                 METHOD

    # "local" is for Unix domain socket connections only
    local   all             all                                     md5
    # IPv4 local connections:
    host    all             all             127.0.0.1/32            md5
    # IPv6 local connections:
    host    all             all             ::1/128                 md5