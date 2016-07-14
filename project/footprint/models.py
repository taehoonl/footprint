from __future__ import unicode_literals

from django.db import models


class IP2Location(models.Model):
    """ """
    ip_from = models.BigIntegerField(primary_key=True, null=False)
    ip_to = models.BigIntegerField(null=False)
    country_code = models.CharField(max_length=2, null=False)
    country_name = models.CharField(max_length=64, null=False)
    region_name = models.CharField(max_length=128, null=False)
    city_name = models.CharField(max_length=128, null=False)
    latitude = models.FloatField(null=False)
    longitude = models.FloatField(null=False)

class ConvertedPackets(models.Model):
    """ """
    timestamp = models.DateTimeField(null=False)
    ip_src = models.BigIntegerField(null=False)
    ip_dst = models.BigIntegerField(null=False)
    ip_len = models.IntegerField(null=False)
    ip_protocol = models.CharField(max_length=8, null=False)
    outbound = models.BooleanField(default=False)

class LivePackets(models.Model):
    """ IP packet model. Stores recently captured packets """

    # packet info
    timestamp = models.DateTimeField(null=False)
    ip_src = models.BigIntegerField(null=False)
    ip_dst = models.BigIntegerField(null=False)
    length = models.IntegerField(null=False)
    ip_protocol = models.CharField(max_length=8, null=False)
    outbound = models.BooleanField(default=False)

    # location info
    ip_from = models.BigIntegerField(null=False)
    ip_to = models.BigIntegerField(null=False)
    country_code = models.CharField(max_length=2, null=False)
    country_name = models.CharField(max_length=64, null=False)
    region_name = models.CharField(max_length=128, null=False)
    city_name = models.CharField(max_length=128, null=False)
    latitude = models.FloatField(null=False)
    longitude = models.FloatField(null=False)

    hostname = models.CharField(max_length=64, null=True)


class LogPackets(models.Model):
    """ IP packet model. Stores logged packets """

    # packet info
    timestamp = models.DateTimeField(null=False)
    ip_src = models.BigIntegerField(null=False)
    ip_dst = models.BigIntegerField(null=False)
    length = models.IntegerField(null=False)
    ip_protocol = models.CharField(max_length=8, null=False)
    outbound = models.BooleanField(default=False)

    # location info
    ip_from = models.BigIntegerField(null=False)
    ip_to = models.BigIntegerField(null=False)
    country_code = models.CharField(max_length=2, null=False)
    country_name = models.CharField(max_length=64, null=False)
    region_name = models.CharField(max_length=128, null=False)
    city_name = models.CharField(max_length=128, null=False)
    latitude = models.FloatField(null=False)
    longitude = models.FloatField(null=False)

    hostname = models.CharField(max_length=64, null=True)
