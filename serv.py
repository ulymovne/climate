import time
from socket import *
import chart as chr

class Sever:
    def __init__(self, ip, port, api_base, base_name, tg_pol_api, tg):
        self.ser = socket(AF_INET, SOCK_STREAM)
        self.api_base = api_base
        self.base_name = base_name
        self.ser.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.ser.bind((ip, port))
        self.ser.listen(3)
        self.tg_pol_api = tg_pol_api
        self.tg = tg

    def connect(self):
        while True:
            user, addr = self.ser.accept()

            # !!!!!!!! записать в логи кто подключился
            print('Client connected:\n\t', addr[0], ':', addr[1])
            self.lissen(user)

    def lissen(self, user):
        curentInterval = self.tg.interval_polling
        if curentInterval == 0:
            self.sender(user, 'connected_0')
        else:
            self.sender(user, 'connected_'+str(curentInterval))
        is_work = True
        while is_work:
            try:
                data = user.recv(1024)
                if self.tg.interval_polling == curentInterval:
                    self.sender(user, 'getted')
                else:
                    self.sender(user, 'stop')
            except Exception as e:
                data = ''
                is_work = False
                print('Error data sent:\n\t', e)

            if len(data):
                msg_data = data.decode('utf-8')
                print(msg_data)

                if msg_data == "disconnect":
                    user.close()
                    is_work = False
                else:
                    try:
                        msg = msg_data.split(';')
                        if msg[0] == self.api_base:
                            chr.add_db(self.base_name, value=int(msg[1]))
                            user.close()
                            is_work = False
                        elif msg[0] == self.tg_pol_api:
                            self.tg.send(self.tg.chat_id, msg[1])
                        time.sleep(1)
                    except Exception as e:
                        print('Error in data:\n\t', e)
            else:
                print('client disconnected')
                user.close()

    def sender(self, user, text):
        user.send(text.encode('utf-8'))
