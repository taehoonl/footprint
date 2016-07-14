# -*- coding: utf8 -*-

from config import config
from datetime import datetime
import os, psycopg2, socket, signal, pdb


# config
app_name            = config.get('main', 'app_name')
project_path        = config.get('main', 'project_path')
converted_filepath  = config.get('collector', 'converted_filepath')
db_name             = config.get('database', 'database_name')
db_username         = config.get('database', 'database_username')
ip2loc_modelname    = config.get('app', 'app_ip2loc_model_name')
ip2loc_tablename    = app_name + '_' + ip2loc_modelname

# sql queries
GROUP_PACKET_QUERY      = """SELECT timestamp, ip_src, ip_dst, SUM(ip_len), ip_protocol, outbound
                            FROM %s
                            GROUP BY timestamp, ip_src, ip_dst, ip_protocol, outbound
                            ORDER BY timestamp ASC"""
LOOKUP_LOCATION_QUERY   = """SELECT * FROM %s
                            WHERE ip_from <= %s
                            ORDER BY ip_from DESC LIMIT 1"""
COPY_FROM_QUERY         = """COPY %s FROM '%s'
                            WITH CSV DELIMITER ',' QUOTE AS '"' """
COPY_FROM_QUERY_W_COLS  = """COPY %s (%s) FROM '%s'
                            WITH CSV DELIMITER ',' QUOTE AS '"' """
COPY_TO_QUERY           = """COPY (%s) TO STDOUT
                            WITH CSV DELIMITER ',' QUOTE AS '"' """
INSERT_INTO_QUERY       = """INSERT INTO %s SELECT * FROM %s"""
ROW_COUNT_QUERY         = """SELECT COUNT(*) FROM %s"""
GET_COLUMNS_QUERY       = """SELECT * FROM %s LIMIT 0"""
DELETE_QUERY            = """DELETE FROM %s"""



def quotify(s):
  """ Returns str representation of arg with double quotes around it """
  return '"%s"' % str(s)

def is_bool(s):
  """ Return True if s is a string representation of True """
  return s.lower() in ['t', 'true']

def reverse_dns(ip_addr):
  """ Return hostname of IPv4 address. Returns empty string if fails """
  name = ''
  try:
    name, alias, address_list = socket.gethostbyaddr(ip_addr)
  except Exception as e:
    pass
  return name



def lookup_and_export(db_conn, src_filepath, dst_filepath):
  """ Cross matches packet's IP address with corresponding IP block,
  look up hostname of IP address, then writes the result to file
  with IP block info added to the original info

  Args:
      db_conn (psycopg2 database connection): database connection
      src_filepath (string): relative path to csv file with
              IP addresses(as the second column) to match
      dst_filepath (string): relative path to output file
  """
  db_cursor = None
  count = 0

  try:
    db_cursor = db_conn.cursor()
    f_src_path = os.path.join(project_path, src_filepath)
    f_dst_path = os.path.join(project_path, dst_filepath)

    with open(f_src_path, 'r') as f_src, open(f_dst_path, 'w') as f_dst:
      for line in f_src:
        columns = line.strip().split(',')
        ip_src = columns[1]     # packet source ip address
        ip_dst = columns[2]     # packet destination ip address
        outbound = is_bool(columns[5])  # True if packet is outbound
        endpoint = ip_dst if outbound else ip_src
        hostname = reverse_dns(endpoint) # reverse DNS hostname

        lookup_query = LOOKUP_LOCATION_QUERY % (ip2loc_tablename, endpoint)
        db_cursor.execute(lookup_query)
        result = db_cursor.fetchone()

        columns.extend(list(result))
        columns.append(hostname)
        columns = map(quotify, columns)
        columns = ','.join(columns) + '\n'
        f_dst.write(columns)

        count += 1

    print '\t%d lookup' % count

  except Exception as e:
    print e
    pdb.set_trace()

  finally:
    if db_cursor:
      db_cursor.close()


def group_and_copy_to(db_conn, tablename, filepath):
  """ Groups packets in database table by criteria specified in query,
  then outputs the result to given filepath

  Args:
      db_conn (psycopg2 database connection): database connection
      tablename (string): name of db table to apply group query
      filepath (string): relative path to output file
  """
  db_cursor = None
  try:
    db_cursor = db_conn.cursor()
    filepath_abs = os.path.join(project_path, filepath)

    group_query = GROUP_PACKET_QUERY % tablename
    copyto_query = COPY_TO_QUERY % (group_query)

    with open(filepath_abs, 'w') as f:
      db_cursor.copy_expert(copyto_query, f)
      db_conn.commit()

  except Exception as e:
    print e
    pdb.set_trace()

  finally:
    if db_cursor:
      db_cursor.close()


def delete_rows(db_conn, tablename):
  """ Delete all rows of given tablename

  Args:
      db_conn (psycopg2 database connection): database connection
      tablename (string): name of db table to delete rows from
  """
  db_cursor = None
  try:
    db_cursor = db_conn.cursor()
    db_cursor.execute(DELETE_QUERY % tablename)
    db_conn.commit()
  except Exception as e:
    print e
    pdb.set_trace()

  finally:
    if db_cursor:
      db_cursor.close()


def copy_from(db_conn, tablename, filepath):
  """ Directly imports csv file into table using 'COPY FROM' query

  Args:
      db_conn (psycopg2 database connection): database connection
      tablename (string): name of db table to copy data into
      filepath (string): relative path to csv file to copy data from
  """
  db_cursor = None
  result = True
  filepath_abs = os.path.join(project_path, filepath)

  try:
    db_cursor = db_conn.cursor()
    filepath_abs = os.path.join(project_path, filepath)

    copyfrom_query = COPY_FROM_QUERY % (tablename, filepath_abs)

    with open(filepath_abs, 'r') as f:
      db_cursor.copy_expert(copyfrom_query, f)
      db_conn.commit()

  except Exception as e:
    result = False
    print e
    pdb.set_trace()

  finally:
    if db_cursor:
      db_cursor.close()

  return result


def copy_from_with_columns(db_conn, tablename, columns, filepath):
  """ Directly imports csv file into table using 'COPY FROM' query
  with specified columns

  Args:
      db_conn (psycopg2 database connection): database connection
      tablename (string): name of db table to copy data into
      columns (list of strings): list of column names
      filepath (string): relative path to csv file to copy data from
  """
  db_cursor = None
  filepath_abs = os.path.join(project_path, filepath)

  try:
    db_cursor = db_conn.cursor()
    filepath_abs = os.path.join(project_path, filepath)
    columns_str = ','.join(columns)

    copyfromcols_query = COPY_FROM_QUERY_W_COLS \
                        % (tablename, columns_str, filepath_abs)

    with open(filepath_abs, 'r') as f:
      db_cursor.copy_expert(copyfromcols_query, f)
      db_conn.commit()

  except Exception as e:
    print e
    pdb.set_trace()

  finally:
    if db_cursor:
      db_cursor.close()


def get_columns(db_conn, tablename):
  """ Returns column names of specified database table as list

  *returns empty list if it fails

  Args:
      db_conn (psycopg2 database connection): database connection
      tablename (string): name of db table to get column names from
  """
  db_cursor = None
  column_names = []
  try:
    db_cursor = db_conn.cursor()

    db_cursor.execute(GET_COLUMNS_QUERY % tablename)
    column_names = [desc[0] for desc in db_cursor.description]

  except Exception as e:
    print e

  finally:
    if db_cursor:
      db_cursor.close()

  return column_names


def get_row_count(db_conn, tablename):
  """ Returns number of rows in table. -1 if fails

  Args:
      db_conn (psycopg2 database connection): database connection
      tablename (string): name of db table to get row count
  """
  row_count = -1
  db_cursor = None
  try:
    db_cursor = db_conn.cursor()

    db_cursor.execute(ROW_COUNT_QUERY % tablename)
    row_count = db_cursor.fetchone()[0]

  except Exception as e:
    print e

  finally:
    if db_cursor:
      db_cursor.close()

  return row_count



# init
# signal.signal(signal.SIGALRM, signal_handler)
# def signal_handler(signum, frame):
#   raise Exception('timeout: signal handler')
# con = psycopg2.connect(database='footprint_db', user='postgres')

# starttime = datetime.now()
# cur = con.cursor()
# # # lookup_and_export(con, 'data/log/2016-07-04-17.csv', 'data/lookup.csv')
# # # delete_rows(con, live_temp_tablename)
# # copy_from(con, 'live_packets', 'data/log/2016-07-05-17.csv')

# get_row_count(con, 'ip2location')

# endtime = datetime.now()
# print str(endtime - starttime)
