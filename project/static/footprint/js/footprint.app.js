'use strict';

var app = angular.module('footprintApp', [
	'ngRoute',
	'angular-loading-bar',
	// 'ui.select',
	// 'ui.bootstrap',
]).run(run);

/* Update xsrf $http headers to align with Django's defaults */
function run($http) {
  $http.defaults.xsrfHeaderName = 'X-CSRFToken';
  $http.defaults.xsrfCookieName = 'csrftoken';
}

/* */
app.config(['$routeProvider', function($routeProvider){
	$routeProvider.
		when('/somepage', {
			templateUrl: '',
			controller: 'somecontroller'
		}).
		otherwise({
			redirectTo: '/'
		})
	},
]);