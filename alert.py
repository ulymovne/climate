import time
import chart as chr
import telega as tg

def alert(mybot:tg.TelegaBot, base_name, chat_id):
    while True:
        if mybot.alert > 0:
            cur_co2 = chr.get_data(base_name)[1]
            if cur_co2 > mybot.alert:
                mybot.send(chat_id, f'*Тревога! Показания CO2 завышены: {cur_co2}*')
        time.sleep(180)