# -*- coding: utf-8 -*-
import requests
import json
import os
import time
import argparse
import apiai


session = requests.Session()


# Подключаем бота
def ai_bot(data):
    # Ключ  API для бота
    data = data[:250]
    request = apiai.ApiAI('API_TOKEN').text_request()
    request.lang = 'ru'
    request.session_id = 'TinChatBot'
    request.query = data
    # Передаем боту вопрос
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    # Разбираем ответ
    response = responseJson['result']['fulfillment']['speech']
    if response:
        return response
    else:
        # Eсли ответа нет то возвращаем '))'
        return '))'


# Авторизация в Tinder
def auth():
    auth_session = requests.Session()
    # Заголовки для запросов
    header_request = {'Connection': 'close',
                      'Accept': '*/*',
                      'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_5 like Mac OS X) AppleWebKit/604.5.2 (KHTML, like Gecko) Mobile/15D5046b AKiOSSDK/4.26.0',
                      'Accept-Language': 'en-us',
                      'Content-Length': '0',
                      'Accept-Encoding': 'gzip, deflate'}
    # Вводим номер телфона в формате 7900000000
    phone_number = input('Input phone numer: ')
    # Первый запрос с номером телефона для для получения confirmation_code и login_request_code
    url = 'https://graph.accountkit.com/v1.2/start_login?access_token=AA|464891386855067|d1891abb4b0bcdfa0580d9b839f4a522' \
          '&credentials_type=phone_number' \
          '&fb_app_events_enabled=1' \
          '&fields=privacy_policy,terms_of_service' \
          '&locale=en_US' \
          '&logging_ref=D122C40E-41F7-4D1E-BB68-8AAD0E13BF3C' \
          '&phone_number=%s' \
          '&response_type=token' \
          '&sdk=ios' \
          '&state=4D8E03ED-5264-456A-B40B-C1A168F267E0' % str(phone_number)
    request = auth_session.post(url, headers=header_request)
    # Извлекаем из ответа login_request_code
    data = json.loads(request.text)
    login_request_code = data['login_request_code']

    # Вовдим код из SMS
    confirmation_code = input('Input confirmation code: ')
    # Отправка confirmation_code и  login_request_code для поулчения access_token
    url = 'https://graph.accountkit.com/v1.2/confirm_login?access_token=AA|464891386855067|d1891abb4b0bcdfa0580d9b839f4a522' \
          '&confirmation_code=%s' \
          '&credentials_type=phone_number' \
          '&fb_app_events_enabled=1' \
          '&fields=privacy_policy,terms_of_service' \
          '&locale=en_US' \
          '&logging_ref=D122C40E-41F7-4D1E-BB68-8AAD0E13BF3C' \
          '&login_request_code=%s' \
          '&phone_number=%s' \
          '&response_type=token' \
          '&sdk=ios' \
          '&state=4D8E03ED-5264-456A-B40B-C1A168F267E0' % (confirmation_code, login_request_code, phone_number)
    request = auth_session.post(url, headers=header_request)
    data = json.loads(request.text)
    # Извлекаем access_token и id
    access_token = data['access_token']
    id = data['id']

    # Отправляем POST запрос к API Tinder-a для получения api_token
    post_data = {"token" : access_token, "id" : id, "client_version" : "8.4.1"}
    api_token = requests.post('https://api.gotinder.com/v2/auth/login/accountkit', data=post_data)
    api_token_data = json.loads(api_token.text)
    auth_complite = api_token_data['data']['api_token']

    # Врзвращаем  API токен
    return auth_complite


# Проверка API токена
def check_token():
    # Фаил с токеном
    file = 'token.txt'
    token = open(file, 'r')
    print('*' * 30)
    print('Check Auth Token')
    # Проверяем не пустой ли фаил и правильная ли длинна токена
    if os.path.getsize(file) != 36:
        auth_complite = auth()
        token = open('token.txt', 'w')
        token.write(auth_complite)
    else:
        for i in token:
            # Делаем запрос с токеном из файла, если запрос отвечает 'Unauthorized' то запискаем функцию авторизации
            headers = {'x-auth-token': i}
            check = session.get('https://api.gotinder.com/meta', headers=headers)
            if check.text == 'Unauthorized':
                auth_complite = auth()
                token = open('token.txt', 'w')
                token.write(auth_complite)
                headers = {'x-auth-token': auth_complite}
            else:
                # Если от API пришел ответ, то разбриаем его и получаем имя пользователя
                data = json.loads(check.text)
                print('*' * 30)
                print('Welcome to Tinder, {}'.format(data['user']['name']))
                print('*' * 30)
            # Вовращаем auth-token
            return headers


# Получения списка всех instagram и VK аккаунтов
def downloads(headers):
    # Файл с основной базой
    file = open('logs.json', 'r')
    # Файл с дампом всех данных
    all_user_data = open('all_user_data.json', 'a')
    # Файил с дампом instagram и VK аккаунтов
    insta_data = open('insta.json', 'a')

    for id in file:
        # Получаем спиосок ID из файла базы данных
        id_result = json.loads(id)
        # Запрос на к API для получения анкеты пользователя
        request = session.get('https://api.gotinder.com/user/%s?locale=ru' % id_result['id'], headers=headers)
        data = json.loads(request.text)
        # Проверяем что анкета есть
        if data['status'] == 200:
            # Записываем все данные по анкете в файл
            user_data = json.dumps(data)
            all_user_data.write(user_data + '\n')
            # Если к аккаунту добавлен instagram извлекаем имя пользователя
            try:
                instagram = 'https://www.instagram.com/' + data['results']['instagram']['username']
                # формируем ссылку на instagram и добавляем к ней /?__a=1 для получения страницы пользователя в формате json
                request = session.get(instagram + '/?__a=1')
                vk_data = json.loads(request.text)
                # Проверяем наличие external_url в описание профиля instagram
                if vk_data['user']['external_url'] != None:
                    print('{} | {}'.format(instagram, vk_data['user']['external_url']))
                    # Если в профиле есть поле external_url записываем данные по instagram и external_url в файл
                    inst_vk = {'id': id_result['id'], 'instagram': instagram, 'vk': vk_data['user']['external_url']}
                    result = json.dumps(inst_vk)
                    insta_data.write(result + '\n')
                else:
                    print(instagram)
                    # Если external_url нет, записываем ссылку на instagram
                    inst_vk = {'id': id_result['id'], 'instagram': instagram, 'vk': None}
                    result = json.dumps(inst_vk)
                    insta_data.write(result + '\n')
            except KeyError:
                pass


# Лайк пользователя и получение ID
def like(headers):
    # Файл с базой данных
    file = open('logs.json', 'a')
    # Запрос на получение списка ID
    request = session.get('https://api.gotinder.com/recs/core?locale=ru', headers=headers)
    data = json.loads(request.text.encode('utf-8'))
    # Просматриваем все ID из списка
    for count in range(len(data['results'])):
        try:
            # Получаем ID, имя пользователя и фотографию
            id = data['results'][count]['_id']
            name = data['results'][count]['name']
            photo = data['results'][count]['photos'][0]['url']
            # Записываем ID и ссылку на фотографию
            string = {'id' : id, "Photo" : photo}
            file.write(json.dumps(string) + '\n')
            # Ставим лайк
            session.get('https://api.gotinder.com/like/%s?fast_match=1&locale=ru' % id, headers=headers)
            text = 'Вы лайкнули: {}, ID: {}, Photo: {}'.format(name, id, photo)
            print(text)
        except:
            print('Ошибка')
            continue
    time.sleep(10)


# Чат с ботом
def chat(headers):
    # Файл с историей сообщений
    file_logs = open('msg_logs.json', 'a')
    # Получаем список чатов
    matches = session.get('https://api.gotinder.com/v2/matches?count=60&locale=ru', headers=headers)
    responseJson = json.loads(matches.text.encode('utf-8'))

    # Получаем свой ИД
    userId_response = session.get('https://api.gotinder.com/meta', headers=headers)
    userId_json = json.loads(userId_response.text.encode('utf-8'))
    userId = str(userId_json['user']['_id'])

    # Получаем данные из списка чатов
    for data in range(len(responseJson['data']['matches'])):
        # Получаем matchId
        matchId = str(responseJson['data']['matches'][data]['_id'])
        # Получаем имя пользвоателя
        user_name = str(responseJson['data']['matches'][data]['person']['name'])
        # Проверяем если у нас нет сообщений с пользователем отправляем ему первое сообщение 'Привет)) Как твои дела? Как настроение?))'
        if len(responseJson['data']['matches'][data]['messages']) == 0:
            # POST данные matchId, наше сообщение и наш ID
            post_data = {"matchId": matchId, "message": "Привет)) Как твои дела? Как настроение?))",
                         "userId": userId}
            session.post('https://api.gotinder.com/user/matches/%s?locale=ru' % matchId, headers=headers,
                         data=post_data)
        else:
            # Если мы уже общались, то проверяем что последние соообщение НЕ наше и отправляем сообщение пользователя боту
            if str(responseJson['data']['matches'][data]['messages'][0]['from']) != userId:
                # ПОлучаем послелние сообщение
                data = str(responseJson['data']['matches'][data]['messages'][0]['message'])
                # Отправляем его боту
                result = ai_bot(data)
                # Формируем и отправляем сообщение с ответом от бота
                post_data = {"matchId": matchId, "message": result, "userId": userId}
                session.post('https://api.gotinder.com/user/matches/%s?locale=ru' % matchId, headers=headers,
                             data=post_data)
                # Выводим текст сообщений в консоль
                print('Пользователь: {} \nВопрос: {} \n Ответ: {}'.format(user_name, data, result))
                print('*' * 30)
                # Записываем Вопрос ответ в файл
                logs = {'request': data, 'response': result}
                file_logs.write(json.dumps(logs) + '\n')
    # Ждем 20 секунд перед запуском нового цикла
    print('Цикл завершен, ожидание 20 секунд')
    print('*'*30)
    time.sleep(20)


# Список аргументов скрипта
def arguments():
    parser = argparse.ArgumentParser(description='Welcome to Tinder Parser')
    # Парсер запускает функцию like()
    parser.add_argument('-p', '--parser', action='store_true')
    # Запускает функцию поиска instagram и VK аккаунтов
    parser.add_argument('-d', '--downloads',  action='store_true')
    # Запускает чат с ботом
    parser.add_argument('-c', '--chat',  action='store_true')

    return parser


if __name__ == "__main__":
    parser = arguments()
    namespace = parser.parse_args()
    headers = check_token()
    if namespace.parser:
        while True:
            like(headers)
    if namespace.downloads:
        downloads(headers)
    if namespace.chat:
        while True:
            chat(headers)
    else:
        pass
