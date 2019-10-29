import jinja2
import base64
from aiohttp import web
import aiohttp_jinja2 as jtemplate
from routes import routes
import settings
from chat.model import InitDB, User, Message
import asyncio
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet
from datetime import datetime
import socketio
import os

SESSION_MANAGER = dict()

sio = socketio.AsyncServer(async_mode='aiohttp')
fernet_key = fernet.Fernet.generate_key()
secret_key = base64.urlsafe_b64decode(fernet_key)
app = web.Application(
    middlewares=[
        session_middleware(EncryptedCookieStorage(secret_key)),
    ]
)
sio.attach(app)

@sio.on('connect', namespace='/socket')
async def connect(sid, environ):
    address = environ['aiohttp.request'].transport.get_extra_info('peername')

    SESSION_MANAGER[sid] = {'address': address[0] + ':' + str(address[1])}
    print('Client Connected: ' + str(sid))

@sio.on('disconnect', namespace='/socket')
async def disconnect(sid):
    if sid in SESSION_MANAGER:
        user_session = SESSION_MANAGER[sid]
        del SESSION_MANAGER[sid]
        if ('username' in user_session):
            user = User()
            await user.set_user_offline(user_session['username'])

            if ('room' in user_session):
                room_users = await user.get_room_users(user_session['username'], user_session['room'][0], user_session['room'][1])
                room = str(user_session['room'][0]) + '_' + user_session['room'][1]
                sio.leave_room(sid, room, namespace='/socket')
                await sio.emit('RoomUsers', room_users, room=room, namespace='/socket')

    print('Client Disconnected: ' + str(sid))

@sio.on('UserOnline', namespace='/socket')
async def set_user_online(sid, username):
    SESSION_MANAGER[sid]['username'] = username
    user = User()
    await user.set_user_online(username, SESSION_MANAGER[sid]['address'])
    print("User %s is online" % username)

@sio.on('RequestRooms', namespace='/socket')
async def get_rooms(sid, username):
    print("User %s request rooms" % username)
    user = User()
    rooms = await user.get_rooms(username)
    await sio.emit('Rooms', rooms, room=sid, namespace='/socket')

@sio.on('GetRoomUsers', namespace='/socket')
async def get_room_users(sid, username, room_id, room_name):
    # Send all other user's info to all connected users
    room = str(room_id) + '_' + room_name
    SESSION_MANAGER[sid]['room'] = [room_id, room_name]
    sio.enter_room(sid, room, namespace='/socket')
    user = User()
    check_user = await user.is_online(username)
    if (check_user):
        room_users = await user.get_room_users(username, room_id, room_name)

        if room_users:
            await sio.emit('RoomUsers', room_users, room=room, namespace='/socket')
        else:
            await sio.emit('Notify', 'There are some errors!', room=sid, namespace='/socket')

    else:
        await sio.emit('Notify', 'There are some errors!', room=sid, namespace='/socket')

@sio.on('MessageSocket', namespace='/socket')
async def message_socket(sid, username, room_id, room_name, msg):
    time_chat = datetime.now()
    room = str(room_id) + '_' + room_name

    if (msg[0:7] == 'file://'):
        msg = msg[0:7] + 'data/' + room + '/' + msg[7:]
    data = {'created_at': time_chat, 'msg': msg}


    message = Message()
    save_message = await message.save_msg(username, room_id, room_name, data)

    if not save_message:
        await sio.emit('Notify', 'There are some errors!', room=sid, namespace='/socket')

    await sio.emit('receive_message', {'username': username, 'created_at': time_chat.strftime('%H:%M | %d/%m/%Y'), 'msg': msg},
                    room=room, namespace='/socket')

app['socketio'] = []
app.add_routes(routes)
app.router.add_static('/static', settings.STATIC_PATH, name='static')
app.router.add_static('/media', settings.MEDIA_PATH, name='media')
app.router.add_static('/data', settings.UPLOAD_DATA_PATH, name='data')
jtemplate.setup(app, loader=jinja2.FileSystemLoader(settings.TEMPLATE_PATH))

if __name__ == '__main__':
    initdb = InitDB()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(initdb.createdb())
    web.run_app(app)
    loop.close()
