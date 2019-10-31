import aiosqlite
import settings
import hashlib

class InitDB():
    def __init__(self):
        self.user_db_file = settings.USER_DB_FILE
        self.room_db_file = settings.ROOM_DB_FILE

    async def createdb(self):
        async with aiosqlite.connect(self.user_db_file) as db:
            await db.execute(
                "create table if not exists users "
                "("
                "id integer primary key asc, "
                "username varchar(50), password varchar(50), "
                "email varchar(50), room_id text, "
                "name text, is_online text"
                ")"
            )

            await db.execute(
                "create table if not exists rooms "
                "("
                "id integer primary key asc, "
                "room_name varchar(50), users text"
                ")"
            )

class User():
    def __init__(self):
        self.user_db_file = settings.USER_DB_FILE
        self.room_db_file = settings.ROOM_DB_FILE

    async def get_user_info(self, username):
        async with aiosqlite.connect(self.user_db_file) as db:
            cursor = await db.execute("select * from users where username = '{0}'".format(username))
            rows = await cursor.fetchone()
            await cursor.close()
            return rows

    async def get_email(self, email):
        async with aiosqlite.connect(self.user_db_file) as db:
            cursor = await db.execute("select * from users where email = '{0}'".format(email))
            rows = await cursor.fetchone()
            await cursor.close()
            return rows

    async def set_user_offline(self, username):
        user = await self.get_user_info(username)
        if not user:
            return False

        async with aiosqlite.connect(self.user_db_file) as db:
            result = await db.execute("update users"
                                      " set is_online = '{0}'"
                                      " where username = '{1}';".format(None, username))
            await db.commit()
            await result.close()

    async def set_user_online(self, username, ip):
        user = await self.get_user_info(username)
        if not user:
            return False

        async with aiosqlite.connect(self.user_db_file) as db:
            result = await db.execute("update users"
                                      " set is_online = '{0}'"
                                      " where username = '{1}';".format(ip, username))
            await db.commit()
            await result.close()

    async def is_online(self, username):
        user = await self.get_user_info(username)
        if not user:
            return False

        if user[6]:
            return user
        return False

    async def create_user(self, data):
        result = False
        user = await self.get_user_info(data.get('username'))
        email = await self.get_email(data.get('email'))

        if not user and not email and data.get('username'):
            async with aiosqlite.connect(self.user_db_file) as db:
                password = hashlib.md5(data.get('password').encode('utf-8')).hexdigest()
                results = await db.execute("insert into users (username, password, email, room_id, name, is_online) "
                                           "values (?, ?, ?, ?, ?, ?)",
                                 [data.get('username'), password,
                                  data.get('email'), "", data.get('name'), None])
                await db.commit()
                if results.lastrowid:
                    result = await self.get_login_user(results.lastrowid)
                await results.close()

        return result

    async def login_user(self, username, password):
        async with aiosqlite.connect(self.user_db_file) as db:
            password = hashlib.md5(password.encode('utf-8')).hexdigest()
            cursor = await db.execute("select * from users where username = '{0}' "
                                      "and password = '{1}'".format(username, password))

            rows = await cursor.fetchone()
            await cursor.close()
            return rows

    async def check_password(self, username, password):
        async with aiosqlite.connect(self.user_db_file) as db:
            cursor = await db.execute("select * from users where username = '{0}' and password = '{1}'".format(username, password))
            rows = await cursor.fetchone()
            await cursor.close()
            return rows

    async def change_password(self, username, old_password, new_password):
        result = False
        check_user = await self.is_online(username)
        if not check_user:
            return result

        async with aiosqlite.connect(self.user_db_file) as db:
            old_password = hashlib.md5(old_password.encode('utf-8')).hexdigest()
            new_password_hash = hashlib.md5(new_password.encode('utf-8')).hexdigest()
            checked = await self.check_password(username, old_password)
            if not checked:
                return result
            else:
                results = await db.execute("update users"
                                          " set password = '{0}'"
                                          " where username = '{1}';".format(new_password_hash, username))
                await db.commit()
                result = await self.login_user(username, new_password)
                await results.close()
        return result

    async def forget_password(self, email):
        async with aiosqlite.connect(self.user_db_file) as db:
            cursor = await db.execute("select * from users where email = '{0}'".format(email))

            rows = await cursor.fetchone()
            await cursor.close()
            return rows

    async def get_login_user(self, user_id):
        async with aiosqlite.connect(self.user_db_file) as db:
            cursor = await db.execute("select * from users where id = '{0}'".format(user_id))
            rows = await cursor.fetchone()
            await cursor.close()
            return rows

    async def get_rooms(self, username):
        user = await self.is_online(username)

        if not user:
            return None
        if len(user[4]) > 0:
            room_id = user[4].split(',')
            rooms = list()
            async with aiosqlite.connect(self.user_db_file) as user_db:
                for id in room_id:
                    cursor = await user_db.execute("select * from rooms where id = '{0}'".format(id))
                    rows = await cursor.fetchone()
                    await cursor.close()
                    rooms.append(rows)
            return rooms
        else:
            return None

    async def get_room_users(self, username, room_id, room_name):

        users = list()
        async with aiosqlite.connect(self.user_db_file) as user_db:
            cursor = await user_db.execute("select rooms.users from rooms "
                                            "where id = '{0}' and room_name = '{1}'".format(room_id, room_name))
            user_names = await cursor.fetchone()
            await cursor.close()

            user_names = user_names[0].split(',')
            for user in user_names:
                if not user:
                    continue

                cursor = await user_db.execute("select users.username, users.name, users.is_online from users "
                                                "where username = '{0}'".format(user))
                row = await cursor.fetchone()
                await cursor.close()
                users.append(row)

        return users

    async def add_room_to_user(self, username, room_id):
        async with aiosqlite.connect(self.user_db_file) as user_db:
            cursor = await user_db.execute("select users.room_id from users where username = '{0}'".format(username))
            row = await cursor.fetchone()
            await cursor.close()
            result = await user_db.execute("update users"
                                      " set room_id = '{0}'"
                                      " where username = '{1}';".format(row[0]+str(room_id)+',', username))
            await user_db.commit()
            await cursor.close()
            await result.close()
        return result

    async def user_create_room(self, username, room_name, users):
        result = False

        check_user = await self.is_online(username)
        if not check_user:
            return result

        available_users = users.split(',')
        for i, user in enumerate(available_users):
            check_user = await self.get_user_info(user)
            if not check_user:
                del available_users[i]
        available_users = username + ',' + ','.join(available_users)

        async with aiosqlite.connect(self.user_db_file) as user_db:
            results = await user_db.execute("insert into rooms (room_name, users) "
                                            "values (?, ?)", [room_name, available_users])
            await user_db.commit()
            if results.lastrowid:
                for user in available_users.split(','):
                    if not user:
                        continue
                    result = await self.add_room_to_user(user, results.lastrowid)

            await results.close()



        async with aiosqlite.connect(self.room_db_file) as room_db:
            print(str(results.lastrowid) + "_" + room_name)
            result = await room_db.execute(
                    "create table if not exists '{0}' "
                    "("
                    "id integer primary key asc, "
                    "username varchar(50), created_at datetime,"
                    "msg text"
                    ")".format(str(results.lastrowid) + "_" + room_name)
            )
            await room_db.commit()
            await result.close()

        return result

class Message:
    def __init__(self):
        self.user_db_file = settings.USER_DB_FILE
        self.room_db_file = settings.ROOM_DB_FILE

    async def save_msg(self, username, room_id, room_name, data):
        user = User()
        user_info = await user.is_online(username)
        if not user_info:
            return False

        if str(room_id) not in user_info[4].split(','):
            return False

        async with aiosqlite.connect(self.room_db_file) as db:
            await db.execute("insert into '{0}' (username, created_at, msg) "
                             "values (?, ?, ?)".format(str(room_id) + '_' + room_name),
                             [username, data.get('created_at'), data.get('msg')])
            await db.commit()
            return True

    async def load_msg(self, username, room_id, room_name):
        user = User()
        user_info = await user.is_online(username)
        if not user_info:
            return None

        if str(room_id) not in user_info[4].split(','):
            return None

        async with aiosqlite.connect(self.room_db_file) as db:
            cursor = await db.execute("select * from '{0}' limit {1} OFFSET "
                                      "(SELECT COUNT(*) FROM '{0}')-{1};".format(str(room_id) + '_' + room_name, settings.MAX_MSG))
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
