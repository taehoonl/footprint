'use strict';

app.controller('actionController', function($rootScope, $scope, $interval, footprintService) {
  var $modalElement = $('#modal-log-file');
  var $logFileSelect = $('#log-file-select');
  var $startLiveBtn = $('#start-live-btn');
  var $stopLiveBtn = $('#stop-live-btn');
  var $loadLogBtn = $('#load-log-btn');
  var repeatUpdateLive;
  var repeatUpdateLiveRate = 3000;
  $scope.isLive = false;

  $scope.setIsLive = function (value){
    $scope.isLive = value;
    if (value) {
      _startLive(); // start collecting live
    } else {
      _stopLive(); // stop colleting live
    }
  };

  $scope.openLogModal = function () {
    // load log file list
    footprintService.getLogFiles().then(
      function successCallback(response) {
        $modalElement.modal();
        _updateSelectOptions($logFileSelect, response.data.files);
      }, function errorCallback(response) {
        alert('Failed to get log files');
      });
  };

  $scope.loadLogFile = function () {
    var selectedFile = $logFileSelect.find('option:selected').val();
    $modalElement.modal('hide');
    _stopLive(); // stop collecting live
    _updateLogPackets(selectedFile);
  };

  var _updateLivePackets = function () {
    $rootScope.$broadcast('updateLivePackets', {});
  }

  var _updateLogPackets = function (filename) {
    $rootScope.$broadcast('updateLogPackets', {'filename': filename});
  }

  var _updateSelectOptions = function (selectElem, options) {
    var i, o;
    selectElem.empty();
    for (i = 0; i < options.length; i++){
      o = options[i];
      selectElem.append($('<option>', {
        value: o,
        text: o,
      }));
    }
    selectElem.selectpicker('refresh');
  };

  var _startLive = function () {
    _disableModeBtns(true); // disable start/stop

    footprintService.startLive().then(
      function successCallback(response) {
        if (response.data.success) {      // success
          console.log('started live');
          $scope.isLive = true;
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

  var _disableModeBtns = function(value) {
    $startLiveBtn.prop('disabled', value);
    $stopLiveBtn.prop('disabled', value);
    $loadLogBtn.prop('disabled', value);
  }

});