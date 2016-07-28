# -*- coding: utf8 -*-

from config import config
from datetime import datetime
import os, threading, concurrent.futures
import util, util_db
import psycopg2

import pdb

class Logger:
  """ Logger is a thread that logs packet data collected by Collector. 

      Given
  """
  def __init__(self):
    self.executor       = concurrent.futures.ThreadPoolExecutor(1)

    self._open_files    = {}

    self._app_name      = config.get('main', 'app_name')
    self._project_path    = config.get('main', 'project_path')
    self._timestamp_format  = config.get('main', 'timestamp_format')
    self._log_directory   = config.get('logger', 'log_directory')
    self._log_fname_format  = config.get('logger', 'log_filename_format')
    self._db_name       = config.get('database', 'database_name')
    self._db_username     = config.get('database', 'database_username')
    self._app_log_model   = config.get('app', 'app_log_model_name')
    self._app_log_tablename = self._app_name + '_' + self._app_log_model

    self.db_conn      = psycopg2.connect(database=self._db_name, \
                          user=self._db_username)
    self._app_log_model_col = util_db.get_columns(self.db_conn, \
                          self._app_log_tablename)

  def log_file(self, filepath):
    """ Given log file, process each row by copying each row into 
        appropriate log file. 
        Assigns this task to threadpool.
    """
    future = self.executor.submit(self.__partition_log_file, filepath)
    r = future.result()
    if not r:
      print 'FAILED: logging target file(%s)' % filepath
    else:
      os.remove(filepath)
      # print '\tlogged target file(%s)' % filepath

  def copy_file_into_model(self, filename):
    """ Copies given file into LogPackets model.
        Assigns this task to threadpool
    """
    future = self.executor.submit(self.__copy_file_into_model, filename)
    r = future.result()
    return r

  def __copy_file_into_model(self, filename):
    """ Copies given file into LogPackets model.
        Returns true if successful. Otherwise, false
      Args:
        filename(String): name of file to copy data from
    """
    try:
      filepath = os.path.join(self._project_path, \
                  self._log_directory, filename)

      # check if file exists
      if not os.path.exists(filepath) or not os.path.isfile(filepath):
        raise Exception('not a valid file: %s' % filepath)

      # load file into log model after deleting all rows
      util_db.delete_rows(self.db_conn, self._app_log_tablename)
      util_db.copy_from_with_columns(self.db_conn, \
                      self._app_log_tablename, \
                      self._app_log_model_col[1:], \
                      filepath)
      return True

    except Exception as e:
      print e
      return False


  def __partition_log_file(self, filepath):
    """ Given file to process, copy each row of file into appropriate
        log file based on timestamp. 
        Returns true if successful. Otherwise, false
      Args:
        filepath(String): path to file to process
    """
    try:
      filepath_abs = os.path.join(self._project_path, filepath)

      with open(filepath_abs, 'r') as log_file:
        content = log_file.readlines()
        for line in content:
          timestamp = line.split(',')[0].strip('"').split('+')[0]
          dst_filepath = self.__timestamp_to_filepath(timestamp)

          if not dst_filepath in self._open_files:
            util.check_and_create_filepath(dst_filepath)
            self._open_files[dst_filepath] = open(dst_filepath, 'a')

          self._open_files[dst_filepath].write(line)

      self.__close_open_files()
      return True

    except Exception as e:
      print 'FAILED: partitioning log file ', e
      return False

  def __close_open_files(self):
    """ Close all open files that Logger has access to """
    for (fpath, fopen) in self._open_files.iteritems():
      try:
        fopen.close()
      except Exception as e:
        print 'failed to close %s' % fpath
        print e
        continue
    self._open_files.clear()

  def __timestamp_to_filepath(self, timestamp_str):
    """ Given timestamp, returns full path to file that timestamp belong to
      Args:
        timestamp_str(String): timestamp string

    """
    filename = 'invalid_timestamp.log'
    try:
      timestamp = datetime.strptime(timestamp_str, self._timestamp_format)
      year = timestamp.strftime('%Y')
      month = timestamp.strftime('%m')
      day = timestamp.strftime('%d')
      hour = timestamp.strftime('%H')

      filename = self._log_fname_format % (year, month, day, hour)
    except Exception as e:
      print e

    return os.path.join(self._log_directory, filename)