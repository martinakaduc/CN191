$(document).ready(function(){
        namespace = '/socket';
        var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);
        const MAX_MSG = 50;
        socket.emit('UserOnline', window.username);

        // show message in div#subscribe
        function showMessage(message) {
            var messageElem = $('#subscribe'),
                height = 0,
                date = new Date();

            if ($.type(message) === "string") {
              messageElem.append($('<p>').html('[' + strftime('%H:%M | %d/%m/%Y', date) + '] ' + message + '\n'));
            } else if (message['msg'].startsWith('file://')) {
              // console.log('')
              file_msg = message['msg'].substr(message['msg'].lastIndexOf('/')+1, message['msg'].length);
              messageElem.append($('<p>').html('[' + message['created_at'] + '] ' + '(' + message['username'] + ') ' +
                                '<a target="_blank" href='+ '\'/' + message['msg'].substr(7, message['msg'].length) + '\'> ' + file_msg + '</a>' + '\n'));
            } else {
              messageElem.append($('<p>').html('[' + message['created_at'] + '] ' + '(' + message['username'] + ') ' + message['msg'] + '\n'));
            }

            messageElem.find('p').each(function(i, value) {
                height += parseInt($(this).height());
            });

            if (messageElem.find('p').length > MAX_MSG) {
                messageElem.find('p:first').remove();
            }

            messageElem.animate({scrollTop: height});
        }

        function sendMessage() {
            var msg = $('#message');
            socket.emit('MessageSocket', window.username, window.room_id, window.room_name, msg.val());
            msg.val('').focus();
        }

        function sendFileLink() {
          var file_name = $('#file').val();
          file_name = 'file://' + file_name.substr(file_name.lastIndexOf('\\')+1, file_name.length);
          socket.emit('MessageSocket', window.username, window.room_id, window.room_name, file_name);
        }

        // send message from form
        $('#submit_msg').click(function() {
            sendMessage();
        });

        $('#submit_file').click(function() {
            sendFileLink();
        });

        $('#message').keyup(function(e) {
            if(e.keyCode == 13){
                sendMessage();
            }
        });

        socket.on('RoomUsers', function(room_users) {
          console.log(room_users);
          var user_status = document.getElementById('user_status');
          user_status.innerHTML = '';
          for (user of room_users) {
            var user_container = document.createElement('div');
            user_container.className = 'row';

            var user_name = document.createElement('h6');
            user_name.className = 'p-r-30';
            user_name.innerHTML = user[1];

            var user_online = document.createElement('div');
            if (user[2] === 'None') {
              user_online.className = 'gray_icon';
            } else {
              user_online.className = 'green_icon';
            }

            user_container.appendChild(user_name);
            user_container.appendChild(user_online);

            user_status.appendChild(user_container);
          }
        });

        // income message handler
        socket.on('receive_message', function(data) {
          showMessage(data);
        });


        $('#profile_rooms').click(function(){
            window.location.href = "/profile"
        });

        socket.on('disconnect', (reason) => {
          showMessage('Disconnected: ' + reason)
          if (reason === 'io server disconnect') {
            // the disconnection was initiated by the server, you need to reconnect manually
            socket.connect();
          }
          // else the socket will automatically try to reconnect
        });

        socket.on('error', (error) => {
          showMessage('Error: ' + error);
        });

        setTimeout(function() {
          socket.emit('GetRoomUsers', window.username, window.room_id, window.room_name);
        }, 250);

});
