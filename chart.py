import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import sqlite3

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
            #plt.show()
            plot_object = io.BytesIO()
            plt.savefig(plot_object)
            plot_object.name = "Chart C02"
            plot_object.seek(0)
            plt.close()

            return plot_object
    except Exception as e:
        print('Connection error:\n\t', e)
        return 'ошибка'
