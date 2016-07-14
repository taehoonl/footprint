from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import JsonResponse
from django.views.generic.base import TemplateView
from rest_framework import viewsets
from rest_framework.decorators import api_view
from footprint.models import LivePackets, LogPackets
from footprint.serializers import LivePacketsSerializer, LogPacketsSerializer
from config import config

import logger, collector
import os, pdb, json, time

LOGGER_INSTANCE = None
COLLECTOR_INSTANCE = None
LOG_DIRECTORY = config.get('logger', 'log_directory')

class CoverView(TemplateView):
  template_name = 'cover.html'


class IndexView(TemplateView):
  template_name = 'index.html'


class LivePacketsViewSet(viewsets.ModelViewSet):
  queryset = LivePackets.objects.all()
  serializer_class = LivePacketsSerializer

  def get_all_packets(self, request):
    serializer = self.serializer_class


class LogPacketsViewSet(viewsets.ModelViewSet):
  queryset = LogPackets.objects.all()
  serializer_class = LogPacketsSerializer

  def get_all_packets(self, request):
    serializer = self.serializer_class

@api_view(['GET'])
def get_log_files(request):
  global LOG_DIRECTORY
  files = []
  for f in os.listdir(LOG_DIRECTORY):
    if os.path.isfile(os.path.join(LOG_DIRECTORY, f)):
      files.append(f)

  return JsonResponse({'files': files})

@api_view(['GET'])
def start_collecting_live(request):
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
  response = {}
  try:
    packets = LivePackets.objects.all()
    serializer = LivePacketsSerializer(packets, many=True)
    response['data'] = serializer.data
    LivePackets.objects.all().delete()
    response['success'] = True
    time.sleep(1) # makes the http loading bar look cool
  except Exception as e:
    print e
    response['success'] = False
  return JsonResponse(response)

@api_view(['POST'])
def load_log_packets(request):
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

