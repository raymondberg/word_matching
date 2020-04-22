var playerState = "down";
var socket = io();

// Util Functions

function getTime() {
  var dt = new Date();
  return dt.toLocaleTimeString();
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
  $("<div>" + getTime() + ": " + data + "</div>").appendTo("#chat-box");
  console.log($("#chat-box").children().length);
  if ($("#chat-box").children().length > 10) {
    $("#chat-box").children()[0].remove();
  }
});

socket.on('send_deck', function(data) {
  $("#my-deck").empty();
  data.forEach(function (card) {
    var cardElement = $("<div>", {class: 'player-card'});
    if (playerActive) {
      cardElement.html(card);
      cardElement.addClass('up');
    } else {
      cardElement.text("CardMatch!");
      cardElement.addClass('down');
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

  $("#game-state").text("Not Started");
  $("#game-help").text("Waiting for players");
});
