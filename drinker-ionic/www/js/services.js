'use strict';

angular.module('Drinker.services', ['ngResource'])
        .constant("baseURL","http://localhost:3000/")
        .constant("testURL2", "http://localhost:1337/fhacktory.shep.fr/api")
        .constant("testURL", "https://fhacktory.shep.fr/api")

        .factory('signinFactory', ['$resource', 'testURL', function($resource, testURL) {
          return $resource(testURL + "/user");
        }])

        .factory('dashFactory', ['$resource', 'testURL', function($resource, testURL) {
          return $resource(testURL + "/user/:mail?lat=:lat&long=:long");
        }])

        .service('loginFactory', ['$resource', 'testURL', function($resource, testURL) {
          this.getLogin = function () {
                    return $resource(testURL+"/user/:mail");
          };

          //return $resource(testURL + "/user/:mail");
        }])

        .service('barFactory', ['$resource', 'testURL', function($resource, testURL) {

          this.getBars = function(){
                return $resource(testURL+"/bar",null);
            };

          this.getBar = function(){
                return $resource(testURL+"/bar/:id",null);
            };

            this.sendBar = function(){
                  return $resource(testURL+"/user/:mail?lat=:lat&long=:long",null);
              };

          this.getDrinks = function(){
                return $resource(testURL+"/drink?bar_id=:id",null);
            };

            this.sendRating = function(){
                  return $resource(testURL+"/bar/:id/:rating?user_id=:user",null);
              };
        }])

        .service('searchFactory', ['$resource', 'testURL', function($resource, testURL) {

          this.getSearchs = function(){
                return $resource(testURL+"/search/:text",null);
            };

            this.sendFriend = function(){
                  return $resource(testURL+"/friend/:id/:mail",null);
              };
        }])

        .service('friendFactory', ['$resource', 'testURL', function($resource, testURL) {

          this.getFriends = function(){
                return $resource(testURL+"/friend?user_id=:user",null);
            };

            this.getAccept = function(){
                  return $resource(testURL+"/friend/:id",null);
              };
        }])

        .factory('$localStorage', ['$window', function($window) {
        return {
          store: function(key, value) {
            $window.localStorage[key] = value;
          },
          get: function(key, defaultValue) {
            return $window.localStorage[key] || defaultValue;
          },
          storeObject: function(key, value) {
            $window.localStorage[key] = JSON.stringify(value);
          },
          getObject: function(key,defaultValue) {
            return JSON.parse($window.localStorage[key] || defaultValue);
          }
        }
      }])

;
