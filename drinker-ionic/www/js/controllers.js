angular.module('Drinker.controllers', ['ionic','ngCordova'])
.controller('AppCtrl', function ($scope, $ionicModal, $timeout, $localStorage, $state, loginFactory, $ionicHistory) {

  // With the new view caching in Ionic, Controllers are only called
  // when they are recreated or on app start, instead of every page change.
  // To listen for when this page is active (for example, to refresh data),
  // listen for the $ionicView.enter event:
  //$scope.$on('$ionicView.enter', function(e) {
  //});

  // Form data for the login modal
  $scope.loginData = $localStorage.getObject('userinfo','{}');

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

    $ionicHistory.nextViewOptions({
      disableBack: true
    });
    $state.go("app.home", {}, {reload: true});
  };

  $scope.logout = function() {
    console.log('Doing logout');
    $localStorage.storeObject('userinfo',{});

    $ionicHistory.clearHistory();
    $ionicHistory.nextViewOptions({ disableBack: true, historyRoot: true });
    $state.go("app.home", {}, {reload: true});
  };

  // Perform the login action when the user submits the login form
  $scope.doLogin = function() {
    console.log('Doing login', $scope.loginData);
    loginFactory.getLogin().get({mail:$scope.loginData.email}).$promise
    .then(function(data){
      $scope.user = data.data;
      $localStorage.storeObject('userinfo',$scope.user);
    });

    $ionicHistory.nextViewOptions({
      disableBack: true
    });
    $state.go("app.dash", {}, {reload: true});

    // Simulate a login delay. Remove this and replace with your login
    // code if using a login system
    $timeout(function() {
      $scope.closeLogin();
    }, 1000);
  };
})

.controller('FriendController', ['$scope', 'friendFactory', 'searchFactory', '$localStorage', function ($scope, friendFactory, searchFactory, $localStorage) {
    $scope.tab = 1;
    $scope.filtText = '';
    $scope.user = $localStorage.getObject('userinfo','{}');
    console.log($scope.user);
    friendFactory.getFriends().get({user:$scope.user.id}).$promise
    .then(function(data){
      $scope.friends = data.data;
      console.log('test friends');
      console.log($scope.friends);
      $scope.currents = $scope.friends.current;
      $scope.pendings = $scope.friends.pending;
      $scope.requests = $scope.friends.request;
    });

    $scope.acceptFriend = function(index) {
      searchFactory.sendFriend().get({id:index}).$promise
      .then(function(data){
        console.log("accepted");
      });
    }

    $scope.select = function(setTab) {
        $scope.tab = setTab;

        if (setTab === 2) {
            $scope.filtText = "Friends";
        }
        else if (setTab === 3) {
            $scope.filtText = "Request";
        }
        else if (setTab === 4) {
            $scope.filtText = "Pending";
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
}])

.controller('IndexController', ['$scope', 'signinFactory', '$localStorage', '$state', '$ionicHistory',  function ($scope, signinFactory, $localStorage, $state, $ionicHistory) {
    $scope.signinData = {};
    $scope.doSignin = function() {
      console.log('Doing signin', $scope.signinData);
      var signin = new signinFactory($scope.signinData);
      signin.$save()
      .then(function(res)  {
        console.log("signin")
        $localStorage.storeObject('userinfo',res.data);
        $ionicHistory.nextViewOptions({
          disableBack: true
        });
        $state.go("app.dash", {}, {reload: true});
      })
      .catch(function(req) { console.log("error saving obj"); })
    };
}])

.controller('DashController', ['$scope', 'signinFactory', 'barFactory', 'dashFactory', '$localStorage', '$cordovaGeolocation', '$ionicLoading', '$ionicPlatform', function ($scope, signinFactory, barFactory, dashFactory, $localStorage, $cordovaGeolocation, $ionicLoading, $ionicPlatform) {
  ionic.Platform.ready(function(){
    $ionicLoading.show({
        template: '<ion-spinner icon="bubbles"></ion-spinner><br/>Acquiring location!'
    });

    var posOptions = {
        enableHighAccuracy: false,
        timeout: 20000,
        maximumAge: 0
    };

    $cordovaGeolocation.getCurrentPosition(posOptions).then(function (position) {
        var lat  = position.coords.latitude;
        var long = position.coords.longitude;

         $scope.user = $localStorage.getObject('userinfo','{}');

         var dash = new dashFactory();
         dash.$save({lat:lat, long:long, mail:$scope.user.email})
         .then(function(res)  { console.log("signin");
          $scope.bars = res.data;
          })
         .catch(function(req) { console.log("error saving obj"); })
         /*
        barFactory.sendBar().$get({lat:lat, long:long, mail:$scope.user.email}).$promise
        .then(function(data){
          $scope.bars = data.data;
          console.log($scope.bars);
        });*/

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
    }])

.controller('BarController', ['$scope', '$stateParams', 'barFactory', '$localStorage', '$ionicHistory', '$state', function($scope, $stateParams, barFactory, $localStorage, $ionicHistory, $state) {

        $scope.bar = {};
        $scope.barData = {};
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

         $scope.doRating = function() {
           $scope.user = $localStorage.getObject('userinfo','{}');
           barFactory.sendRating().get({id:$scope.bar.id, rating:$scope.barData.rating, user:$scope.user.id}).$promise
           .then(function(data){
             $scope.bars = data.data;
             console.log($scope.bars);
             $ionicHistory.nextViewOptions({
               disableBack: true
             });
             $state.go("app.dash", {}, {reload: true});
           });
           console.log($scope.barData);
         }
      }])

.controller('SearchController', ['$scope', 'searchFactory', '$localStorage', function ($scope, searchFactory, $localStorage) {
  $scope.searcher = {};
  $scope.search = function () {
    console.log($scope.searcher.text);
    searchFactory.getSearchs().get({text:$scope.searcher.text}).$promise
    .then(function(data){
      $scope.searchs = data.data;
      console.log($scope.searchs);
      $scope.bars = $scope.searchs.bar;
      $scope.drinks = $scope.searchs.drink;
      $scope.users = $scope.searchs.user;
      console.log('test drinks');
    })
  }

  $scope.addFriend = function(index) {
    console.log(2);
    $scope.user = $localStorage.getObject('userinfo','{}');
    searchFactory.sendFriend().get({mail:index, id:$scope.user.id}).$promise
    .then(function(data){
      console.log("good");
    });
  }
}])

.controller('AboutController', ['$scope', 'corporateFactory', 'leaders', 'baseURL', function($scope, corporateFactory, leaders, baseURL) {

    $scope.baseURL = baseURL;
    $scope.leaders = leaders
    console.log($scope.leaders);

}])

;
