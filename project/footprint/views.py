from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import JsonResponse
from django.views.generic.base import TemplateView
from rest_framework import viewsets
from rest_framework.decorators import api_view
from footprint.models import *
from footprint.serializers import *
from config import config

import logger, collector
import os, pdb, json, time, socket, struct

LOGGER_INSTANCE = None # logger
COLLECTOR_INSTANCE = None # collector
LOG_DIRECTORY = config.get('logger', 'log_directory')
LOOKUP_LOCATION_QUERY = """SELECT * FROM %s
                          WHERE ip_from <= %s
                          ORDER BY ip_from DESC LIMIT 1"""
IP2LOCATION_TABLENAME = config.get('main', 'app_name') + '_' \
                        + config.get('app', 'app_ip2loc_model_name')


class CoverView(TemplateView):
  template_name = 'cover.html'


class IndexView(TemplateView):
  template_name = 'index.html'

class LivePacketsViewSet(viewsets.ModelViewSet):
  """ REST framework serializer for LivePackets model """
  queryset = LivePackets.objects.all()
  serializer_class = LivePacketsSerializer

  def get_all_packets(self, request):
    serializer = self.serializer_class

class LogPacketsViewSet(viewsets.ModelViewSet):
  """ REST framework serializer for LogPackets model """
  queryset = LogPackets.objects.all()
  serializer_class = LogPacketsSerializer

  def get_all_packets(self, request):
    serializer = self.serializer_class

@api_view(['GET'])
def get_log_files(request):
  """ Returns list of log files in log directory
    Args:
      request(http): default http request object
  """
  global LOG_DIRECTORY
  files = []
  for f in os.listdir(LOG_DIRECTORY):
    if os.path.isfile(os.path.join(LOG_DIRECTORY, f)):
      files.append(f)

  return JsonResponse({'files': files})

@api_view(['GET'])
def start_collecting_live(request):
  """ Start collector instance to capture packets. 
      Returns true if successfully starts instance. Otherwise, false
  """
  global COLLECTOR_INSTANCE
  global LOGGER_INSTANCE

  success = True
  try:
    if not LOGGER_INSTANCE or LOGGER_INSTANCE is None:
      LOGGER_INSTANCE = logger.Logger()

    if not COLLECTOR_INSTANCE or COLLECTOR_INSTANCE is None:
      COLLECTOR_INSTANCE = collector.Collector(LOGGER_INSTANCE)

    COLLECTOR_INSTANCE.start()
  except Exception as e:
    print e
    success = False

  return JsonResponse({'success': success})

@api_view(['GET'])
def stop_collecting_live(request):
  """ Stop collector instance from capturing packets 
      Returns true if successfully stops instance. Otherwise, false
  """
  global COLLECTOR_INSTANCE
  success = True
  try:
    if not COLLECTOR_INSTANCE or COLLECTOR_INSTANCE is None:
      return JsonResponse({'success': success})

    COLLECTOR_INSTANCE.shutdown() # blocks
    del COLLECTOR_INSTANCE
    COLLECTOR_INSTANCE = None

  except Exception as e:
    print e
    success = False

  return JsonResponse({'success': success})

@api_view(['GET'])
def take_all_live_packets(request):
  """ Returns all records in LivePackets model and then deletes all records.
      Also returns true if successfully returns all records. Otherwise, false
  """
  response = {}
  try:
    packets = LivePackets.objects.all()
    serializer = LivePacketsSerializer(packets, many=True)
    response['data'] = serializer.data
    LivePackets.objects.all().delete()
    response['success'] = True
    time.sleep(0.1) # makes the http loading bar look cool
  except Exception as e:
    print e
    response['success'] = False
  return JsonResponse(response)

@api_view(['POST'])
def load_log_packets(request):
  """ Loads given log file into LogPackets model and returns all records.
      Also returns true if successfully returns all records. Otherwise, false
  """

  global LOGGER_INSTANCE
  response = {}
  try:
    if not LOGGER_INSTANCE or LOGGER_INSTANCE is None:
      LOGGER_INSTANCE = logger.Logger()

    filename = str(json.loads(request.body).get('filename'))
    result = LOGGER_INSTANCE.copy_file_into_model(filename)

    if not result:
      raise Exception('failed: logger copy file into model')

    packets = LogPackets.objects.all()
    serializer = LogPacketsSerializer(packets, many=True)
    response['data'] = serializer.data
    response['success'] = True
  except Exception as e:
    print e
    response['success'] = False
  return JsonResponse(response)


@api_view(['POST'])
def search_ip_address(request):
  """ Searches given IP address on IP2Location model. 
      Returns IP2Location model record. Also returns true if successfully 
      returns search result. Otherwise, false
    Args:
      request(http post): contains 'ipaddress'
  """

  global LOOKUP_LOCATION_QUERY
  response = {}

  try:
    ipaddr = ip2int(str(json.loads(request.body).get('ipaddress')))
    query = LOOKUP_LOCATION_QUERY % (IP2LOCATION_TABLENAME, ipaddr)
    location = IP2Location.objects.raw(query)
    serializer = IP2LocationSerializer(location[0], many=False)
    response['data'] = serializer.data
    response['success'] = True
  except Exception as e:
    print e
    response['success'] = False

  return JsonResponse(response)

def ip2int(addr):
  """ Returns int representation of given IP address """
  return struct.unpack("!I", socket.inet_aton(addr))[0]