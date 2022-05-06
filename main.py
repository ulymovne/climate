import sqlite3
from socket import *
from datetime import datetime
import configparser
import telebot
import threading

BASE_NAME = 'climate_co3.db'

""" 
DataBase
"""
def add_db(data_base=BASE_NAME, api="", value=0):
    global conf_parapms
    if api == conf_parapms['api_base']:
        try:
            with sqlite3.connect(data_base) as db:
                cur = db.cursor()
                date_u = round(datetime.now().timestamp()) + 3600 * conf_parapms['time_zone']
                date_str = datetime.fromtimestamp(date_u).strftime("%d.%m.%y %H:%M")
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

            #!!!!!!!! записать в логи кто подключился
            print('Client connected:\n\t', addr[0], ':',addr[1])
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
def telegram(token:str):
    bot = telebot.TeleBot(token)

    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row('/get')

    def send(id, text):
        bot.send_message(id, text, reply_markup=keyboard)

    @bot.message_handler(commands=['get'])
    def answer(message):
        data = get_data()
        send(message.chat.id, data[0] + ' value: ' + str(data[1]))

    @bot.message_handler(content_types=['text'])
    def message_text(message):
        send(message.chat.id, 'hi')

    bot.polling(none_stop=True)


conf = configparser.ConfigParser()
conf.read('config/conf.ini')
#time_zone = сколько часов +UTC
conf_parapms = {'base_name':conf['Database']['base_name'],
                'api_base':conf['Database']['api_base'],
                'ip':conf['Server']['ip'],
                'port':int(conf['Server']['port']),
                'time_zone':int(conf['Server']['time_zone']),
                'tg_token':conf['Tg_bot']['token']}

threading.Thread(target=telegram, args=(conf_parapms['tg_token'],)).start()

Sever(conf_parapms['ip'], conf_parapms['port']).connect()




