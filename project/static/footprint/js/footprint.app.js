'use strict';

var app = angular.module('footprintApp', [
  'ngRoute',
  'angular-loading-bar',
]).run(run);

/** Update xsrf $http headers to align with Django's defaults
*/
function run($http) {
  $http.defaults.xsrfHeaderName = 'X-CSRFToken';
  $http.defaults.xsrfCookieName = 'csrftoken';
}

/** route provider setting
*/
app.config(['$routeProvider', function ($routeProvider) {
  $routeProvider.
    otherwise({
      redirectTo: '/'
    })
  },
]);
