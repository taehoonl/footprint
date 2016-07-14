'use strict';

app.controller('mapController', function($scope, $rootScope, footprintService) {
	var $loadLogBtn = $('#load-log-btn');

	var map;
	var markerInformation = {}; // key: 'ip_from' value: marker information
	var markerInfoKey = 'ip_from';
	var markerObjKey = 'markerObj';
	var markerCumulativeKey = 'length';

	var isLiveMode = false;
	var updatingLive = false;
	var updatingLog = false;
	var markerClusterGroup = L.markerClusterGroup({
		iconCreateFunction: _customClusteringFunction,
	});

	// var markerClusterGroup = L.esri.Cluster.clusteredFeatureLayer({
 //    url: 'https://services.arcgis.com/rOo16HdIMeOBI4Mb/arcgis/rest/services/stops/FeatureServer/0',
	// 	iconCreateFunction: _customClusteringFunction
	// });

	var markerLevels = [
		{ 'class': 'marker-cluster-small', 'size': 40 },
		{ 'class': 'marker-cluster-medium', 'size': 40 },
		{ 'class': 'marker-cluster-large', 'size': 40 },
	];
	var locationInfo = [
		'ip_from', 'ip_to', 'country_name', 'city_name', 'latitude', 'longitude'
	];
	var cumulativeInfo = [
		'length', 'ip_protocol', 'outbound'
	];
	var dictInfo = [
		'ip_src', 'ip_dst', 'hostname'
	];
	var ipAddr = [
		'ip_from', 'ip_to', 'ip_src', 'ip_dst' 
	];


	$rootScope.$on('updateLogPackets', function (event, data) {
		_displayLogPackets(data.filename);
	});

	$rootScope.$on('updateLivePackets', function (event, data) {
		_displayLivePackets();
	});

	// display live packets
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

	// display log packets
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

	var _clearMarkers = function () {
		markerInformation = {};
		markerClusterGroup.clearLayers();
	};


	var _addMarkers = function (data) {
		var key, subkey, cVal, mInfo;
		var changedMarkers = [];

		// sum up all info
		for (var i = 0; i < data.length; i++) {

			// convert all ip addresses
			for (var j = 0; j < ipAddr.length; j++) {
				data[i][ipAddr[j]] = _ipFromLong(data[i][ipAddr[j]]);
			}

			key = data[i][markerInfoKey];
			cVal = parseInt(data[i][markerCumulativeKey]);

			// one time infomation
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

		// create/refresh icons
		var toRemove = [];
		var toAdd = [];
		for (var i = 0; i < changedMarkers.length; i++) {
			mInfo = changedMarkers[i];
			if (markerObjKey in mInfo) {
				toRemove.push(mInfo[markerObjKey]);
			}
			var latLng = L.latLng(mInfo['latitude'], mInfo['longitude']);
			var marker = L.marker(latLng, { 
				'icon': _createDivIcon(mInfo[markerCumulativeKey]) 
			});
			mInfo[markerObjKey] = marker;
			toAdd.push(marker);
		}
		markerClusterGroup.addLayers(toAdd);
		markerClusterGroup.removeLayers(toRemove);
		map.addLayer(markerClusterGroup)
		
	};

	// clustering algorithm
	var _customClusteringFunction = function (cluster) {
		var n = 0;
		console.log('in cluserint');
		var childMarkers = cluster.getAllChildMarkers();
		for (var i = 0; i < childMarkers.length; i++) {
			var num = parseint($(childMarkers[i].options.icon.options.html).text());
			console.log(num);
			if (isNaN(num)) {
				n++;
			} else {
				n += num;
			}
		}
		console.log(n);

		return _createDivIcon(n);
	};

	var _createDivIcon = function (count) {
		var level;

		if (count < markerLevels[0].count) {
			level = markerLevels[0];
		} else if (count < markerLevels[1].count) {
			level = markerLevels[1];
		} else {
			level = markerLevels[2];
		}
		
		return new L.DivIcon({
			html: '<div><span>' + count + '</span></div>',
			className: 'marker-cluster ' + level.class,
			iconSize: new L.Point(level.size, level.size)
		});
	}

	var _ipFromLong = function (ipAddr) {
		return ((ipAddr >>> 24) + '.' +
      (ipAddr >> 16 & 255) + '.' +
      (ipAddr >> 8 & 255) + '.' +
      (ipAddr & 255) );
	};

	var _init = function () {
		map = L.map("map", {
			minZoom: 2,
			maxZoom: 13,
		}).setView([37.0, 127.0], 6)
		map.attributionControl.setPosition('bottomleft');

		L.esri.basemapLayer('Gray').addTo(map);
	};

	_init();
});
