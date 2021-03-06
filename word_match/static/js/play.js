var playerState = "down";
var socket = io();

// Util Functions

function isEmpty(data){
  return Object.keys(data).length === 0 && data.constructor === Object
}
function getTime() {
  var dt = new Date();
  const hours = dt.getHours();
  const actual_hours = (hours % 12 == 0) ? 12 : hours % 12;
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

function makeCard(up=false, prompt=false){
    var cardElement = $("<div>", {class: (prompt) ? 'prompt-card':'player-card'});
    if(up) {
      cardElement.addClass('up');
    } else {
      cardElement.text("CardMatch!");
      cardElement.addClass('down');
    }
    return cardElement;
}

function gameActive(state) {
  return ["responding", "reviewing"].includes(state)
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

socket.on('reload', function() {
  socket.disconnect();
  location.reload(true);
});

socket.on('chat', function(data) {
  var newChatMessage = $("<div/>");
  $("<div/>", {"class": "chat-time"}).text(getTime()).appendTo(newChatMessage);
  $("<div/>").text(data).appendTo(newChatMessage);
  newChatMessage.appendTo("#chat-messages");

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
    var userSummary = $("<div>", {class: "col-6"});
    var userAction = $("<div>", {class: "col-6"});

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
        if(data.players_responded.includes(username)){
          userAction.text("Responded");
        } else if (data.chooser == username) {
          userAction.text("Choosing");
        } else if (gameActive(data.state)) {
          userAction.text("Still Thinking");
        }
      } else {
        userAction.text("Just Watching");
      }
    }
    userSummary.text(username)
    userSummary.appendTo(userEntry);
    userAction.appendTo(userEntry);
    userEntry.appendTo("#roster");
  });

  var playPileCount = data.play_pile.length
  if(gameActive(data.state)){
    $("#pile-status").html(
      "<h2>" + data.chooser + " is choosing</h2>");

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
    }
    makeCard(up=true, prompt=true)
      .html($("<h4/>").text(data.prompt_card))
      .appendTo($("#pile-status"));
    if(myUsername == data.chooser || data.players_responded.includes(myUsername)){
      $("#my-deck").addClass("played");
    } else {
      $("#my-deck").removeClass("played");
    }
  } else if (data.state == "not_started"){
    $("#pile-status").html(
      "<h2> Not Started </h2>" +
      "<p>Players must use the &quot;Deal me In&quot; buttons on the right.</p>");
  }
});
