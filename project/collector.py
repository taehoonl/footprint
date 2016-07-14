# -*- coding: utf8 -*-

from config import config
from datetime import datetime
import pcap, dpkt
import os, socket, struct
import threading, concurrent.futures, time
import psycopg2
import logger
import util, util_db
import pdb

class Collector:
  """ Collector is a thread that collects and processes network packets
  for application to use

  Collector begins by collecting network packets and converting them
  into readable format. Then groups packets by predetermined criteria,
  looks up location of packet's source IP address and loads processed
  data into application's database.

  Processed data is then logged for future uses
  """
  def __init__(self, logger_instance):
    """ Init

    Args:
        logger_instance (Logger): used to log processed file
    """

    if not logger_instance or not isinstance(logger_instance, logger.Logger):
       raise ValueError('invalid logger instance')

    self._shutdown            = False
    self._signal_refresh      = False

    self._pcap                = None
    self._live_file           = None
    self._pcap_writer         = None
    self._timer               = None
    self.executor             = None
    self.logger               = logger_instance
    self.protocols            = self.__get_ip_protocols()

    # self._local_ip_addr       = self.__get_local_endpoint()
    self._refresh_interval    = int(config.get('collector', 'refresh_interval'))
    self._app_name            = config.get('main', 'app_name')
    self._timestamp_format    = config.get('main', 'timestamp_format')
    self._live_fpath          = config.get('collector', 'live_filepath')
    self._converted_fpath     = config.get('collector', 'converted_filepath')
    self._grouped_fpath       = config.get('collector', 'grouped_filepath')
    self._lookup_fpath        = config.get('collector', 'lookup_filepath')
    self._templog_fpath       = config.get('logger', 'templog_filepath')
    self._db_name             = config.get('database', 'database_name')
    self._db_username         = config.get('database', 'database_username')
    self._app_conv_model      = config.get('app', 'app_converted_model_name')
    self._app_conv_tablename  = self._app_name + '_' + self._app_conv_model
    self._app_live_model      = config.get('app', 'app_live_model_name')
    self._app_live_tablename  = self._app_name + '_' + self._app_live_model

    self.db_conn              = psycopg2.connect(database=self._db_name, \
                                                user=self._db_username)
    self._app_conv_model_col  = util_db.get_columns(self.db_conn, \
                                                self._app_conv_tablename)
    self._app_live_model_col  = util_db.get_columns(self.db_conn, \
                                                  self._app_live_tablename)


  def start(self):
    """ Start collecting IP packets """

    self._shutdown = False
    if self.executor:
      print 'collector already started'
      return

    if not self.executor:
      self.executor = concurrent.futures.ThreadPoolExecutor(1)
      print 'created threadpool for collector'
      t = self.executor.submit(self.__collect_live_packets)


  def shutdown(self):
    """ Shutdown thread """
    self._shutdown = True

    if self._timer:
      self._timer.cancel()

    if self._live_file:
      self._live_file.close()

    if self._pcap_writer:
      self._pcap_writer.close()

    self.executor.shutdown(wait=True)
    self.executor = None
    print '\nshutdown collector %s\n' % str(datetime.now())


  def __collect_live_packets(self):
    """ Main Function:
    Collects network packets, convert them into readable format,
    group packets, matches with location, copy result into db table,
    then logs packets using Logger instance
    """
    while not self._shutdown:
      try:

        # open pcap interface if not open already (req. root accsess)
        if not self._pcap:
          self._pcap = pcap.pcap(promisc=True, immediate=True)
          print 'started capturing packets'

        # open file and set up dpkt writer
        if not self._live_file or not self._pcap_writer:
          self._live_file = open(self._live_fpath, 'wb')
          self._pcap_writer = dpkt.pcap.Writer(self._live_file)

        # signal periodically
        self._signal_refresh = False
        self.__timeout(self._refresh_interval, self.__set_signal_refresh, [])

        for timestamp, packet in self._pcap: # main loop
          if self._shutdown:
            break

          if self._signal_refresh:
            self._signal_refresh = False

            self.__stop_collecting()
            self.__convert_packets(self._live_fpath, \
                                    self._converted_fpath, \
                                    self._app_conv_tablename)
            self.__group_packets(self._grouped_fpath, \
                                    self._app_conv_tablename)
            self.__lookup_packets(self._grouped_fpath, \
                                    self._lookup_fpath, \
                                    self._app_live_tablename)
            os.rename(self._lookup_fpath, self._templog_fpath)
            self.logger.log_file(self._templog_fpath)
            break

          self._pcap_writer.writepkt(packet, timestamp)

      except KeyboardInterrupt:
        self.shutdown()

      except Exception as e:
        print e
        pdb.set_trace()


  def __stop_collecting(self):
    """ Helper Function:
    Stops collecting packets to .pcap file
    """
    nrecv, ndrop, nifdrop = self._pcap.stats()
    print '%d recv \t%d dropped' % (nrecv, ndrop),

    self._pcap_writer.close()
    self._live_file.close()
    self._pcap_writer = None
    self._live_file = None


  def __convert_packets(self, pcap_filepath, output_filepath, tablename):
    """ Helper Function:
    Converts data in .pcap to readable format, outputs converted data
    to file and copy data into database table for further processing.

    *removes .pcap file after processing.

    Args:
        pcap_filepath (string): relative path to .pcap file
        output_filepath (string): relative path to output file
        tablename (string): db tablename to copy data into
    """
    count = nonip_count = 0

    with open(pcap_filepath, 'rb') as pcap_file:
      pcap_lines = dpkt.pcap.Reader(pcap_file)
      with open(output_filepath, 'w') as output_file:
        for ts, buf in pcap_lines:
          timestamp = datetime.fromtimestamp(ts)
          timestamp = timestamp.strftime(self._timestamp_format)
          eth = dpkt.ethernet.Ethernet(buf)

          count += 1
          if eth.type != dpkt.ethernet.ETH_TYPE_IP: # IPv4 only
            nonip_count += 1
            continue

          ip = eth.data

          proto = self.__ip_protocol(int(ip.p))
          ipsrc = self.__ip2intstr(ip.src)
          ipdst = self.__ip2intstr(ip.dst)
          # outbound = str(ipsrc == self._local_ip_addr)
          output_line = '%s,%s,%s,%s,%s\n' % \
                  (timestamp, ipsrc, ipdst, ip.len, proto)
          output_file.write(output_line)

    print '\t%d converted' % (count - nonip_count),

    os.remove(pcap_filepath) # no longer need .pcap file

    util_db.delete_rows(self.db_conn, tablename)
    util_db.copy_from_with_columns(self.db_conn, tablename, \
                                    self._app_conv_model_col[1:], \
                                    output_filepath)

  def __group_packets(self, dst_filepath, tablename):
    """ Helper Function:
    Group packets in table and output grouped result to file

    Args:
        dst_filepath (string): relative path to output file
        tablename (string): db tablename that contains packets
                            data that need grouping
    """
    util_db.group_and_copy_to(self.db_conn, tablename, dst_filepath)


  def __lookup_packets(self, src_filepath, dst_filepath, tablename):
    """ Helper Function:
    Given a file with IP addresses,
        1. look up rDNS and location of IP addr and output result to file
        2. copy file data from previous step into specified database table
    Args:
        src_filepath (string): relative path to file containing
                                data to look up
        dst_filepath (string): relative path to output file
        tablename (string): db tablename to copy look up result into
    """


    util_db.lookup_and_export(self.db_conn, src_filepath, dst_filepath)
    util_db.copy_from_with_columns(self.db_conn, tablename, \
                                      self._app_live_model_col[1:], \
                                      dst_filepath)

  def __ip_protocol(self, proto_num):
    """ Given protocol number, returns str representation of IP protocol """
    if proto_num in self.protocols:
      return self.protocols[proto_num]
    return str(proto_num)


  def __ip2intstr(self, address):
    """ Returns int representation of given IP address as string

        Args:
            address (inet struct): inet network address
    """
    return str(struct.unpack('!I', address)[0])


  def __timeout(self, seconds, func, *args):
    """ Create and start a thread that periodically executes given func

    Args:
        seconds (int): interval to execute func
        func (function): function to execute
        *args (pointer): pointer to arguments for function
    """
    t = threading.Timer(seconds, func, *args)
    self._timer = t
    t.start()

  def __set_signal_refresh(self):
    """ Set refresh signal variable to True """
    self._signal_refresh = True

  def __get_ip_protocols(self):
    """ Returns IP protocols as dict where key is protocol number(int)
        and value is the name(string) of corresponding protocol name
    """
    ip_proto_prefix = 'IPPROTO_'
    return dict((getattr(socket, n), n[len(ip_proto_prefix):]) \
                for n in dir(socket) if n.startswith(ip_proto_prefix))

  # def __get_local_endpoint(self):
  #   """ Returns local endpoint ip address as int string representation """
  #   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  #   s.connect(('google.com',80)) # make a temp connection to site
  #   addr = socket.inet_pton(socket.AF_INET, s.getsockname()[0])
  #   return self.__ip2intstr(addr)
