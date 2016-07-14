'use strict';

var app = angular.module('footprintApp', [
  'ngRoute',
  'angular-loading-bar',
]);



/* */
app.config(['$routeProvider', function ($routeProvider) {
  $routeProvider.
    // when('/somepage', {
    //   templateUrl: '',
    //   controller: 'somecontroller'
    // }).
    otherwise({
      redirectTo: '/'
    })
  },
]);

// .run( function run( $http, $cookies ){
//     // titleService.setSuffix( '[title]' );

//     // For CSRF token compatibility with Django
//   $http.defaults.xsrfHeaderName = 'X-CSRFToken';
//   $http.defaults.xsrfCookieName = 'csrftoken';
//   $http.defaults.headers.post['X-CSRFToken'] = $cookies['csrftoken'];
// });

/* Update xsrf $http headers to align with Django's defaults */
// app.config(['$http', function ($http) {
//   $http.defaults.xsrfHeaderName = 'X-CSRFToken';
//   $http.defaults.xsrfCookieName = 'csrftoken';
// }]);

// app.config(function($httpProvider , $interpolateProvider, $resourceProvider){
//     $httpProvider.defaults.xsrfCookieName = 'csrftoken';
//     $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
//     //** django urls loves trailling slashes which angularjs removes by default.
//     $resourceProvider.defaults.stripTrailingSlashes = false;

//     //** you can skip these if you want
//     // $interpolateProvider.startSymbol('[[');
//     // $interpolateProvider.endSymbol(']]');

//   });