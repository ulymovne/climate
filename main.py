import sqlite3
from socket import *
from datetime import datetime
import configparser

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
                date_u = round(datetime.now().timestamp()) + 3600 * conf_parapms['time_zone']
                date_str = datetime.fromtimestamp(date_u).strftime("%d.%m.%y %H:%M")
                query = f""" INSERT INTO co_data (date_str, date_u, co2) VALUES ("{date_str}",{date_u}, {value}) """
                cur.execute(query)
                print('Data updated')

        except Exception as e:
            print('Connection error:\n\t', e)
            pass

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

conf = configparser.ConfigParser()
conf.read('config/conf.ini')
#time_zone = сколько часов +UTC
conf_parapms = {'base_name':conf['Database']['base_name'],
                'api_base':conf['Database']['api_base'],
                'ip':conf['Server']['ip'],
                'port':int(conf['Server']['port']),
                'time_zone':int(conf['Server']['time_zone']),
                'tg_token':conf['Tg_bot']['token']}

Sever(conf_parapms['ip'], conf_parapms['port']).connect()

"""
Telegram
"""

