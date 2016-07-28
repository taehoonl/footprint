'use strict';

/** Controller for map. Responsible for updating and drawing on the map */
app.controller('mapController', function($scope, $rootScope, footprintService) {

  // local state vars
  var isLiveMode = false;
  var updatingLive = false;
  var updatingLog = false;

  // Listen on broadcasts(cross controllers calls)
  $rootScope.$on('updateLogPackets', function (event, data) {
    _displayLogPackets(data.filename);
  });
  $rootScope.$on('updateLivePackets', function (event, data) {
    _displayLivePackets();
  });
  $rootScope.$on('searchIPAddress', function (event, data) {
    _displayIPAddress(data.ipaddress);
  });


  /** Given IP address, search IP address and display search result on map
  Args:
    ipaddr(string): IP address to search and display
  */
  var _displayIPAddress = function (ipaddr) {
    footprintService.searchIPAddress(ipaddr).then(
      function successCallback(response) {
        if (response.data.success) {
          $rootScope.$emit('addSearchMarker', {'data': response.data.data});
        } else {
          console.log('Failed search IP address');
        }
        
      }, function errorCallback(response) {
        console.log('Error: search IP address');
      });
  }

  /** Display live packets on map by digesting packets in the live db table.
      Add to existing markers on map if the existing markers are from live
      db table. Otherwise, clear all markers
  */
  var _displayLivePackets = function () {
    if (updatingLive) return; // prevent multiple executions of this call

    updatingLive = true;

    footprintService.takeAllLivePackets().then( // take all objects
      function successCallback(response) {
        if (response.data.success) {
          if (!isLiveMode) { // if not live, clear all map markers
            $rootScope.$emit('clearPacketMarkers', {});
          }
          $rootScope.$emit('addPacketMarkers', {'data': response.data.data});
        } else {
          console.log('Failed to taked all live packets');
        }
      }, function errorCallback(response) {
        console.log('Error: take all live packets');
      }
    ).finally(function () { // set state variables
      isLiveMode = true;
      updatingLive = false;
    });
  };

  /** Display packets from log file on map
  Args:
    filename(string): name of log file name in data/log folder
  */
  var _displayLogPackets = function(filename) {
    if (updatingLog) return; // prevent multiple calls to this

    updatingLog = true;

    footprintService.loadLogPackets(filename).then(
      function successCallback(response) {
        if (response.data.success) {
          $rootScope.$emit('clearPacketMarkers', {});
          $rootScope.$emit('addPacketMarkers', {'data': response.data.data});
        } else {
          console.log('Failed to load log packets');
        }
      }, function errorCallback(response) {
        console.log('Eror: load log packets');
      }
    ).finally( function () {
      isLiveMode = false;
      updatingLog = false;
    });
  };

  // Initialize map
  var _init = function () {
    var map = L.map("map", {
      minZoom: 2,
      maxZoom: 13,
    }).setView([37.0, 127.0], 3);

    map.attributionControl.setPosition('bottomleft');
    L.esri.basemapLayer('Gray').addTo(map);
    footprintService.setMap(map);
  };

  _init();
});
