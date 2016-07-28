# -*- coding: utf8 -*-

from config import config
import util_db
import os, psycopg2, pdb, time

# config
app_name            = config.get('main', 'app_name')
project_path        = config.get('main', 'project_path')
dev_server_ipaddr   = config.get('main', 'dev_server_ipaddr')
db_name             = config.get('database', 'database_name')
db_username         = config.get('database', 'database_username')

ip2loc_modelname    = config.get('app', 'app_ip2loc_model_name')
ip2loc_tablename    = app_name + '_' + ip2loc_modelname
converted_modelname = config.get('app', 'app_converted_model_name')
converted_tablename = app_name + '_' + converted_modelname

ip2loc_filepath     = config.get('database', 'ip2location_filepath')
ip2loc_filepath_abs = os.path.join(project_path, ip2loc_filepath)


# helper funcs
def create_database():
  """ Create PostgreSQL db via command line """
  command ='sudo su %s psql -c "createdb %s;"' % (db_username, db_name)

  print '\n' + command
  r = os.system(command)

  if r != 0:
    raise Exception('Failed to create database: %s' % db_name)


# main
def start():
  conn = None

  # db exists
  try:
    conn = psycopg2.connect(database=db_name, user=db_username)
  except psycopg2.OperationalError: # database doesn't exist
    try:
      create_database()
      conn = psycopg2.connect(database=db_name, user=db_username)
    except Exception as e:
      print e
      return False

  # migrate
  makemigrations_cmd = 'python manage.py makemigrations ' + app_name
  print '\n' + makemigrations_cmd
  os.system(makemigrations_cmd)

  migrate_cmd = 'python manage.py migrate'
  print '\n' + migrate_cmd
  os.system(migrate_cmd)

  # add ip2location data if necessary
  if util_db.get_row_count(conn, ip2loc_tablename) == 0:
    print '\nCopying "%s" data into database table "%s"' \
                        % (ip2loc_filepath, ip2loc_tablename)
    r = util_db.copy_from(conn, ip2loc_tablename, ip2loc_filepath_abs)
    if not r:
      print 'Failed to copy ip2location data'
      return False

  # start development server
  runserver_cmd = 'sudo python manage.py runserver %s' % dev_server_ipaddr
  print '\n' + runserver_cmd
  r = os.system(runserver_cmd)
  print r

  return True

# main
if __name__ == '__main__':
  kill_command = "sudo kill -9 $(ps aux | grep 'python manage.py runserver' | awk '{print $2}')"
  try:
    print kill_command
    os.system(kill_command) # kill existing runserver
    r = start()
  except (KeyboardInterrupt, Exception) as e:
    print e
    print kill_command
    os.system(kill_command)