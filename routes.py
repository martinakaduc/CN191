from aiohttp import web
from chat.views import CreateUser, Login, ForgetPassword, Logout, Profile, RoomChat, UploadData

routes = [
    web.get('/', Login, name='homepage'),
    web.get('/createuser', CreateUser, name='createuser'),
    web.post('/createuser', CreateUser),
    web.post('/login', Login, name='login'),
    web.get('/forgetpassword', ForgetPassword, name='forgetpassword'),
    web.post('/forgetpassword', ForgetPassword),
    web.get('/logout', Logout, name='logout'),
    web.get('/profile', Profile, name='profile'),
    web.post('/profile', Profile),
    web.get('/room_chat', RoomChat, name='room_chat'),
    web.post('/room_chat', RoomChat),
    web.get('/upload_data', UploadData, name='upload_data'),
    web.post('/upload_data', UploadData)
]
