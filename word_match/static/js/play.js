var playerState = "down";
var socket = io();

// Util Functions

function isEmpty(data){
  return Object.keys(data).length === 0 && data.constructor === Object
}
function getTime() {
  var dt = new Date();
  const hours = dt.getHours();
  const actual_hours = (hours % 12 == 0) ? 12 : hours;
  return actual_hours + ":" + dt.getMinutes().toString().padStart(2, "0") + (hours < 12 ? "am": "pm");
}

function sendChat() {
  socket.emit('send_chat', {room_id: gameId, message: $('#chat-input').val()})
  $('#chat-input').val("")
}

function deckUp() {
  socket.emit('deck_up', {room_id: gameId})
  playerActive = true;
}

function deckDown() {
  socket.emit('deck_down', {room_id: gameId})
  playerActive = false;
}

function reviewCards() {
  socket.emit('review_cards', {room_id: gameId})
}

function reset() {
  socket.emit('reset', {room_id: gameId})
}

function makeCard(up=False){
    var cardElement = $("<div>", {class: 'player-card'});
    if(up) {
      cardElement.addClass('up');
    } else {
      cardElement.text("CardMatch!");
      cardElement.addClass('down');
    }
    return cardElement;
}

$(document).on('keypress',function(e) {
  if(e.which == 13) {
    sendChat()
  }
});

// SocketIO Interactions

socket.on('connect', function() {
  socket.emit('join', {room_id: gameId});
});

socket.on('chat', function(data) {
  $("<div>" + data + " (" + getTime() + ")</div>").appendTo("#chat-messages");
  var container = $("#chat-messages");
  if (container.children().length > 20) {
    container.children()[0].remove();
  }
  container.scrollTop(9999999);
});

socket.on('send_deck', function(data) {
  $("#my-deck").empty();
  if (isEmpty(data)) {
    return;
  }
  data.forEach(function (card) {
    var cardElement = makeCard(playerActive);
    if (playerActive) {
      cardElement.html(card);
      cardElement.click(function () {
        socket.emit('play_card', {room_id: gameId, card: card});
      });
    }
    cardElement.appendTo("#my-deck");
  });
});

socket.on('game_state', function(data) {
  $("#roster").empty();
  data.users.forEach(function (username) {
    var userEntry = $("<div>", {class: "row"});
    var userSummary = $("<div>", {class: "col-md-6"});
    var userAction = $("<div>", {class: "col-md-6"});

    if(username == myUsername) {
      var button = $("<input/>", {type: "button"});
      if(data.players.includes(username)) {
          playerActive = true;
          button.val("Sit out");
          button.click(deckDown)
      } else {
          playerActive = false;
          button.val("Deal me in");
          button.click(deckUp)
      }
      button.appendTo(userAction);
    } else {
      if(data.players.includes(username)) {
        userAction.text("Playing");
      } else {
        userAction.text("Watching");
      }
    }
    userSummary.text(username)
    userSummary.appendTo(userEntry);
    userAction.appendTo(userEntry);
    userEntry.appendTo("#roster");
  });

  var playPileCount = data.play_pile.length
  if(["responding", "reviewing"].includes(data.state)){
    $("#pile-status").html(
      "<h2>" + data.chooser + " is choosing</h2>" +
      "<p>Cards in the pile</p>");

    $("#card-field").empty()
    if (! isEmpty(data.play_pile)) {
      data.play_pile.forEach(function (card) {
        console.log(card);
        var cardElement = makeCard(card != null);
        if(card != null) {
          cardElement.html(card);
          if(myUsername == data.chooser) {
            cardElement.click(function () { socket.emit('choose_card', { room_id: gameId, card: card }) });
          }
        }
        cardElement.appendTo($("#card-field"));
      });
    }
    if(myUsername == data.chooser) {
      var reviewButton = $("<input type='button' style='text-align:center' value='Review " + playPileCount + " cards'/>");
      reviewButton.click(function () { reviewCards() } );
      reviewButton.appendTo($("#pile-status"));
    } else {
      $("<h1 style='text-align:center'>" + playPileCount + "</h1>").appendTo($("#pile-status"));
    }
  }

  $("#game-state").text("Not Started");
  $("#game-help").text("Waiting for players");
});
