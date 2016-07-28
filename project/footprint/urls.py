from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from footprint.views import *

router = DefaultRouter()
router.register(prefix='livepackets', viewset=LivePacketsViewSet)
router.register(prefix='logpackets', viewset=LogPacketsViewSet)

urlpatterns = [
    url(r'^$', CoverView.as_view(), name='coverview'),
    url(r'^get_log_files/', get_log_files),
    url(r'^start_collecting/', start_collecting_live),
    url(r'^stop_collecting/', stop_collecting_live),
    url(r'^take_all_live_packets/', take_all_live_packets),
    url(r'^load_log_packets/', load_log_packets),
    url(r'^search_ip_address/', search_ip_address),
]

urlpatterns.extend(router.urls)
urlpatterns.append(url(r'^.*$', IndexView.as_view(), name='indexview'))