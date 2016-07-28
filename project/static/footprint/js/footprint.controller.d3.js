'use strict';

/** Controller for drawing and handling d3 */
app.controller('d3Controller', function($scope, $rootScope, footprintService) {

  $rootScope.$on('d3DonutChart', function (event, data) {
    var dataset = [
      ['Sent', data.data[$rootScope.OUTBOUND]],
      ['Received', data.data[$rootScope.INBOUND]],
    ]
    _drawDonutChart(data.htmlElemId, dataset);
  });

  /** Draw a donut chart on given HTML element with data set
    Args:
      htmlElemId(String): ID of HTML element
      dataset(list): refer to C3.js columns 
  */
  var _drawDonutChart = function (htmlElemId, dataset) {
    $('#' + htmlElemId).empty(); // clear

    var chart = c3.generate({
      bindto: '#' + htmlElemId,
      data: {
        columns: dataset,
        type : 'donut',
        // onclick: function (d, i) { console.log("onclick", d, i); },
        // onmouseover: function (d, i) { console.log("onmouseover", d, i); },
        // onmouseout: function (d, i) { console.log("onmouseout", d, i); }
      },
      donut: {
        title: "Data"
      },
      transition: {
        duration: 500
      },
      padding: {
        // bottom: 10,
      },
      legend: {
        // position: 'right',
      }
    });
  }


}); 
