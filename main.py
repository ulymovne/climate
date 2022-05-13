import sqlite3
from socket import *
from datetime import datetime, timedelta
import configparser
import threading
from telebot import types, TeleBot
import chart as chr


BASE_NAME = 'climate_co2.db'

""" 
DataBase
"""

def add_db(data_base=BASE_NAME, api="", value=0):
    global conf_parapms
    if api == conf_parapms['api_base']:
        try:
            with sqlite3.connect(data_base) as db:
                cur = db.cursor()
                date_u = round(datetime.now().timestamp())
                date_u_temp = date_u + 3600 * conf_parapms['time_zone']
                date_str = datetime.fromtimestamp(date_u_temp).strftime("%d.%m.%y %H:%M")
                query = f""" INSERT INTO co_data (date_str, date_u, co2) VALUES ("{date_str}",{date_u}, {value}) """
                cur.execute(query)
                print('Data updated')

        except Exception as e:
            print('Connection error:\n\t', e)


def get_data(data_base=BASE_NAME):
    value = [('0', 0)]
    try:
        with sqlite3.connect(data_base) as db:
            cur = db.cursor()
            query = f""" SELECT date_str, co2 FROM co_data ORDER BY id DESC LIMIT 1 """
            cur.execute(query)
            value = cur.fetchall()

    except Exception as e:
        print('Connection error:\n\t', e)
    return value[0]


""" 
Server
"""

class Sever:
    def __init__(self, ip, port):
        self.ser = socket(AF_INET, SOCK_STREAM)
        self.ser.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.ser.bind((ip, port))
        self.ser.listen(3)

    def connect(self):
        while True:
            user, addr = self.ser.accept()

            # !!!!!!!! записать в логи кто подключился
            print('Client connected:\n\t', addr[0], ':', addr[1])
            self.lissen(user)

    def lissen(self, user):
        global conf_parapms
        self.sender(user, 'connected_ok')
        is_work = True
        while is_work:
            try:
                data = user.recv(1024)
                self.sender(user, 'getted')
            except Exception as e:
                data = ''
                is_work = False
                print('Error data sent:\n\t', e)

            if len(data):
                msg_data = data.decode('utf-8')
                print(msg_data)
                msg = msg_data.split(';')
                try:
                    add_db(conf_parapms['base_name'], api=msg[0], value=int(msg[1]))
                    is_work = False
                except Exception as e:
                    print('Error in data:\n\t', e)

            else:
                print('client disconnected')
                is_work = False

    def sender(self, user, text):
        user.send(text.encode('utf-8'))


"""
Telegram
"""

def telegram(token: str):
    bot = TeleBot(token)

    def set_commands():
        commands = [
            types.BotCommand(command="/get", description="Получить текущие показания"),
            types.BotCommand(command="/polling", description="Включить опрос"),
            types.BotCommand(command="/chart", description="Построить график"),
            types.BotCommand(command="/alert", description="Включить алёртинг")
        ]
        bot.set_my_commands(commands)


    def get_markup(markup_type: str):
        markup = types.InlineKeyboardMarkup()
        if markup_type == "pool":
            b1 = types.InlineKeyboardButton('30 секунд', callback_data='pool_1')
            b2 = types.InlineKeyboardButton('60 секунд', callback_data='pool_2')
            b3 = types.InlineKeyboardButton('120 секунд', callback_data='pool_3')
            markup.row(b1, b2, b3)
        elif markup_type == "chart":
            b1 = types.InlineKeyboardButton('За последние 24 часа', callback_data='chart_1')
            b2 = types.InlineKeyboardButton('За последние 12 часов', callback_data='chart_2')
            b3 = types.InlineKeyboardButton('За вчерашние сутки', callback_data='chart_3')
            markup.row(b1, b2)
            markup.row(b3)
        elif markup_type == "alert":
            b1 = types.InlineKeyboardButton('1000 едениц', callback_data='alert_1')
            b2 = types.InlineKeyboardButton('1200 единиц', callback_data='alert_2')
            b3 = types.InlineKeyboardButton('1400 единиц', callback_data='alert_3')
            b4 = types.InlineKeyboardButton('1600 единиц', callback_data='alert_4')
            markup.row(b1, b2)
            markup.row(b3, b4)
        back = types.InlineKeyboardButton('Отмена', callback_data='back_')
        markup.row(back)
        return markup


    def set_chart(call, number):
        date_start, date_end, title_chart = 0, 0, ''
        if number == '1':
            date_start = round((datetime.now()- timedelta(days=1)).timestamp())
            date_end = round(datetime.now().timestamp())
            title_chart = 'Показания СО2 за последние сутки'
        elif number == '2':
            date_start = round((datetime.now()- timedelta(hours=12)).timestamp())
            date_end = round(datetime.now().timestamp())
            title_chart = 'Показания СО2 за последние 12 часов'
        elif number == '3':
            cur_date = datetime.today()
            date_start = round((cur_date.combine(cur_date.date(), cur_date.min.time()) - timedelta(days=1)).timestamp())
            date_end = round((cur_date.combine(cur_date.date(), cur_date.min.time())).timestamp())
            title_chart = 'Показания СО2 за вчерашние сутки'

        bot.send_photo(chat_id=call.message.chat.id,
                       photo=chr.get_chart(conf_parapms['base_name'], date_start, date_end, title_chart))

    @bot.message_handler(commands=['get'])
    def answer(message):
        data = get_data()
        bot.send_message(message.chat.id, data[0] + ", показания CO2: *" + str(data[1]) + "*", parse_mode='Markdown')

    @bot.message_handler(commands=['polling'])
    def answer(message):
        bot.send_message(message.chat.id, 'Частота опроса:', reply_markup=get_markup('pool'))

    @bot.message_handler(commands=['chart'])
    def answer(message):
        bot.send_message(message.chat.id, 'Какой график построить:', reply_markup=get_markup('chart'))

    @bot.message_handler(commands=['alert'])
    def answer(message):
        bot.send_message(message.chat.id, 'Допустимые значения:', reply_markup=get_markup('alert'))

    @bot.callback_query_handler(func=lambda call: True)
    def handle(call):
        markup_type, number = call.data.split("_")
        if markup_type == 'pool':
            # может тут перестать записывать в базу? и ограничить тайминг на 5-10 минут макс.
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text=f"Опрос с частотой: {number}")
        elif markup_type == 'chart':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text=f"Строим график:")
            set_chart(call, number)
        elif markup_type == 'alert':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text=f"Запуск алерта: {number}")
        elif markup_type == 'back':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Отмена")
        bot.answer_callback_query(call.id)

    set_commands()
    bot.polling(none_stop=True)


conf = configparser.ConfigParser()
conf.read('config/conf.ini')
# time_zone = сколько часов +UTC
conf_parapms = {'base_name': conf['Database']['base_name'],
                'api_base': conf['Database']['api_base'],
                'ip': conf['Server']['ip'],
                'port': int(conf['Server']['port']),
                'time_zone': int(conf['Server']['time_zone']),
                'tg_token': conf['Tg_bot']['token'],
                'alert': 0}

threading.Thread(target=telegram, args=(conf_parapms['tg_token'],)).start()

Sever(conf_parapms['ip'], conf_parapms['port']).connect()
