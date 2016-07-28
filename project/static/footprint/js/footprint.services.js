'use strict';

/** Service responsible for making HTTP requests */
app.factory('footprintService', function($http) {
  var factory = {};
  var map;

  factory.getMap = function () {
    return map;
  }

  factory.setMap = function (m) {
    map = m;
  }

  factory.getLogFiles = function () {
    return $http.get('get_log_files/');
  };

  factory.startLive = function () {
    return $http.get('start_collecting/');
  };

  factory.stopLive = function () {
    return $http.get('stop_collecting/');
  };

  factory.takeAllLivePackets = function () {
    return $http.get('take_all_live_packets/');
  };

  factory.loadLogPackets = function (logFilename) {
    return $http.post('load_log_packets/', {
      'filename': logFilename,
    });
  };

  factory.searchIPAddress = function (ipaddr) {
    return $http.post('search_ip_address/', {
      'ipaddress': ipaddr,
    });
  }

  return factory;
});
