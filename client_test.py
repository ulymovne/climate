from socket import *
import configparser

conf = configparser.ConfigParser()
conf.read('config/conf.ini')
conf_parapms = {'ip':conf['Server']['ip'],
                'port':int(conf['Server']['port'])}

soc = socket(AF_INET, SOCK_STREAM)
soc.connect((conf_parapms['ip'], conf_parapms['port']))

try:
    msg = soc.recv(1024).decode('utf-8')
    if msg.startswith('connected_'):
        print('Connected')
        is_work = True
        while is_work:
            send_text = input('Enter key and values:\n')
            if send_text:
                soc.send(send_text.encode('utf-8'))
                while soc.recv(1024).decode('utf-8') != 'getted':
                    soc.send(send_text.encode('utf-8'))
                print('Data send')
                #is_work = False
            else:
                is_work = False

except Exception as e:
    print(e)
