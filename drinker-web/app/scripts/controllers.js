'use strict';

angular.module('DrinkerApp')

        .controller('MenuController', ['$scope', 'menuFactory', function($scope, menuFactory) {

            $scope.tab = 1;
            $scope.filtText = '';
            $scope.showDetails = false;


            $scope.showMenu = true;
            $scope.message = "Loading ...";
            $scope.dishes = menuFactory.getDishes().query();

            menuFactory.getDishes()
            .then(
                function(response) {
                    $scope.dishes = response.data;
                    $scope.showMenu = true;
                },
                function(response) {
                    $scope.message = "Error: "+response.status + " " + response.statusText;
                }
            );


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
        }])

.controller('ContactController', ['$scope', function($scope) {
      $scope.feedback = {mychannel:"", firstName:"", lastName:"", agree:false, email:"" };
      var channels = [{value:"tel", label:"Tel."}, {value:"Email",label:"Email"}];
      $scope.channels = channels;
      $scope.invalidChannelSelection = false;
}])

.controller('FeedbackController', ['$scope', 'feedbackFactory', function($scope, feedbackFactory) {
    $scope.sendFeedback = function() {
        if ($scope.feedback.agree && ($scope.feedback.mychannel === "")) {
            $scope.invalidChannelSelection = true;
            console.log('incorrect');
        }
        else {
            $scope.invalidChannelSelection = false;
            console.log($scope.feedback);
            feedbackFactory.sendFeedback().save($scope.feedback);
            $scope.feedback = {mychannel:"", firstName:"", lastName:"", agree:false, email:"" };
            $scope.feedback.mychannel="";
            $scope.feedbackForm.$setPristine();
        }
    };
}])

.controller('IndexController', ['$scope', 'menuFactory', 'corporateFactory', function($scope, menuFactory, corporateFactory) {

        $scope.leader = corporateFactory.getLeader().get({id:3});
        $scope.showLeader = true;
        $scope.messageLeader="Loading ...";
        $scope.leader.$promise.then(
          function(response) {
            console.log(response);
            $scope.leader = response;
            $scope.showLeader = true;
          },
          function(response){
            console.log(response);
            $scope.messageLeader = "Error: "+response.status + " " + response.statusText;
            $scope.showLeader = false;
          }
        )

        $scope.promotion = menuFactory.getPromotion().get({id:0});
        $scope.showPromo = true;
        $scope.messagePromo="Loading ...";
        $scope.promotion.$promise.then(
          function(response) {
            console.log(response);
            $scope.promotion = response;
            $scope.showPromo = true;
          },
          function(response){
            console.log(response);
            $scope.messagePromo = "Error: "+response.status + " " + response.statusText;
            $scope.showPromo = false;
          }
        )


        $scope.dish = {};
        $scope.showDish = true;
        $scope.message="Loading ...";
        $scope.dish = menuFactory.getDishes().get({id:0});
}])

.controller('AboutController', ['$scope', 'menuFactory', 'corporateFactory', function($scope, menuFactory, corporateFactory) {
        $scope.leaders = corporateFactory.getLeaders().query();
        $scope.showLeaders = true;
        $scope.messageLeaders="Loading ...";
        $scope.leaders.$promise.then(
          function(response) {
            console.log(response);
            $scope.leaders = response;
            $scope.showLeaders = true;
          },
          function(response){
            console.log(response);
            $scope.messageLeaders = "Error: "+response.status + " " + response.statusText;
            $scope.showLeaders = false;
          }
        )
}])

;
