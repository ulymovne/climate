import configparser
import threading
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
                    'tg_pol_api': conf['Tg_bot']['polling_id']
                    }



    tg1 = tg.TelegaBot(conf_parapms['tg_token'], conf_parapms['base_name'])
    tg1.start()
    tg2 = threading.Thread(target=alert, args=(tg1, conf_parapms['base_name']))
    tg2.start()
    serv1 = serv.Sever(conf_parapms['ip'], conf_parapms['port'], conf_parapms['api_base'], conf_parapms['base_name'], conf_parapms['tg_pol_api'], tg1)
    serv1.connect()


if __name__ == "__main__":
    main()