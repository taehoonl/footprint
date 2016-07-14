# -*- coding: utf8 -*-

from config import config
import util_db
import os, psycopg2, pdb, time

# config
app_name = config.get('main', 'app_name')
project_path = config.get('main', 'project_path')
dev_server_ipaddr = config.get('main', 'dev_server_ipaddr')
db_name = config.get('database', 'database_name')
db_username = config.get('database', 'database_username')

ip2loc_modelname = config.get('app', 'app_ip2loc_model_name')
ip2loc_tablename = app_name + '_' + ip2loc_modelname
converted_modelname = config.get('app', 'app_converted_model_name')
converted_tablename = app_name + '_' + converted_modelname

ip2loc_filepath = config.get('database', 'ip2location_filepath')
ip2loc_filepath_abs = os.path.join(project_path, ip2loc_filepath)


# helper funcs
def create_database():
	""" Create PostgreSQL db via command line
	"""
	command ='sudo su %s psql -c "createdb %s;"' % (db_username, db_name)

	print '\n' + command
	r = os.system(command)

	if r != 0:
		raise Exception('Failed to create database: %s' % db_name)


# main
def start():
	conn = None
	cursor = None

	# db exists
	try:
		conn = psycopg2.connect(database=db_name, user=db_username)
	except psycopg2.OperationalError: # database doesn't exist
		try:
			create_database()
			conn = psycopg2.connect(database=db_name, user=db_username)
		except Exception as e:
			print e

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
	try:
		r = start()
	except (KeyboardInterrupt, Exception) as e:
		print e
		kill_command = "sudo kill $(ps aux | grep 'python manage.py runserver' | awk '{print $2}')"
		print kill_command
		os.system(kill_command)





'''
def init_ip2location_table():
	""" Copy csv data(directly) into ip to location db table via command line
	"""
	copy_command = \
	"""psql -d %s -U %s -c "COPY %s 
		FROM '%s' 
		WITH DELIMITER ',' QUOTE AS '\\"' CSV" """ \
	% (db_name, db_username, ip2loc_tablename, ip2loc_filepath_abs)

	print '\n' + copy_command
	r = os.system(copy_command)

	if r != 0:
		raise Exception('Failed to copy "%s" into table: %s' \
						% (ip2loc_filepath_abs, ip2loc_tablename))

def create_ip2location_table():
	""" Create ip to location db table via command line. Table columns 
		correspond to columns in ip2location_filepath in config (main.ini)
	"""
	create_command = \
		"""psql -d %s -U %s -c "CREATE TABLE %s(
			ip_from bigint NOT NULL,
			ip_to bigint NOT NULL,
			country_code character(2) NOT NULL,
			country_name character varying(64) NOT NULL,
			region_name character varying(128) NOT NULL,
			city_name character varying(128) NOT NULL,
			latitude real NOT NULL,
			longitude real NOT NULL,
			CONSTRAINT %s_pkey PRIMARY KEY (ip_from, ip_to));" """ \
		% (db_name, db_username, ip2loc_tablename, ip2loc_tablename)

	print '\n' + create_command
	r = os.system(create_command)

	if r != 0:
		raise Exception('Failed to create table: %s' % ip2loc_tablename)


def create_temp_table(tablename):
	""" Create temporary db table used by Collector and Logger. Table columns
		corresponds to columns written in Collector
	"""
	create_command = \
		"""psql -d %s -U %s -c "CREATE TABLE %s(
			timestamp timestamp NOT NULL,
			ip_src bigint NOT NULL,
			ip_dst bigint NOT NULL,
			ip_len int NOT NULL,
			ip_protocol character varying(8));" """ \
		% (db_name, db_username, tablename)

	print '\n' + create_command
	r = os.system(create_command)

	if r != 0:
		raise Exception('Failed to create table: %s' % tablename)

def create_full_table(tablename):
	""" Create db table used by Collector and Logger. Table columns correspond
		to columns of App models
	"""
	create_command = \
		"""psql -d %s -U %s -c "CREATE TABLE %s(
			timestamp timestamp NOT NULL,
			ip_src bigint NOT NULL,
			ip_dst bigint NOT NULL,
			ip_len int NOT NULL,
			ip_protocol character varying(8),
			ip_from bigint NOT NULL,
			ip_to bigint NOT NULL,
			country_code character(2) NOT NULL,
			country_name character varying(64) NOT NULL,
			region_name character varying(128) NOT NULL,
			city_name character varying(128) NOT NULL,
			latitude real NOT NULL,
			longitude real NOT NULL);" """ \
		% (db_name, db_username, tablename)

	print '\n' + create_command
	r = os.system(create_command)

	if r != 0:
		raise Exception('Failed to create table: %s' % tablename)

create table location (
loc_id integer PRIMARY KEY,
country character(2) NOT NULL,
region character varying(128) NOT NULL,
city character varying(128) NOT NULL,
postal_code character varying(12) NOT NULL,
latitude real NOT NULL,
longitude real NOT NULL,
metro_code integer,
area_code integer );

copy location from 
'/home/john/Desktop/project_ip_getaway/project/data/ip2location/GeoLiteCity-Location-utf8.csv' 
WITH CSV DELIMITER ',' QUOTE AS '"';


create table ip2location_geolite (
ip_from bigint NOT NULL,
ip_to bigint NOT NULL,
loc_id integer references location(loc_id),
CONSTRAINT ip2location_geolite_pkey PRIMARY KEY (ip_from, ip_to)
);


copy ip2location_geolite from 
'/home/john/Desktop/project_ip_getaway/project/data/ip2location/GeoLiteCity-Blocks-utf8.csv' 
WITH CSV DELIMITER ',' QUOTE AS '"';

	# # ip2location table exists
	# try:
	# 	cursor = conn.cursor()
	# 	cursor.execute("SELECT COUNT(*) FROM %s" % ip2loc_tablename)
	# except Exception as e:
	# 	create_ip2location_table()
	# 	init_ip2location_table()

	# # converted/grouped table exists
	# for t_name in [converted_tablename]:
	# 	try:
	# 		cursor.execute("SELECT COUNT(*) FROM %s" % t_name)
	# 	except Exception as e:
	# 		create_temp_table(t_name)

	# # live/log table exists
	# for t_name in [live_tablename, log_tablename]:
	# 	try:
	# 		cursor.execute("SELECT COUNT(*) FROM %s" % t_name)
	# 	except Exception as e:
	# 		create_full_table(t_name)

"""
'''