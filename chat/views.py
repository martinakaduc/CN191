import json
import settings
from aiohttp import web, WSMsgType
from aiohttp_session import get_session
import aiohttp_jinja2
from time import time
from datetime import datetime
from .model import User, Message
from settings import log
import os

def redirect(request, router_name):
    url = request.app.router[router_name].url_for()
    raise web.HTTPFound(url)

def set_session(session, key, user_data):
    session[key] = user_data
    session['last_visit'] = time()

def convert_json(message):
    return json.dumps({'error': message})

async def load_msg(username, room):
    history = list()
    message = Message()
    messages = await message.load_msg(username, room['room_id'], room['room_name'])

    for msg in messages:
        history.append(
            {'time': datetime.strptime(msg[2], '%Y-%m-%d %H:%M:%S.%f'), 'user': msg[1], 'msg': msg[3]})

    return history

class Login(web.View):
    @aiohttp_jinja2.template('chat/login.html')
    async def get(self):
        return None

    async def post(self):
        data = await self.request.post()
        user = User()
        result = await user.login_user(data.get('username'), data.get('password'))
        if isinstance(result, tuple):
            session = await get_session(self.request)
            set_session(session, 'user', {'id': result[0], 'username': result[1]})

            redirect(self.request, 'profile')
        else:
            return web.Response(text="Can't login")

class ForgetPassword(web.View):
    @aiohttp_jinja2.template('chat/forget_password.html')
    async def get(self):
        session = await get_session(self.request)
        session_user = session.get('user')
        if session_user:
            redirect(self.request, 'profile')
        return None

    async def post(self):
        session_user = await get_session(self.request)
        if session_user.get('user'):
            redirect(self.request, 'profile')

        data = await self.request.post()
        user = User()
        result = await user.forget_password(data.get('email'))
        if isinstance(result, tuple):
            with open(settings.FORGET_PASSWORD_LIST, 'w+', encoding='utf8') as f:
                f.write(str(result) + '\n')

            redirect(self.request, 'homepage')
        else:
            return web.Response(text="Email isn't recognized")

class CreateUser(web.View):
    @aiohttp_jinja2.template('chat/create_user.html')
    async def get(self):
        session = await get_session(self.request)
        session_user = session.get('user')
        if session_user:
            redirect(self.request, 'profile')
        else:
            return None

    async def post(self):
        data = await self.request.post()

        user = User()
        post = {'username': data.get('username'),
                'password': data.get('password'),
                'email': data.get('email'), 'name' : data.get('name')}
        result = await user.create_user(data=post)
        if isinstance(result, tuple):
            session = await get_session(self.request)
            set_session(session, 'user', {'id': result[0], 'username': result[1]})

            redirect(self.request, 'profile')
        else:
            return web.Response(text="Can't register")

class Logout(web.View):

    async def get(self):
        session = await get_session(self.request)
        session_user = session.get('user')
        if not session_user:
            redirect(self.request, 'homepage')

        username = session_user.get('username')

        user = User()
        await user.set_user_offline(username)

        if session_user:
            del session['user']

        redirect(self.request, 'homepage')

class Profile(web.View):
    @aiohttp_jinja2.template('chat/profile.html')
    async def get(self):
        session = await get_session(self.request)
        session_user = session.get('user')
        if not session_user:
            redirect(self.request, 'homepage')

        username = session_user.get('username')

        user = User()
        user_info = await user.get_user_info(username)

        user_info = {'id': user_info[0], 'username': user_info[1], 'email': user_info[3], 'name': user_info[5],
                    'rooms': len(user_info[4].split(',')) - 1, 'is_online': True}

        return {'user_info': user_info}

    async def post(self): # For password changing
        data = await self.request.post()
        session = await get_session(self.request)
        session_user = session.get('user')
        if not session_user:
            redirect(self.request, 'homepage')

        username = session_user.get('username')

        if (data.get('old_password') and data.get('password')):
            user = User()
            change_password = await user.change_password(username, data.get('old_password'), data.get('password'))
            if (not change_password):
                redirect(self.request, 'logout')
            else:
                redirect(self.request, 'profile')

        elif (data.get('room_name')):
            user = User()
            res = await user.user_create_room(username, data.get('room_name'), data.get('users'))

        redirect(self.request, 'profile')

class RoomChat(web.View):
    @aiohttp_jinja2.template('chat/room_chat.html')
    async def get(self):
        session = await get_session(self.request)
        if not session.get('user') or not session.get('room'):
            redirect(self.request, 'homepage')

        session_user = session.get('user')

        messages = await load_msg(session_user.get('username'), session.get('room'))

        return {"user_info": session.get('user'), "room_info": session.get('room'), "messages": messages}

    async def post(self):
        data = await self.request.post()
        if ('room_id' not in data or 'room_name' not in data):
            redirect(self.request, 'homepage')

        session = await get_session(self.request)
        if not session.get('user'):
            redirect(self.request, 'homepage')

        set_session(session, 'room', {'room_id': data['room_id'], 'room_name': data['room_name']})
        redirect(self.request, 'room_chat')

class UploadData(web.View):
    async def get(self):
        print("Request file")
        return None
    async def post(self):
        session = await get_session(self.request)
        if not session.get('user') or not session.get('room'):
            redirect(self.request, 'homepage')

        reader = await self.request.multipart()
        field = await reader.next()
        assert field.name == 'file'
        filename = field.filename

        room = session.get('room')

        folder_path = settings.UPLOAD_DATA_PATH + '/' + str(room['room_id']) + '_' + room['room_name']
        file_path = folder_path + '/' + filename
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # You cannot rely on Content-Length if transfer is chunked.
        size = 0
        with open(file_path, 'wb') as f:
            while True:
                chunk = await field.read_chunk()  # 8192 bytes by default.
                if not chunk:
                    break
                size += len(chunk)
                f.write(chunk)

        redirect(self.request, 'room_chat')
