$(document).ready(function(){
  namespace = '/socket';
  var socket = io.connect('http://' + document.domain + ':' + location.port + namespace, {forceNew: true});

  var request_rooms = document.getElementById('rooms-tab');
  var list_rooms = document.getElementsByClassName('list-group')[0];
  var all_rooms = [];

  function create_room_row(room_name, room_id) {
    var list_group_item = document.createElement('li');
    list_group_item.className = 'list-group-item';


    var item_name = document.createElement('div');
    item_name.innerHTML = room_name;

    item_name.onclick = function() {
      var data = {'room_id': room_id, 'room_name': room_name};
      $.redirect('/room_chat', data);
    };

    var show_menu = document.createElement('span');
    show_menu.className = 'show-menu';

    var open_menu = document.createElement('i');
    open_menu.className = 'fa fa-arrow-right';
    open_menu.setAttribute('aria-hidden', 'true');

    show_menu.appendChild(open_menu);

    var list_group_menu = document.createElement('ul');
    list_group_menu.className = 'list-group-submenu';

    var delete_item = document.createElement('li');
    delete_item.className = 'list-group-submenu-item danger';

    var delete_icon = document.createElement('i');
    delete_icon.className = 'fa fa-trash';
    delete_icon.setAttribute('aria-hidden', 'true');

    delete_item.appendChild(delete_icon);

    var add_item = document.createElement('li');
    add_item.className = 'list-group-submenu-item success';

    var add_icon = document.createElement('i');
    add_icon.className = 'fa fa-plus';
    add_icon.setAttribute('aria-hidden', 'true');

    add_item.appendChild(add_icon);

    list_group_menu.appendChild(delete_item);
    list_group_menu.appendChild(add_item);

    list_group_item.appendChild(item_name);
    list_group_item.appendChild(show_menu);
    list_group_item.appendChild(list_group_menu);

    return list_group_item
  };

  socket.on('Rooms', function(rooms) {
    all_rooms = rooms;
    while (list_rooms.firstChild) {
      list_rooms.removeChild(list_rooms.firstChild);
    }

    for (room of rooms) {
      if (!room) continue;
      list_rooms.appendChild(create_room_row(room[1], room[0]));
    };

    $('.list-group-item > .show-menu').on('click', function(event) {
      event.preventDefault();
      $(this).closest('li').toggleClass('open');
    });
  });

  request_rooms.onclick = function() {
    socket.emit('RequestRooms', window.username);
  };

  $('.modal').on('hidden.bs.modal', function() {
    $("input").val('');
  });

  $('#logout_btn').on('click', function(event) {
    // event.preventDefault();
    window.location.href = '/logout';
  });

});
