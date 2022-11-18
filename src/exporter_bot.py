import json
import logging
import random
from time import sleep
import psycopg2
import pytz
import telegram
from aiogram.utils.exceptions import RetryAfter, NetworkError
from dateutil import parser
from flask import request, Flask
from flask_basicauth import BasicAuth
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)  # создание ip-адреса во Flask
metrics = PrometheusMetrics(app)  # добавление ip-адреса в Prometheus, чтобы тот смог сгенерировать дефолтные метрики
app.secret_key = 'lAlAlA123'  # создание секретного ключа
basic_auth = BasicAuth(app)

chatID = "-1001793852701"  # ID чата, в который бот будет отправлять сообщения(алерты)

app.config['BASIC_AUTH_FORCE'] = False
app.config['BASIC_AUTH_USERNAME'] = 'XXXUSERNAME'
app.config['BASIC_AUTH_PASSWORD'] = 'XXXPASSWORD'

bot = telegram.Bot(token="1968302406:AAHjhuHBhYjxAuySyCWq0H5UBoRr35kRN1I")  # присваивание переменой бота токена,
# который был выдан при создании


@app.route('/alert', methods=['POST'])  # данная строка говорит, что нижестоящая функция будет вызвана при эндпоинте
# /alert. В нашем случае на этот эндпоинт отправляет алерты alertmanager
def postAlertmanager():
    message = ""
    # Ниже в блоке try заполняется сообщение, которое впоследствии будет отправлено ботом. В блоках except прописаны
    # возможные исключения, которые могут возникнуть в блоке try
    try:
        content = json.loads(request.get_data())
        for alert in content['alerts']:
            if alert['status'] == 'firing':
                message = "\ud83d\udd34: "+alert['status'] + "\n"
            elif alert['status'] == 'resolved':
                message = "\u2705: " + alert['status'] + "\n"
            if 'alertname' in alert['labels']:
                message += "\ud83d\udcdd: "+alert['labels']['alertname'] + "\n"
            if 'summary' in alert['annotations']:
                message += "\ud83d\udccb: "+alert['annotations']['summary']+"\n"
            if 'description' in alert['annotations']:
                message += "\u2747\ufe0f: " + "Количество заказов: " + alert['annotations']['description']+"\n"
            # if alert['status'] == "firing":
            if 'startsAt' in alert:
                a = parser.parse(alert['startsAt']).astimezone(pytz.timezone('Europe/Moscow'))
                correctDate = a.strftime('%Y-%m-%d %H:%M:%S')
                message += "\ud83d\udcc6: " + correctDate
            bot.sendMessage(chat_id=chatID, text=message)
            return "Alert OK", 200
    except RetryAfter:
        sleep(30)
        bot.sendMessage(chat_id=chatID, text=message)
        return "Alert OK", 200
    except NetworkError as e:
        sleep(60)
        bot.sendMessage(chat_id=chatID, text=message)
        return "Alert OK", 200
    except Exception as error:
        bot.sendMessage(chat_id=chatID, text="Error: "+str(error))
        app.logger.info("\t%s", error)
        return "Alert fail", 200


common_counter = metrics.counter(
    'by_endpoint_counter', 'Request count by endpoints',
    labels={'endpoint': lambda: request.endpoint}
)
common_gauge = metrics.gauge('test_gauge', 'Request gauge by endpoints',
                             labels={'endpoint': lambda: request.endpoint, 'url': lambda: request.url})
info = metrics.info('dynamic_info', 'Something dynamic')
# Выше создаются собственноручные метрики разных типов: counter, gauge, info.


# Функция ниже проверяет работу метрики типа counter по эндпоинту /common/one
@app.route('/common/one')
@common_counter
def endpoint_one():
    return str(24)


# Функция ниже проверяет работу метрики типа gauge по эндпоинту /gauge/one
@app.route('/gauge/one')
@common_gauge
def endpoint_three():
    common_gauge.set(100)
    return str(20)


# В функции ниже записывается значение из базы данных в метрику dynamic_info по эндпоинту gauge/two
@app.route('/gauge/two')
@common_gauge
def endpoint_four():
    a = db_request()[0]  # Получение значения из базы данных
    info.set(a)
    return str(a)


# Создание дефолтной метрики типа counter, которая подсчитывает значения при всез эндпоинтах
metrics.register_default(
    metrics.counter(
        'by_path_counter', 'Request count by request paths',
        labels={'path': lambda: request.path}
    )
)


# Функция для общения с базой данных
def db_request():
    conn = psycopg2.connect("dbname=postgres user=postgres password=postgres")
    cur = conn.cursor()
    cur.execute("INSERT INTO public.user (id, name, surname) VALUES (%s, %s, %s)", (random.randint(0, 100), "Pavel", "Tol"))
    # cur.execute("INSERT INTO public.user (id, name, surname) VALUES (%s, %s, %s)", (5, "Vl", "Koloskov"))
    # cur.execute("DELETE FROM public.user WHERE ID = %s", str(4))
    cur.execute("SELECT id FROM public.user")
    res = cur.fetchall()
    print(res[len(res) - 1])
    conn.commit()
    cur.close()
    conn.close()
    return res[len(res) - 1]


# Запуск скрипта
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run('0.0.0.0', 7896, threaded=True)  # Поднятие ip-адреса Flask на порту 7896
