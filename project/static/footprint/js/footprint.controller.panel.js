'use strict';

/** Controller that handles all events that occur on the panel */
app.controller('panelController', function($rootScope, $scope, $interval, footprintService) {
  // html elements
  var $modalElement = $('#modal-log-file');
  var $logFileSelect = $('#log-file-select');
  var $startLiveBtn = $('#start-live-btn');
  var $stopLiveBtn = $('#stop-live-btn');
  var $loadLogBtn = $('#load-log-btn');

  // local vars
  var repeatUpdateLive;
  var repeatUpdateLiveRate = 3000;

  // const
  const STATUS_DETAIL_SEPARATOR = ' / ';

  // scope vars
  $scope.isLive = false;
  $scope.statusDetail = '';
  $scope.detailLocation;
  $scope.detailIPRange;
  $scope.detailDataTransfer;
  $scope.detailIPProtocol;
  $scope.detailHostname;
  $scope.detailIPSrc;
  $scope.detailIPDst;


  // listen to broadcasts
  $rootScope.$on('markerClick', function (event, data) {
    _updateDetail(data.data);
  });


  // scope funcs
  /** Starts or stops live mode 
    Args:
      value(boolean): true = start live, false = stop live
  */
  $scope.setIsLive = function (value){
    $scope.isLive = value;
    if (value) {
      _startLive(); // start collecting live
    } else {
      _stopLive(); // stop colleting live
    }
  };

  /** Opens modal window for selecting log file */
  $scope.openLogModal = function () {
    footprintService.getLogFiles().then( // load log file list
      function successCallback(response) { // open modal and update select options
        $modalElement.modal();
        _updateSelectOptions($logFileSelect, response.data.files);
      }, function errorCallback(response) { // error
        alert('Failed to get log files');
      });
  };

  /** Load selected log file on to map */
  $scope.loadLogFile = function () {
    var selectedFile = $logFileSelect.find('option:selected').val();

    $modalElement.modal('hide');

    _stopLive(); // stop collecting live
    _updateLogPackets(selectedFile);
    _setStatusDetail(false, selectedFile);
  };

  /** Given input, validates input is a valid IP Address.
      Then search IP address and display search result on map 
    Args:
      input(string): IP Address to search
  */
  $scope.searchIPAddress = function (input) {
    var ipaddr = $.trim(input.replace(/['"]+/g, ''));
    if (!_validateIPAddress(ipaddr)) {
      alert('Invalid IP Address format!');
      return;
    }
    _searchIPAddress(ipaddr);
  }

  // Send out signal to clear search markers on map
  $scope.clearSearchMarkers = function() {
    $rootScope.$broadcast('clearSearchMarkers', {});
  }

  // Send out signal to clear packet markers on map
  $scope.clearPacketMarkers = function() {
    $rootScope.$broadcast('clearPacketMarkers', {});
  }

  // helper funcs
  /** Signals to update live mode on map */
  var _updateLivePackets = function () {
    $rootScope.$broadcast('updateLivePackets', {});
  }

  /** Signals to update log mode on map 
    Args:
      filename(string): name of log file
  */
  var _updateLogPackets = function (filename) {
    $rootScope.$broadcast('updateLogPackets', {'filename': filename});
  }

  /** Signals to search and display IP address on map
    Args:
      ipaddr(string): ip address
  */
  var _searchIPAddress = function (ipaddr) {
    $rootScope.$broadcast('searchIPAddress', {'ipaddress': ipaddr});
  }

  /** Update details part with data 
    Args:
      data(object): contains marker data such as location, ip range, etc.
  */
  var _updateDetail = function(data) {
    if (Object.keys(data).length == 0) return;

    $scope.detailLocation = data.city_name  
        + ((data.region_name == null) ? '' : ', ' + data.region_name)
        + ' ('+ data.country_name + ')';
    $scope.detailIPRange = data.ip_from + ' - ' + data.ip_to;

    if ($rootScope.MARKER_INFO_CUMULATIVE_KEY in data) { // length
      var n = data[$rootScope.MARKER_INFO_CUMULATIVE_KEY];
      $scope.detailDataTransfer = $rootScope.byteToStr(n, 3);
    } else {
      $scope.detailDataTransfer = '';
    }

    if ($rootScope.IP_PROTOCOL in data) { // protocols
      var protocols = Object.keys(data[$rootScope.IP_PROTOCOL]);
      protocols = _cleanArray(protocols);
      $scope.detailIPProtocol = protocols.join(', ');
    } else {
      $scope.detailIPProtocol = '';
    }

    if ($rootScope.HOSTNAME in data) { // hostnames
      var hostnames = Object.keys(data[$rootScope.HOSTNAME]);
      hostnames = _cleanArray(hostnames);
      $scope.detailHostname = hostnames.join('\n');
    } else {
      $scope.detailHostname = '';
    }

    if ($rootScope.IP_SRC in data) { // ip src
      var src = Object.keys(data[$rootScope.IP_SRC]);
      $scope.detailIPSrc = src.join('\n');
    } else {
      $scope.detailIPSrc = '';
    }

    if ($rootScope.IP_DST in data) { // ip dst
      var dst = Object.keys(data[$rootScope.IP_DST]);
      $scope.detailIPDst = dst.join('\n');
    } else {
      $scope.detailIPDst = '';
    }

    // donut chart for inbound vs outbound data transfer
    if ($rootScope.INBOUND in data && $rootScope.OUTBOUND in data) {
      $rootScope.$broadcast('d3DonutChart', { 
        'htmlElemId': 'data-transfer-chart',
        'data': data
      });
    } else {
      $('#data-transfer-chart').empty();
    }

    $scope.$digest();
  };

  /** Updates options for log file select 
    Args:
      selectElem(html select element): log file select element
      options(list of strings): list of select options
  */
  var _updateSelectOptions = function (selectElem, options) {
    selectElem.empty();
    for (var i = 0; i < options.length; i++){
      var o = options[i];
      selectElem.append($('<option>', {
        value: o,
        text: o,
      }));
    }
    selectElem.selectpicker('refresh');
  };

  /** Starts live mode process. Repeats calls to _updateLivePackets() */
  var _startLive = function () {
    _disableModeBtns(true); // disable start/stop

    footprintService.startLive().then(
      function successCallback(response) {
        if (response.data.success) {      // success
          console.log('started live');
          $scope.isLive = true;
          _setStatusDetail(true, '');
          repeatUpdateLive = $interval(function () {
            _updateLivePackets();
          }, repeatUpdateLiveRate);
        } else {                          // fail
          console.log('failed to start live');
          $scope.isLive = false;
        }
      },
      function errorCallback(response) {  // fail
        console.log('error startLive()');
        $scope.isLive = false;
      })
    .finally(function () {
      _disableModeBtns(false);
    });
  };

  /** Stops live mode process */
  var _stopLive = function () {
    _disableModeBtns(true); // disable start/stop

    footprintService.stopLive().then(
      function successCallback(response) {
        if (response.data.success) {        // success
          console.log('stopped live');
          $scope.isLive = false
          if (angular.isDefined(repeatUpdateLive)) {
            $interval.cancel(repeatUpdateLive);
            repeatUpdateLive = undefined;
          }
        } else {                            // fail
          console.log('failed to stop live');
          $scope.isLive = true
        }
      },
      function errorCallback(response) {    // fail
        console.log('error stopLive()');
        $scope.isLive = true;
      })
    .finally(function () {
      _disableModeBtns(false);
    });
  };

  /** Sets status detail
    Args: 
      setTime(boolean): true = set status detail to current time
                        false = set status detail to given str
      str(string): string to set status detail
   */
  var _setStatusDetail = function (setTime, str) {
    if (!setTime) {
      $scope.statusDetail = STATUS_DETAIL_SEPARATOR + str;
    } else {
      function pad2(n) {
        return (n < 10 ? '0' : '') + n;
      }
      var d = new Date($.now());
      var dStr = d.getFullYear() + '-' +
                 pad2(d.getMonth() + 1) + '-' +
                 pad2(d.getDate()) + ' ' +
                 pad2(d.getHours()) + ':' +
                 pad2(d.getMinutes()) + ':' +
                 pad2(d.getSeconds());
      $scope.statusDetail = STATUS_DETAIL_SEPARATOR + dStr + str;
    }
  }

  /** Enables or disables all mode buttons 
    Args:
      value(boolean): true = disable, false = enable
  */
  var _disableModeBtns = function (value) {
    $startLiveBtn.prop('disabled', value);
    $stopLiveBtn.prop('disabled', value);
    $loadLogBtn.prop('disabled', value);
  }

  /** Returns true if given string is a valid IP Address. 
      Otherwise returns false
    Args:
      ipaddr(string): string to check if it is a valid IP Address
  */
  var _validateIPAddress = function (ipaddr) {
    if (/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ipaddr)){
      return true;
    }
    return false;
  }

  /** Returns array with '' and null items removed
    Args:
      arr(list): target list
  */
  var _cleanArray = function (arr) {
    var newArr = [];
    for (var i = 0; i < arr.length; i++) {
      if (arr[i] !== '' && arr[i] !== null) {
        newArr.push(arr[i]);
      }
    }
    return newArr;
  }

  // init
  var _init = function () {
    $('.form-group').tooltip({
        placement: "bottom",
        trigger: "hover"
    });

    // shutdown live before exiting browser
    $(window).bind("beforeunload", function (e) {
      if ($scope.isLive) {
        _stopLive();
      }
    });
  };

  _init();
});