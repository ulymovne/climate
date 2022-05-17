import configparser
import threading
import time

import telega as tg
import serv
from alert import alert


def main():
    conf = configparser.ConfigParser()
    conf.read('config/conf.ini')
    conf_parapms = {'base_name': conf['Database']['base_name'],
                    'api_base': conf['Database']['api_base'],
                    'ip': conf['Server']['ip'],
                    'port': int(conf['Server']['port']),
                    'tg_token': conf['Tg_bot']['token'],
                    'tg_chat_id': conf['Tg_bot']['chat_id']
                    }

    def service_polling(tg_:tg.TelegaBot, serv_:serv.Sever):
        while True:
            if tg_.interval_polling > 0:
                serv_.intrval_polling = tg_.interval_polling
                tg_.interval_polling = 0
            time.sleep(20)

    tg1 = tg.TelegaBot(conf_parapms['tg_token'], conf_parapms['base_name'])
    tg1.start()
    tg2 = threading.Thread(target=alert, args=(tg1, conf_parapms['base_name'], conf_parapms['tg_chat_id']))
    tg2.start()
    serv1 = serv.Sever(conf_parapms['ip'], conf_parapms['port'], conf_parapms['api_base'], conf_parapms['base_name'])
    threading.Thread(target=service_polling, args=(tg1, serv1)).start()
    serv1.connect()


if __name__ == "__main__":
    main()