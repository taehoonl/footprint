'use strict';

/** Controller for drawing and handling markers. 
    Stores cache data PACKET_MARKER_INFORMATION */
app.controller('markerController', function($scope, $rootScope, footprintService) {

  var $mapkey = $('#map-key');

  // global vars
  $rootScope.MARKER_INFO_CUMULATIVE_KEY = 'length';  // used to define cumulative value
  $rootScope.INBOUND = 'inbound';
  $rootScope.OUTBOUND = 'outbound';
  $rootScope.IP_SRC = 'ip_src';
  $rootScope.IP_DST = 'ip_dst';
  $rootScope.IP_PROTOCOL = 'ip_protocol';
  $rootScope.HOSTNAME = 'hostname';

  // constants
  const MARKER_INFO_KEY = 'ip_from'; 						// each marker has unique ip_from
  const MARKER_INFO_OBJ_KEY = 'markerObj'; 			// key to Leaflet marker obj
  const SRC_PREFIX = 'src_';
  const DST_PREFIX = 'dst_';
  const MARKER_LEVELS = [
    { 'unit': 'MB', 'unit_full': 'MB', 'count' : 1000000, 'class': 'marker-cluster-large'},
    { 'unit': 'kB', 'unit_full': 'kB', 'count' : 1000,    'class': 'marker-cluster-medium'},
    { 'unit': 'B',  'unit_full': 'Byte',     'count' : 1,       'class': 'marker-cluster-small'},
  ];
  const LOCATION_FIELDS = [
    'ip_from', 'ip_to', 'country_name', 'city_name', 
    'region_name', 'latitude', 'longitude'
  ];
  const CUMULATIVE_FIELDS = [
  	$rootScope.MARKER_INFO_CUMULATIVE_KEY, 
    $rootScope.INBOUND, $rootScope.OUTBOUND
  ];
  const COLLECTION_FIELDS = [
  	$rootScope.IP_SRC, $rootScope.IP_DST, 
    $rootScope.IP_PROTOCOL, $rootScope.HOSTNAME
  ];
  const IPADDR_FIELDS = [
    'src_ip_from', 'src_ip_to', 'dst_ip_from', 'dst_ip_to',
    $rootScope.IP_SRC, $rootScope.IP_DST, 
  ];

  // local state variables
  var MAP = footprintService.getMap();
  var PACKET_MARKER_INFORMATION = {}; // key: 'MARKER_INFO_KEY' value: marker info
  var PACKET_MARKER_CLUSTER = L.markerClusterGroup({
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
  var SEARCH_MARKER_CLUSTER = L.markerClusterGroup();

  // listen broadcasts(cross controller functions)
  $rootScope.$on('clearPacketMarkers', function (event, data) {
    _clearPacketMarkers();
  });
  $rootScope.$on('addPacketMarkers', function (event, data) {
    _addPacketMarkers(data.data);
  });
  $rootScope.$on('clearSearchMarkers', function (event, data) {
    _clearSearchMarkers();
  });  
  $rootScope.$on('addSearchMarker', function (event, data) {
    _addSearchMarkers(data.data);
  });

  /** Given IP Geolocation data, add a marker on map
    Args:
      data(object): obj containing IP Geolocation data such as 
                    city_name, country_name, ip_from, etc.
  */
  var _addSearchMarkers = function (data) {
    data['ip_from'] = _ipFromLong(data['ip_from']);
    data['ip_to'] = _ipFromLong(data['ip_to']);
    
    var latLng = L.latLng(data['latitude'], data['longitude']);
    var markerIcon = L.AwesomeMarkers.icon({
      prefix: 'glyphicon',
      icon: 'signal',
      markerColor: 'darkblue',
    });
    var marker = L.marker(latLng, {'icon': markerIcon});
    marker.on('click', _searchMarkerClick);
    marker['data'] = data;

    SEARCH_MARKER_CLUSTER.addLayer(marker);
    MAP.addLayer(SEARCH_MARKER_CLUSTER);
    MAP.setView(latLng, 4, { animate: true });
  }

  /** Given packet marker info, returns corresponding marker obj in
      PACKET_MARKER_INFORMATION.
    Args:
      prefix(SRC_PREFIX or DST_PREFIX): used for determining src or dst
      markerInfo(object): obj containing LOCATION_FIELDS, CUMULATIVE_FIELDS
                          and COLLECTION_FIELDS
  */
  var _getMarkerInfo = function (prefix, markerInfo) {
  	var subkey;
  	var key = markerInfo[prefix + MARKER_INFO_KEY];

  	if (!(key in PACKET_MARKER_INFORMATION)) { // create new marker info obj
      var mInfoTemp = {};
      for (var j = 0; j < LOCATION_FIELDS.length; j++) { // one time init
        subkey = LOCATION_FIELDS[j];
        mInfoTemp[subkey] = markerInfo[prefix + subkey];
      }
      for (var j = 0; j < CUMULATIVE_FIELDS.length; j++) {
      	subkey = CUMULATIVE_FIELDS[j];
      	mInfoTemp[subkey] = 0;
      }
      for (var j = 0; j < COLLECTION_FIELDS.length; j++) {
      	subkey = COLLECTION_FIELDS[j];
      	mInfoTemp[subkey] = {};
      }
      PACKET_MARKER_INFORMATION[key] = mInfoTemp; // cache marker info obj
    }
    return PACKET_MARKER_INFORMATION[key];
  }

  /** Given list of Packet Marker data, draw markers on map and store data 
      in cache for other usages.
    Args:
      data(list of Packet Marker data): data to draw and store
  */
  var _addPacketMarkers = function (data) {
  	var changedMarkers = {};
  	var toAdd = [];
  	var toRemove = [];

    for (var i = 0; i < data.length; i++) {
      for (var j = 0; j < IPADDR_FIELDS.length; j++) { // convert all ip addresses
        data[i][IPADDR_FIELDS[j]] = _ipFromLong(data[i][IPADDR_FIELDS[j]]);
      }

      var srcMarkerInfo = _getMarkerInfo(SRC_PREFIX, data[i]);
      var dstMarkerInfo = _getMarkerInfo(DST_PREFIX, data[i]);
      var cVal = parseInt(data[i][$rootScope.MARKER_INFO_CUMULATIVE_KEY]);

      // add cumulative values
      for (var j = 0; j < CUMULATIVE_FIELDS.length; j++) {
      	var subkey = CUMULATIVE_FIELDS[j];
      	if (subkey == $rootScope.OUTBOUND) {
      		srcMarkerInfo[subkey] += cVal;
      	} else if (subkey == $rootScope.INBOUND) {
      		dstMarkerInfo[subkey] += cVal;
      	} else {
      		srcMarkerInfo[subkey] += cVal;
      		dstMarkerInfo[subkey] += cVal;
      	}
      }

      // add collection values
      for (var j = 0; j < COLLECTION_FIELDS.length; j++) {
        var subkey = COLLECTION_FIELDS[j];
        if (subkey == $rootScope.IP_SRC) {
        	dstMarkerInfo[subkey][String(data[i][subkey])] = true; 
        } else if (subkey == $rootScope.IP_DST) {
        	srcMarkerInfo[subkey][String(data[i][subkey])] = true; 
        } else {
        	dstMarkerInfo[subkey][String(data[i][subkey])] = true;
        	srcMarkerInfo[subkey][String(data[i][subkey])] = true;
        }
      }

      changedMarkers[data[i][SRC_PREFIX + MARKER_INFO_KEY]] = true;
      changedMarkers[data[i][DST_PREFIX + MARKER_INFO_KEY]] = true;
    }

    // create and refresh markers
    for (var key in changedMarkers) {
    	var markerInfo = PACKET_MARKER_INFORMATION[key];

      // check if map marker already exists, remove and add if this case
    	if (MARKER_INFO_OBJ_KEY in markerInfo) { 
    		toRemove.push(markerInfo[MARKER_INFO_OBJ_KEY]);
    	}

      // create marker
      var n = markerInfo[$rootScope.MARKER_INFO_CUMULATIVE_KEY];
    	var markerObj = L.marker(
        L.latLng(markerInfo['latitude'], markerInfo['longitude']),
        { 'icon': _createDivIcon(n) }
      );
      markerObj.on('click', _packetMarkerClick);
      markerObj[MARKER_INFO_KEY] = markerInfo[MARKER_INFO_KEY];

      markerInfo[MARKER_INFO_OBJ_KEY] = markerObj;
      toAdd.push(markerObj);
    }

    // add/remove from map
    PACKET_MARKER_CLUSTER.addLayers(toAdd);
    PACKET_MARKER_CLUSTER.removeLayers(toRemove);
    MAP.addLayer(PACKET_MARKER_CLUSTER);
  };

  /** Broadcasts that packet marker has been clicked
    Args:
      e(event): contains key to PACKET_MARKER_INFORMATION
  */
  var _packetMarkerClick = function (e) {
    var markerInfo = PACKET_MARKER_INFORMATION[e.target[MARKER_INFO_KEY]];
    $('.collapse').collapse('show');
    $rootScope.$emit('markerClick', {'data': markerInfo});
  }

  /** Broadcasts that search marker has been clicked
    Args:
      e(event): contains information about IP Geolocation data
  */
  var _searchMarkerClick = function (e) {
    $('.collapse').collapse('show');
    $rootScope.$emit('markerClick', {'data': e.target.data});
  }


  /** Returns byte string representation of given numerical value
    Args:
      number(int): numerical value to convert into string representation
      decimal(int): number of decimals to return
  */
  $rootScope.byteToStr = function (number, decimal) {
    var level;
    var digit;
    if (number >= MARKER_LEVELS[0].count) {
      level = MARKER_LEVELS[0];
    } else if (number >= MARKER_LEVELS[1].count) {
      level = MARKER_LEVELS[1];
    } else {
      level = MARKER_LEVELS[2];
    }
    digit = number / level.count;
    if (level != MARKER_LEVELS[2]) {
      digit = digit.toFixed(decimal);
    }
    return digit + level.unit;
  };

  /** Returns numerical value of given string representation of byte
    Args:
      str(string): string representation of byte with unit
  */
  var _strToByte = function (str) {
    var level;
    if (str.endsWith(MARKER_LEVELS[0].unit)) {
      level = MARKER_LEVELS[0];
    } else if (str.endsWith(MARKER_LEVELS[1].unit)) {
      level = MARKER_LEVELS[1];
    } else {
      level = MARKER_LEVELS[2];
    }
    return parseFloat(str) * level.count;
  };

  /** Returns div marker cluster icon with given numerical value 
      converted into string representation with byte unit
    Args:
      count(int): numerical value that appears on icon
  */
  var _createDivIcon = function (count) {
    var level;

    if (count >= MARKER_LEVELS[0].count) {
      level = MARKER_LEVELS[0];
    } else if (count >= MARKER_LEVELS[1].count) {
      level = MARKER_LEVELS[1];
    } else {
      level = MARKER_LEVELS[2];
    }

    return new L.DivIcon({
      html: '<div><span>' + $rootScope.byteToStr(count, 1) + '</span></div>',
      className: 'marker-cluster ' + level.class,
      iconSize: new L.Point(40, 40)
    });
  }

  /** Returns readable string representation of given 
      int representation of IP address
    Args:
      ipaddr(int or long): numerical representation of IP address
  */
  var _ipFromLong = function (ipaddr) {
    return ((ipaddr >>> 24) + '.' +
      (ipaddr >> 16 & 255) + '.' +
      (ipaddr >> 8 & 255) + '.' +
      (ipaddr & 255) );
  };

  // delete packet markers from map and cache data
  var _clearPacketMarkers = function () {
    PACKET_MARKER_INFORMATION = {};
    PACKET_MARKER_CLUSTER.clearLayers();
  };

  // delete search markers from map
  var _clearSearchMarkers = function () {
    SEARCH_MARKER_CLUSTER.clearLayers();
  };


  // init
  var _init = function () {
    for (var key in MARKER_LEVELS) {
      var level = MARKER_LEVELS[key];
      var markerDiv = $('<div>', {
        class: 'marker-cluster ' + level.class,
        css: {
          'display': 'table',
          'margin': '0 auto',
          'width': '40px',
          'height': '40px',
          'z-index': '477',
          'outline': 'none',
          'padding-top': '1px',
        }
      });
      var markerDivDiv = $('<div>', {
        css: {

        }
      });
      var markerDivDivSpan = $('<span>' + level.unit_full + '</span>');

      markerDiv.append(markerDivDiv.append(markerDivDivSpan));

      console.log(markerDiv);
      $mapkey.append(markerDiv);
    }
  }
  _init();
});