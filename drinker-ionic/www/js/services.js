'use strict';

angular.module('Drinker.services', ['ngResource'])
        .constant("baseURL","http://localhost:3000/")
        .constant("testURL2", "http://localhost:1337/fhacktory.shep.fr/api")
        .constant("testURL", "https://fhacktory.shep.fr/api")

        .factory('signinFactory', ['$resource', 'testURL', function($resource, testURL) {
          return $resource(testURL + "/user");
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
                  return $resource(testURL+"/bar?lat=:lat&long=:long",null);
              };

          this.getDrinks = function(){
                return $resource(testURL+"/drink?bar_id=:id",null);
            };
        }])

        .factory('menuFactory', ['$resource', 'baseURL', function ($resource, baseURL) {
            return $resource(baseURL + "dishes/:id", null, {
                'update': {
                    method: 'PUT'
                }
            });

        }])

        .factory('promotionFactory', ['$resource', 'baseURL', function ($resource, baseURL) {
                    return $resource(baseURL + "promotions/:id");

        }])

        .factory('favoriteFactory', ['$resource', '$localStorage','baseURL', function ($resource, $localStorage, baseURL) {
            var favFac = {};
            var favorites = [];
            var fav = $localStorage.getObject('fav','{}');

            favFac.addToFavorites = function (index) {
                for (var i = 0; i < favorites.length; i++) {
                    if (favorites[i].id == index)
                        return;
                }
                favorites.push({id: index});
                $localStorage.storeObject('fav',favorites);
            };

            favFac.deleteFromFavorites = function (index) {
              for (var i = 0; i < favorites.length; i++) {
                if (favorites[i].id == index) {
                  favorites.splice(i, 1);
                }
              }
              $localStorage.storeObject('fav',favorites);
            }

            favFac.getFavorites = function () {
              favorites = $localStorage.getObject('fav','{}');
              return favorites;
            };

            return favFac;
        }])

        .factory('corporateFactory', ['$resource', 'baseURL', function($resource,baseURL) {
            return $resource(baseURL+"leadership/:id");
        }])

        .factory('feedbackFactory', ['$resource', 'baseURL', function($resource,baseURL) {
            return $resource(baseURL+"feedback/:id");
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
