from rest_framework import serializers

from footprint.models import IP2Location, LivePackets, LogPackets

class IP2LocationSerializer(serializers.ModelSerializer):
  class Meta:
    model = IP2Location
    fields = (  'ip_from', 'ip_to', 'country_code', 'country_name', 'region_name', \
                'city_name', 'latitude', 'longitude')


class LivePacketsSerializer(serializers.ModelSerializer):
  class Meta:
    model = LivePackets
    fields = (  'timestamp', 'ip_src', 'ip_dst', 'length', 'ip_protocol', \
                'src_ip_from', 'src_ip_to', 'src_country_code', 'src_country_name', \
                'src_region_name', 'src_city_name', 'src_latitude', 'src_longitude', \
                'dst_ip_from', 'dst_ip_to', 'dst_country_code', 'dst_country_name', \
                'dst_region_name', 'dst_city_name', 'dst_latitude', 'dst_longitude', \
                'hostname')

class LogPacketsSerializer(serializers.ModelSerializer):
  class Meta:
    model = LogPackets
    fields = (  'timestamp', 'ip_src', 'ip_dst', 'length', 'ip_protocol', \
                'src_ip_from', 'src_ip_to', 'src_country_code', 'src_country_name', \
                'src_region_name', 'src_city_name', 'src_latitude', 'src_longitude', \
                'dst_ip_from', 'dst_ip_to', 'dst_country_code', 'dst_country_name', \
                'dst_region_name', 'dst_city_name', 'dst_latitude', 'dst_longitude', \
                'hostname')