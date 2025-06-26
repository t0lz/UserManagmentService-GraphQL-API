import requests
import json

SERVER_URL = 'http://localhost:5000'
TOKEN = None


def print_response(response):
    if response.status_code == 200:
        data = response.json()
        print("\nСтатус:", data.get('status'))
        print("Сообщение:", data.get('message'))

        if 'data' in data:
            print("Данные:")
            print(json.dumps(data['data'], indent=2, ensure_ascii=False))

        if 'errors' in data:
            print("\nОшибки:")
            for error in data['errors']:
                print("-", error)
    else:
        print(f"\nОшибка {response.status_code}: {response.text}")


def login(username, password):
    global TOKEN
    response = requests.post(
        f'{SERVER_URL}/login',
        json={'username': username, 'password': password}
    )

    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'SUCCESS':
            TOKEN = data['token']
            print(f"Успешный вход! Токен сохранен: {TOKEN}")
        else:
            print(f"Ошибка: {data['message']}")
    else:
        print(f"Ошибка входа: {response.text}")


def make_gql_request(query, variables=None):
    if not TOKEN:
        print("Ошибка: нет токена. Необходимо авторизоваться.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {TOKEN}' if TOKEN else None
    }

    payload = {'query': query}
    if variables:
        payload['variables'] = variables

    try:
        response = requests.post(
            f'{SERVER_URL}/graphql',
            headers=headers,
            json=payload
        )
        print_response(response)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка соединения: {e}")
        return None


if __name__ == '__main__':
    print("=== ТЕСТИРОВАНИЕ ГРАФQL СЕРВЕРА ===")

    # 1. Авторизация
    print("\n1. Авторизация:")
    login('admin', 'admin123')

    # 2. Получение всех пользователей
    print("\n2. Получение всех пользователей:")
    query_users = '''
    query {
        users {
            id
            name
            email
            role
        }
    }
    '''
    make_gql_request(query_users)

    # 3. Получение несуществующего пользователя
    print("\n3. Получение несуществующего пользователя:")
    query_user = '''
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            name
            email
            role
        }
    }
    '''
    response = make_gql_request(query_user, {"id": "999"})

    if response and response.get("data") and response["data"].get("user") is None:
        print("Пользователь с таким ID не найден.")
    else:
        print("Пользователь найден:", response["data"]["user"])

    # 4. Создание нового пользователя
    print("\n4. Создание нового пользователя:")
    mutation_create = '''
    mutation CreateUser($input: UserInput!) {
        createUser(input: $input) {
            user {
                id
                name
                email
            }
            status
            message
        }
    }
    '''
    new_user_data = {
        "input": {
            "name": "Екатерина",
            "email": "kate@example.com",
            "role": "USER"
        }
    }
    make_gql_request(mutation_create, new_user_data)

    # 5. Попытка создать пользователя с существующим email
    print("\n5. Попытка создать пользователя с существующим email:")
    make_gql_request(mutation_create, new_user_data)

    # 6. Обновление пользователя
    print("\n6. Обновление пользователя:")
    mutation_update = '''
    mutation UpdateUser($id: ID!, $input: UserInput!) {
        updateUser(id: $id, input: $input) {
            user {
                id
                name
                email
            }
            status
            message
        }
    }
    '''
    update_data = {
        "id": "1",
        "input": {
            "name": "Алиса (обновлено)",
            "email": "alice_new@example.com",
            "role": "ADMIN"
        }
    }
    make_gql_request(mutation_update, update_data)

    # 7. Удаление пользователя
    print("\n7. Удаление пользователя:")
    mutation_delete = '''
    mutation DeleteUser($id: ID!) {
        deleteUser(id: $id) {
            status
            message
        }
    }
    '''
    make_gql_request(mutation_delete, {"id": "2"})

    # 8. Проверка удаления
    print("\n8. Проверка удаления:")
    make_gql_request(query_users)
