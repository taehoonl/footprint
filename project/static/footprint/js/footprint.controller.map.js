'use strict';

app.controller('mapController', function($scope, $rootScope, footprintService) {
  var $loadLogBtn = $('#load-log-btn');

  var map;
  var markerInformation = {}; // key: 'ip_from' value: marker info
  var markerInfoKey = 'ip_from'; // each marker has unique ip_from
  var markerObjKey = 'markerObj'; // key to Leaflet marker obj in marker info
  var markerCumulativeKey = 'length';

  var isLiveMode = false;
  var updatingLive = false;
  var updatingLog = false;
  var markerClusterGroup = L.markerClusterGroup({
    iconCreateFunction: function (cluster) {
      var n = 0;
      var childMarkers = cluster.getAllChildMarkers();
      for (var i = 0; i < childMarkers.length; i++) {
        var num = _strToByte($(childMarkers[i].options.icon.options.html).text());
        if (isNaN(num)) {
          n++;
        } else {
          n += num;
        }
      }
      return _createDivIcon(n);
    },
  });

  var markerLevels = [
    { 'unit': 'MB', 'count' : 1000000,  'class': 'marker-cluster-large'},
    { 'unit': 'kB', 'count' : 1000,     'class': 'marker-cluster-medium'},
    { 'unit': 'B',  'count' : 1,        'class': 'marker-cluster-small'},
  ];
  var locationInfo = [
    'ip_from', 'ip_to', 'country_name', 'city_name', 'latitude', 'longitude'
  ];
  var cumulativeInfo = [
    'length', 'ip_protocol'
  ];
  var dictInfo = [
    'ip_src', 'ip_dst', 'hostname'
  ];
  var ipAddr = [
    'src_ip_from', 'src_ip_to', 'dst_ip_from', 'dst_ip_to','ip_src', 'ip_dst'
  ];

  /* Listen on broadcasts */
  $rootScope.$on('updateLogPackets', function (event, data) {
    _displayLogPackets(data.filename);
  });
  $rootScope.$on('updateLivePackets', function (event, data) {
    _displayLivePackets();
  });

  /* Init map */
  var _init = function () {
    map = L.map("map", {
      minZoom: 2,
      maxZoom: 13,
    }).setView([37.0, 127.0], 4)
    map.attributionControl.setPosition('bottomleft');

    L.esri.basemapLayer('Gray').addTo(map);
  };


  /**/
  var _displayLivePackets = function () {
    if (updatingLive) return; // prevent multiple calls to this

    updatingLive = true;

    footprintService.takeAllLivePackets().then( // take all objects
      function successCallback(response) {
        if (response.data.success) {
          if (!isLiveMode) { // if not live, clear all map markers
            _clearMarkers();
          }
          _addMarkers(response.data.data);
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

  /**/
  var _displayLogPackets = function(filename) {
    if (updatingLog) return; // prevent multiple calls to this

    updatingLog = true;

    footprintService.loadLogPackets(filename).then(
      function successCallback(response) {
        if (response.data.success) {
          _clearMarkers();
          _addMarkers(response.data.data);
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

  /**/
  var _clearMarkers = function () {
    markerInformation = {};
    markerClusterGroup.clearLayers();
  };

  /**/
  var _addMarkers = function (data) {
    var key, subkey, cVal, mInfo;
    var changedMarkers = [];
    var toRemove = [];
    var toAdd = [];

    // sum up all info
    for (var i = 0; i < data.length; i++) {
      for (var j = 0; j < ipAddr.length; j++) { // convert all ip addresses
        data[i][ipAddr[j]] = _ipFromLong(data[i][ipAddr[j]]);
      }
      key = data[i][markerInfoKey];
      cVal = parseInt(data[i][markerCumulativeKey]);

      // add one time infomation
      if (!(key in markerInformation)) { // create new marker info obj
        var markerInfoTemp = {};
        for (var j = 0; j < locationInfo.length; j++) { // one time init
          subkey = locationInfo[j];
          markerInfoTemp[subkey] = data[i][subkey];
        }
        markerInformation[key] = markerInfoTemp;
      }
      mInfo = markerInformation[key];

      // add cumulative values
      for (var j = 0; j < cumulativeInfo.length; j++) {
        subkey = cumulativeInfo[j];
        if (!(subkey in mInfo)) {
          mInfo[subkey] = cVal;
        } else {
          mInfo[subkey] += cVal;
        }
      }

      // add list values
      for (var j = 0; j < dictInfo.length; j++) {
        subkey = dictInfo[j];
        if (!(subkey in mInfo)) {
          mInfo[subkey] = {};
        }
        mInfo[subkey][String(data[i][subkey])] = true;
      }
      changedMarkers.push(mInfo);
    }

    // create and refresh icons
    for (var i = 0; i < changedMarkers.length; i++) {
      mInfo = changedMarkers[i];
      if (markerObjKey in mInfo) {
        toRemove.push(mInfo[markerObjKey]);
      }
      ;
      var marker = L.marker(
        L.latLng(mInfo['latitude'], mInfo['longitude']),
        { 'icon': _createDivIcon(mInfo[markerCumulativeKey]) }
      );
      marker[markerInfoKey] = mInfo[markerInfoKey];
      marker.on('click', _markerClick); // register click

      mInfo[markerObjKey] = marker; // add a reference to marker
      toAdd.push(marker);
    }
    markerClusterGroup.addLayers(toAdd);
    markerClusterGroup.removeLayers(toRemove);
    map.addLayer(markerClusterGroup)

  };

  var _markerClick = function (e) {
    var thisMarkerInfo = markerInformation[e.target[markerInfoKey]];
    console.log(thisMarkerInfo)
  }

  var _byteToStr = function (n) {
    var level;
    var digit;
    if (n >= markerLevels[0].count) {
      level = markerLevels[0];
    } else if (n >= markerLevels[1].count) {
      level = markerLevels[1];
    } else {
      level = markerLevels[2];
    }
    digit = n / level.count;
    return digit.toFixed(1) + level.unit;
  };

  var _strToByte = function (str) {
    var level;
    if (str.endsWith(markerLevels[0].unit)) {
      level = markerLevels[0];
    } else if (str.endsWith(markerLevels[1].unit)) {
      level = markerLevels[1];
    } else {
      level = markerLevels[2];
    }
    return parseFloat(str) * level.count;
  };


  var _createDivIcon = function (count) {
    var level;

    if (count >= markerLevels[0].count) {
      level = markerLevels[0];
    } else if (count >= markerLevels[1].count) {
      level = markerLevels[1];
    } else {
      level = markerLevels[2];
    }

    return new L.DivIcon({
      html: '<div><span>' + _byteToStr(count) + '</span></div>',
      className: 'marker-cluster ' + level.class,
      iconSize: new L.Point(40, 40)
    });
  }

  var _ipFromLong = function (ipAddr) {
    return ((ipAddr >>> 24) + '.' +
      (ipAddr >> 16 & 255) + '.' +
      (ipAddr >> 8 & 255) + '.' +
      (ipAddr & 255) );
  };

  _init();
});
