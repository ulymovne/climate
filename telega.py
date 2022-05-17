import threading
from telebot import types, TeleBot
from datetime import datetime, timedelta
import chart as chr


class TelegaBot(threading.Thread):

    def __init__(self, token, basename):
        super().__init__()
        self.bot = TeleBot(token)
        self.basename = basename
        self.alert = 0
        self.interval_polling = 0


    def run(self):

        def set_commands():
            commands = [
                types.BotCommand(command="/get", description="Получить текущие показания"),
                types.BotCommand(command="/polling", description="Включить опрос"),
                types.BotCommand(command="/chart", description="Построить график"),
                types.BotCommand(command="/alert", description="Настроить алерт")
            ]
            self.bot.set_my_commands(commands)

        def get_markup(markup_type: str):
            markup = types.InlineKeyboardMarkup()
            if markup_type == "pool":
                b1 = types.InlineKeyboardButton('30 секунд', callback_data='pool_1')
                b2 = types.InlineKeyboardButton('60 секунд', callback_data='pool_2')
                b3 = types.InlineKeyboardButton('120 секунд', callback_data='pool_3')
                b4 = types.InlineKeyboardButton('Отключить', callback_data='pool_0')
                markup.row(b1, b2, b3)
                markup.row(b4)
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
                b5 = types.InlineKeyboardButton('Отключить', callback_data='alert_0')
                markup.row(b1, b2)
                markup.row(b3, b4)
                markup.row(b5)
            back = types.InlineKeyboardButton('Отмена', callback_data='back_')
            markup.row(back)
            return markup

        def set_chart(call, number):
            date_start, date_end, title_chart = 0, 0, ''
            if number == '1':
                date_start = round((datetime.now() - timedelta(days=1)).timestamp())
                date_end = round(datetime.now().timestamp())
                title_chart = 'Показания СО2 за последние сутки'
            elif number == '2':
                date_start = round((datetime.now() - timedelta(hours=12)).timestamp())
                date_end = round(datetime.now().timestamp())
                title_chart = 'Показания СО2 за последние 12 часов'
            elif number == '3':
                cur_date = datetime.today()
                date_start = round(
                    (cur_date.combine(cur_date.date(), cur_date.min.time()) - timedelta(days=1)).timestamp())
                date_end = round((cur_date.combine(cur_date.date(), cur_date.min.time())).timestamp())
                title_chart = 'Показания СО2 за вчерашние сутки'

            self.bot.send_photo(chat_id=call.message.chat.id,
                           photo=chr.get_chart(self.basename, date_start, date_end, title_chart))

        def set_alert(number):
            values = {'0': 0, '1': 1000, '2': 1200, '3': 1400, '4': 1600}
            if number in values:
                self.alert = values[number]

        def set_polling(number):
            values = {'0': 0, '1': 30, '2': 60, '3': 120}
            if number in values:
                self.interval_polling = values[number]

        @self.bot.message_handler(commands=['get'])
        def answer(message):
            data = chr.get_data(self.basename)
            self.bot.send_message(message.chat.id, data[0] + ", показания CO2: *" + str(data[1]) + "*",
                             parse_mode='Markdown')

        @self.bot.message_handler(commands=['polling'])
        def answer(message):
            self.bot.send_message(message.chat.id, 'Частота опроса:', reply_markup=get_markup('pool'))

        @self.bot.message_handler(commands=['chart'])
        def answer(message):
            self.bot.send_message(message.chat.id, 'Какой график построить:', reply_markup=get_markup('chart'))

        @self.bot.message_handler(commands=['alert'])
        def answer(message):
            self.bot.send_message(message.chat.id, f'Выберете порог. Сейчас установлено: {self.alert}', reply_markup=get_markup('alert'))

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle(call):
            markup_type, number = call.data.split("_")
            if markup_type == 'pool':
                # может тут перестать записывать в базу? и ограничить тайминг на 5-10 минут макс.
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text="Опрос с частотой:")
                set_polling(number)
            elif markup_type == 'chart':
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text="Строим график:")
                set_chart(call, number)
            elif markup_type == 'alert':
                if number == '0':
                    text_ = "Алерт отключен"
                else:
                    text_ = "Запуск алерта:"
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                      text=text_)
                set_alert(number)
            elif markup_type == 'back':
                self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Отмена")
            self.bot.answer_callback_query(call.id)

        set_commands()
        #self.bot.polling(none_stop=True)
        self.bot.infinity_polling()

    def send(self, chat_id, text_):
        self.bot.send_message(chat_id, text=text_, parse_mode='Markdown')


