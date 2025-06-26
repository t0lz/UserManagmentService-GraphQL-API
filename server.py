from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime
from jwt.exceptions import InvalidTokenError
import graphene
from graphene import ObjectType, String, ID, Field

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ваш-секретный-ключ'

AUTH_USERS = {
    "admin": "admin123",
    "user": "user123"
}

users_db = [
    {
        "id": "1",
        "name": "Алиса",
        "email": "alice@example.com",
        "role": "ADMIN",
        "created_at": datetime.datetime.now()
    },
    {
        "id": "2",
        "name": "Боб",
        "email": "bob@example.com",
        "role": "USER",
        "created_at": datetime.datetime.now()
    }
]

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
                'status': 'ERROR',
                'message': 'Требуется авторизация'
            }), 401

        try:
            token = token.split()[1]
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except InvalidTokenError:
            return jsonify({
                'status': 'ERROR',
                'message': 'Недействительный токен'
            }), 401
        except Exception as e:
            return jsonify({
                'status': 'ERROR',
                'message': 'Ошибка авторизации'
            }), 401

        return f(*args, **kwargs)

    return decorated


class User(ObjectType):
    id = ID()
    name = String()
    email = String()
    role = String()
    created_at = String()

# Вводные данные для пользователя
class UserInput(graphene.InputObjectType):
    name = String(required=True)
    email = String(required=True)
    role = String(required=True)

# Мутация для создания пользователя
class CreateUser(graphene.Mutation):
    class Arguments:
        input = UserInput(required=True)

    user = Field(User)
    status = String()
    message = String()

    def mutate(self, info, input):
        if any(u['email'] == input.email for u in users_db):
            return CreateUser(
                user=None,
                status="ERROR",
                message="Пользователь с таким email уже существует"
            )

        user_data = {
            "id": str(len(users_db) + 1),
            "name": input.name,
            "email": input.email,
            "role": input.role,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        users_db.append(user_data)
        return CreateUser(
            user=user_data,
            status="SUCCESS",
            message="Пользователь успешно создан"
        )

# Мутация для обновления пользователя
class UpdateUser(graphene.Mutation):
    class Arguments:
        id = ID(required=True)
        input = UserInput(required=True)

    user = Field(User)
    status = String()
    message = String()

    def mutate(self, info, id, input):
        user = next((u for u in users_db if u['id'] == id), None)
        if not user:
            return UpdateUser(
                user=None,
                status="ERROR",
                message="Пользователь не найден"
            )

        user.update({
            "name": input.name,
            "email": input.email,
            "role": input.role
        })

        return UpdateUser(
            user=user,
            status="SUCCESS",
            message="Данные пользователя обновлены"
        )

# Мутация для удаления пользователя
class DeleteUser(graphene.Mutation):
    class Arguments:
        id = ID(required=True)

    status = String()
    message = String()

    def mutate(self, info, id):
        global users_db
        initial_count = len(users_db)
        users_db = [u for u in users_db if u['id'] != id]

        if len(users_db) == initial_count:
            return DeleteUser(
                status="ERROR",
                message="Пользователь не найден"
            )
        return DeleteUser(
            status="SUCCESS",
            message="Пользователь удален"
        )

# Запрос для получения списка пользователей
class Query(ObjectType):
    users = graphene.List(User, description="Получить список всех пользователей")
    user = graphene.Field(User, id=ID(), description="Получить пользователя по ID")

    def resolve_users(self, info):
        return users_db

    def resolve_user(self, info, id):
        user = next((u for u in users_db if u['id'] == id), None)
        return user

class Mutation(ObjectType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({
            'status': 'ERROR',
            'message': 'Необходимо указать логин и пароль'
        }), 400

    username = auth['username']
    password = auth['password']

    if username not in AUTH_USERS or AUTH_USERS[username] != password:
        return jsonify({
            'status': 'ERROR',
            'message': 'Неверные учетные данные'
        }), 401

    token = jwt.encode({
        'user': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'status': 'SUCCESS',
        'token': token,
        'message': 'Авторизация прошла успешно'
    })

@app.route('/graphql', methods=['POST'])
@token_required
def graphql_server():
    data = request.get_json()

    if not data or 'query' not in data:
        return jsonify({
            'status': 'ERROR',
            'message': 'Не указан GraphQL запрос'
        }), 400

    query = data.get('query')
    variables = data.get('variables', {})

    try:
        result = schema.execute(query, variables=variables)
        if result.errors:
            errors = [str(err) for err in result.errors]
            return jsonify({
                'status': 'ERROR',
                'message': 'Ошибка выполнения запроса',
                'errors': errors
            }), 400
        return jsonify({
            'status': 'SUCCESS',
            'data': result.data
        })
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'message': 'Внутренняя ошибка сервера',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
