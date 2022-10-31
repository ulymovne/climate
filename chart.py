import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import sqlite3
from datetime import datetime
import sys

# построить график с показаниями CO2 за период
def get_chart(base:str, date_start:int, date_end:int, title_chart:str):
    try:
        with sqlite3.connect(base) as db:
            cur = db.cursor()
            query = f""" SELECT date_u, co2 FROM co_data WHERE date_u BETWEEN {date_start} AND {date_end} ORDER BY date_u"""
            cur.execute(query)
            df = pd.DataFrame(cur.fetchall(), columns=['date_', 'co2'])
            df['date_'] = pd.to_datetime(df['date_'], unit='s')

            plt.figure(figsize=(10, 11))
            plt.xticks(rotation=65, fontsize=14)
            plt.title(title_chart, fontsize=25, pad=25)
            sns.lineplot(data=df, x='date_', y='co2', linewidth=2, color='r')
            plt.xlabel("Время", fontdict={'fontsize': 18}, labelpad=10)
            plt.ylabel("Уровень СО2", fontdict={'fontsize': 18}, labelpad=10)
            plt.tight_layout(pad=2, h_pad=2)
            plot_object = io.BytesIO()
            plt.savefig(plot_object)
            plot_object.name = "Chart C02"
            plot_object.seek(0)
            plt.close()

            return plot_object
    except Exception as e:
        print('Get chart - connection error:\n\t', e)
        return 'ошибка'

def get_data(base:str):
    value = [('0', 0, 0)]
    try:
        with sqlite3.connect(base) as db:
            cur = db.cursor()
            query = f""" SELECT date_str, co2, hcho FROM co_data ORDER BY id DESC LIMIT 1 """
            cur.execute(query)
            value = cur.fetchall()

    except Exception as e:
        print('Get data - connection error:\n\t', e)
    return value[0]

def add_db(data_base:str, value:list):
    try:
        with sqlite3.connect(data_base) as db:
            cur = db.cursor()
            date_u = round(datetime.now().timestamp())
            date_str = datetime.fromtimestamp(date_u).strftime("%d.%m.%y %H:%M")
            query = f""" INSERT INTO co_data (date_str, date_u, co2, hcho) VALUES ("{date_str}",{date_u}, {value[0]}, {value[1]}) """
            cur.execute(query)
            print('Data updated')

    except Exception as e:
        print('Add to db - connection error:\n\t', e)

def create_db(data_base):
    try:
        with sqlite3.connect(data_base) as db:
            cur = db.cursor()
            cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='co_data'")
            val = cur.fetchall()
            if val[0][0] == 0:
                query = """CREATE TABLE "co_data" (
                    "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                    "date_str"	TEXT,
                    "co2"	INTEGER,
                    "date_u"	INTEGER,
                    "hcho"	REAL
                    );
                    """
                cur.execute(query)
                print("The database created")
            else:
                print("The database already exists")
    except Exception as e:
        print("Error create db: \n\t", e)

if __name__ == "__main__":
    if len(sys.argv)>=3 and sys.argv[1] == '-cr':
        # проверить что базы нет и создать ее, плюс записать в conf.ini название базы
        create_db(sys.argv[2])
