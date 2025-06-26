import graphene
from graphene import Scalar
from datetime import datetime

class Email(Scalar):
    @staticmethod
    def serialize(value):
        if '@' not in value:
            raise ValueError("Некорректный формат email")
        return value

    @staticmethod
    def parse_literal(node):
        if '@' not in node.value:
            raise ValueError("Некорректный формат email")
        return node.value

    @staticmethod
    def parse_value(value):
        if '@' not in value:
            raise ValueError("Некорректный формат email")
        return value

class User(graphene.ObjectType):
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
    email = graphene.Field(Email, required=True)
    role = graphene.String(required=True)
    created_at = graphene.DateTime()

class UserInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Имя пользователя")
    email = graphene.Field(Email, required=True, description="Email пользователя")
    password = graphene.String(required=True, min_length=6, description="Пароль (мин. 6 символов)")
    role = graphene.String(required=True, default_value="USER", description="Роль пользователя")

class CreateUser(graphene.Mutation):
    class Arguments:
        input = UserInput(required=True)

    user = graphene.Field(User)
    status = graphene.String()
    message = graphene.String()

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
            "created_at": datetime.now()
        }
        users_db.append(user_data)
        return CreateUser(
            user=user_data,
            status="SUCCESS",
            message="Пользователь успешно создан"
        )

class UpdateUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = UserInput(required=False)

    user = graphene.Field(User)
    status = graphene.String()
    message = graphene.String()

    def mutate(self, info, id, input=None):
        user = next((u for u in users_db if u['id'] == id), None)
        if not user:
            return UpdateUser(
                user=None,
                status="ERROR",
                message="Пользователь не найден"
            )

        if input:
            if len(input.password) < 6:
                return UpdateUser(
                    user=None,
                    status="ERROR",
                    message="Пароль должен содержать минимум 6 символов"
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

class DeleteUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    status = graphene.String()
    message = graphene.String()

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

class Query(graphene.ObjectType):
    users = graphene.List(User, description="Получить список всех пользователей")
    user = graphene.Field(
        User,
        id=graphene.ID(required=True),
        description="Получить пользователя по ID"
    )

    def resolve_users(self, info):
        return users_db

    def resolve_user(self, info, id):
        user = next((u for u in users_db if u['id'] == id), None)
        if not user:
            raise ValueError("Пользователь не найден")
        return user

users_db = [
    {
        "id": "1",
        "name": "Алиса",
        "email": "alice@example.com",
        "role": "ADMIN",
        "created_at": datetime.now()
    },
    {
        "id": "2",
        "name": "Боб",
        "email": "bob@example.com",
        "role": "USER",
        "created_at": datetime.now()
    }
]

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field(description="Создать нового пользователя")
    update_user = UpdateUser.Field(description="Обновить данные пользователя")
    delete_user = DeleteUser.Field(description="Удалить пользователя")

schema = graphene.Schema(query=Query, mutation=Mutation)
