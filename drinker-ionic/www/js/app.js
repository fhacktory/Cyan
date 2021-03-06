// Ionic Starter App

// angular.module is a global place for creating, registering and retrieving Angular modules
// 'starter' is the name of this angular module example (also set in a <body> attribute in index.html)
// the 2nd parameter is an array of 'requires'
// 'starter.controllers' is found in controllers.js
angular.module('Drinker', ['ionic', 'Drinker.controllers','Drinker.services'])

.run(function($ionicPlatform, $rootScope, $ionicLoading) {
  $ionicPlatform.ready(function() {
    if (window.cordova && window.cordova.plugins.Keyboard) {
      cordova.plugins.Keyboard.hideKeyboardAccessoryBar(true);
      cordova.plugins.Keyboard.disableScroll(true);
    }
    if (window.StatusBar) {
      StatusBar.styleDefault();
    }
  });

  $rootScope.$on('loading:show', function () {
        $ionicLoading.show({
            template: '<ion-spinner></ion-spinner> Loading ...'
        })
    });

    $rootScope.$on('loading:hide', function () {
        $ionicLoading.hide();
    });

    $rootScope.$on('$stateChangeStart', function () {
        console.log('Loading ...');
        $rootScope.$broadcast('loading:show');
    });

    $rootScope.$on('$stateChangeSuccess', function () {
        console.log('done');
        $rootScope.$broadcast('loading:hide');
    });
})

.config(function($stateProvider, $urlRouterProvider) {
  $stateProvider

  .state('app', {
    url: '/app',
    abstract: true,
    templateUrl: 'templates/sidebar.html',
    controller: 'AppCtrl'
  })

  .state('app.home', {
  url: '/home',
  views: {
    'mainContent': {
      templateUrl: 'templates/home.html',
      controller: 'IndexController',
    }
  }
})

.state('app.dash', {
url: '/dash',
views: {
  'mainContent': {
    templateUrl: 'templates/dash.html',
    controller: 'DashController',
  }
}
})

.state('app.bar', {
url: '/bar/:id',
views: {
  'mainContent': {
    templateUrl: 'templates/bar.html',
    controller: 'BarController',
  }
}
})

.state('app.search', {
url: '/search',
views: {
  'mainContent': {
    templateUrl: 'templates/search.html',
    controller: 'SearchController',
  }
}
})

  .state('app.aboutus', {
      url: '/aboutus',
      views: {
        'mainContent': {
          templateUrl: 'templates/aboutus.html',
          controller: 'AboutController',
          resolve: {
              leaders:  ['corporateFactory', function(corporateFactory){
                return corporateFactory.query();
              }]
          }
        }
      }
    })

   .state('app.contactus', {
      url: '/contactus',
      views: {
        'mainContent': {
          templateUrl: 'templates/contactus.html'
        }
      }
    })

    .state('app.friend', {
      url: '/friend',
      views: {
        'mainContent': {
          templateUrl: 'templates/friend.html',
          controller: 'FriendController',
        }
      }
    })

  .state('app.favorites', {
      url: '/favorites',
      views: {
        'mainContent': {
          templateUrl: 'templates/favorites.html',
          controller:'',
        }
      }
    });

  // if none of the above states are matched, use this as the fallback
  $urlRouterProvider.otherwise('/app/home');

});
