angular.module('Drinker.controllers', ['ionic','ngCordova'])
.controller('AppCtrl', function ($scope, $ionicModal, $timeout, $localStorage, $state, loginFactory) {

  // With the new view caching in Ionic, Controllers are only called
  // when they are recreated or on app start, instead of every page change.
  // To listen for when this page is active (for example, to refresh data),
  // listen for the $ionicView.enter event:
  //$scope.$on('$ionicView.enter', function(e) {
  //});

  // Form data for the login modal
  $scope.loginData = {};

  // Create the login modal that we will use later
  $ionicModal.fromTemplateUrl('templates/login.html', {
    scope: $scope
  }).then(function(modal) {
    $scope.modal = modal;
  });

  // Triggered in the login modal to close it
  $scope.closeLogin = function() {
    $scope.modal.hide();
  };

  // Open the login modal
  $scope.login = function() {
    $scope.modal.show();
  };

  // Perform the login action when the user submits the login form
  $scope.doLogin = function() {
    console.log('Doing login', $scope.loginData);
    //var signin = new loginFactory($scope.loginData);
    console.log($scope.loginData.email);
    $scope.login = loginFactory.getLogin().get({mail:$scope.loginData.email});
    $state.go("app.dash");

    // Simulate a login delay. Remove this and replace with your login
    // code if using a login system
    $timeout(function() {
      $scope.closeLogin();
    }, 1000);
  };
})

.controller('MenuController', ['$scope', 'menuFactory', 'favoriteFactory',
'dishes', 'baseURL', '$ionicListDelegate', function ($scope, menuFactory,
  favoriteFactory, dishes, baseURL, $ionicListDelegate) {
    $scope.baseURL = baseURL;

    $scope.tab = 1;
    $scope.filtText = '';
    $scope.showDetails = false;
    $scope.showMenu = false;
    $scope.message = "Loading ...";
    $scope.dishes = dishes

    $scope.select = function(setTab) {
        $scope.tab = setTab;

        if (setTab === 2) {
            $scope.filtText = "appetizer";
        }
        else if (setTab === 3) {
            $scope.filtText = "mains";
        }
        else if (setTab === 4) {
            $scope.filtText = "dessert";
        }
        else {
            $scope.filtText = "";
        }
    };

    $scope.isSelected = function (checkTab) {
        return ($scope.tab === checkTab);
    };

    $scope.toggleDetails = function() {
        $scope.showDetails = !$scope.showDetails;
    };

    $scope.addFavorite = function (index) {
        console.log("index is " + index);
        favoriteFactory.addToFavorites(index);
        $ionicListDelegate.closeOptionButtons();
    }
}])

.controller('IndexController', ['$scope', 'signinFactory', function ($scope, signinFactory) {
    $scope.signinData = {};
    $scope.doSignin = function() {
      console.log('Doing signin', $scope.signinData);
      var signin = new signinFactory($scope.signinData);
      signin.$save()
      .then(function(res)  { console.log("signin") })
      .catch(function(req) { console.log("error saving obj"); })
      .finally(function()  { console.log("always called") });;
    };
}])

.controller('DashController', ['$scope', 'signinFactory', 'barFactory', '$cordovaGeolocation', '$ionicLoading', '$ionicPlatform', function ($scope, signinFactory, barFactory, $cordovaGeolocation, $ionicLoading, $ionicPlatform) {
  ionic.Platform.ready(function(){
    $ionicLoading.show({
        template: '<ion-spinner icon="bubbles"></ion-spinner><br/>Acquiring location!'
    });

    var posOptions = {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 0
    };

    $cordovaGeolocation.getCurrentPosition(posOptions).then(function (position) {
        var lat  = position.coords.latitude;
        var long = position.coords.longitude;

        barFactory.sendBar().get({lat:lat, long:long}).$promise
        .then(function(data){
          barFactory.getBars().get().$promise
          .then(function(data){
          	$scope.bars = data.data;
            console.log($scope.bars);
          });

        });

        console.log(lat + " - " + long);
        var myLatlng = new google.maps.LatLng(lat, long);

        var mapOptions = {
            center: myLatlng,
            zoom: 16,
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };

        var map = new google.maps.Map(document.getElementById("map"), mapOptions);

        $scope.map = map;
        $ionicLoading.hide();

    }, function(err) {
        $ionicLoading.hide();
        console.log(err);
      });
    })

    barFactory.getBars().get().$promise
    .then(function(data){
    	$scope.bars = data.data;
      console.log($scope.bars);
    });


  }])

.controller('BarController', ['$scope', '$stateParams', 'barFactory', function($scope, $stateParams, barFactory) {

        $scope.bar = {};
        barFactory.getBar().get({id:parseInt($stateParams.id,10)}).$promise
         .then(function(data){
         	 $scope.bar = data.data;
           console.log($scope.bar);

           barFactory.getDrinks().get({id:$scope.bar.id}).$promise
           .then(function(data){
           	 $scope.drinks = data.data;
             console.log('test drinks');
             console.log($scope.drinks);
           });
         });
      }])

.controller('AboutController', ['$scope', 'corporateFactory', 'leaders', 'baseURL', function($scope, corporateFactory, leaders, baseURL) {

    $scope.baseURL = baseURL;
    $scope.leaders = leaders
    console.log($scope.leaders);

}])

.controller('FavoritesController', ['$scope', 'dishes', 'favorites', "menuFactory",
'favoriteFactory', 'baseURL', '$ionicListDelegate', '$ionicPopup',
'$ionicLoading', '$timeout', function ($scope, dishes, favorites, menuFactory,
  favoriteFactory, baseURL, $ionicListDelegate, $ionicPopup, $ionicLoading,
  $timeout) {
  $scope.baseURL = baseURL;
  $scope.shouldShowDelete = false;

  $scope.favorites = favorites;

  $scope.dishes = dishes;

    $ionicLoading.show({
        template: '<ion-spinner></ion-spinner> Loading...'
    });

    $scope.favorites = favoriteFactory.getFavorites();

    $scope.dishes = menuFactory.query(
      function (response) {
          $scope.dishes = response;
          $timeout(function () {
              $ionicLoading.hide();
          }, 1000);
      },
      function (response) {
          $scope.message = "Error: " + response.status + " " + response.statusText;
          $timeout(function () {
              $ionicLoading.hide();
          }, 1000);
    });

    console.log($scope.dishes, $scope.favorites);

    $scope.toggleDelete = function () {
        $scope.shouldShowDelete = !$scope.shouldShowDelete;
        console.log($scope.shouldShowDelete);
    }

    $scope.deleteFavorite = function (index) {
        var confirmPopup = $ionicPopup.confirm({
            title: 'Confirm Delete',
            template: 'Are you sure you want to delete this item?'
        });

        confirmPopup.then(function (res) {
            if (res) {
                console.log('Ok to delete' + index + "aa");
                favoriteFactory.deleteFromFavorites(index);
            } else {
                console.log('Canceled delete');
            }
        });

        $scope.shouldShowDelete = false;

    }
}])

.filter('favoriteFilter', function () {
  return function (dishes, favorites) {
    var out = [];
    for (var i = 0; i < favorites.length; i++) {
      for (var j = 0; j < dishes.length; j++) {
        if (dishes[j].id === favorites[i].id)
            out.push(dishes[j]);
      }
    }
    return out;
}});

;
