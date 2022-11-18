#!/usr/bin/env  python3
import sys
sys.path
sys.executable

import os
import psycopg2
import logging
from logging import StreamHandler, Formatter
from prometheus_client import CollectorRegistry, Counter, push_to_gateway

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(Formatter(fmt='%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)

logger.info("Запуск скрипта taxi_metric")

registry = CollectorRegistry()

taxi_status_metric = Counter('taxi_status', 'Доставки на такси в статусах', ["taxi_name", "status", "processType"], registry=registry)

OrdersForReceipt = {}

#############################################################################################################################################################

try:
    logger.info("Подключение к базе данных delivery")
    conn = psycopg2.connect("dbname=" + os.environ['taxi_dbname'] + " user=" + os.environ['taxi_user'] + " password=" + os.environ['taxi_password'] + " host=" + os.environ['taxi_host'] + " port=" + os.environ['port'])

    logger.info("Получение курсора от БД delivery")
    cur = conn.cursor()

    logger.info("Запрос в базу данных delivery")
    cur.execute("select order_number, context from reserve.delivery where update_time > now() - INTERVAL '30 MINUTES';")

    logger.info("Сохранение результата от delivery в переменную")
    answer = cur.fetchall()

    logger.info("Подтверждение изменений в БД delivery")
    conn.commit()

    logger.info("Закрытие курсора в БД delivery")
    cur.close()

    logger.info("Завершение подключения к БД delivery")
    conn.close()

except BaseException:
    logger.info("Ошибка: Ошибка при подключении к БД")
    exit()

logger.info("Создание метрик по статусам заказов в delivery")

#print(answer)

for row in answer:

    if row[1]["type"] not in OrdersForReceipt:
        
        OrdersForReceipt[row[1]["type"]] = []
        
        OrdersForReceipt[row[1]["type"]].append(row[0])
    else:
        OrdersForReceipt[row[1]["type"]].append(row[0])

    logger.info("Заказ в статусах: " + str(row[1]["type"]) + " " + str(row[1]["status"]["text"] + " " + str(row[1]["processType"])))

    taxi_status_metric.labels(row[1]["type"], row[1]["status"]["text"], row[1]["processType"]).inc()

########################################################################################################################################3
try:

    logger.info('Отправка метрик в pushgateway')

    push_to_gateway('https://pushgateway.lards.yc.mvideo.ru', job='taxi_custom_metrics', registry=registry)

except BaseException:

    logger.info("Ошибка: Ошибка при отправке метрик в pushgateway")

    exit()

logger.info("Успешное выполнение скрипта taxi_metric")
