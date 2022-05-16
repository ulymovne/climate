from socket import *
import chart as chr

class Sever:
    def __init__(self, ip, port, api_base, base_name):
        self.ser = socket(AF_INET, SOCK_STREAM)
        self.api_base = api_base
        self.base_name = base_name
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
                    if msg[0] == self.api_base:
                        chr.add_db(self.base_name, value=int(msg[1]))
                        is_work = False
                except Exception as e:
                    print('Error in data:\n\t', e)

            else:
                print('client disconnected')
                is_work = False

    def sender(self, user, text):
        user.send(text.encode('utf-8'))
