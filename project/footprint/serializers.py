from rest_framework import serializers

from footprint.models import LivePackets, LogPackets

class LivePacketsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivePackets
        fields = ('timestamp', 'ip_src', 'ip_dst', 'length', 'ip_protocol', \
                    'ip_from', 'ip_to', 'country_code', 'country_name', \
                    'region_name', 'city_name', 'latitude', 'longitude', 'hostname')

class LogPacketsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogPackets
        fields = ('timestamp', 'ip_src', 'ip_dst', 'length', 'ip_protocol', \
                    'ip_from', 'ip_to', 'country_code', 'country_name', \
                    'region_name', 'city_name', 'latitude', 'longitude', 'hostname')