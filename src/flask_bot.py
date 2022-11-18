from time import sleep

import json
import logging
import pytz
import telegram
from aiogram.utils.exceptions import RetryAfter, NetworkError
from dateutil import parser
from flask import Flask
from flask import request
from flask_basicauth import BasicAuth

app = Flask(__name__)
app.secret_key = 'lAlAlA123'
basic_auth = BasicAuth(app)

chatID = "-1001793852701"

app.config['BASIC_AUTH_FORCE'] = False
app.config['BASIC_AUTH_USERNAME'] = 'XXXUSERNAME'
app.config['BASIC_AUTH_PASSWORD'] = 'XXXPASSWORD'

bot = telegram.Bot(token="1968302406:AAHjhuHBhYjxAuySyCWq0H5UBoRr35kRN1I")


@app.route('/alert', methods=['POST'])
def postAlertmanager():
    message = ""
    try:
        content = json.loads(request.get_data())
        for alert in content['alerts']:
            message = "\ud83d\udd34: "+alert['status'] + "\n"
            if 'alertname' in alert['labels']:
                message += "\ud83d\udcdd: "+alert['labels']['alertname'] + "\n"
            if 'summary' in alert['annotations']:
                message += "\ud83d\udccb: "+alert['annotations']['summary']+"\n"
            if 'description' in alert['annotations']:
                message += "\u2747\ufe0f: "+alert['annotations']['description']+"\n"
            # if alert['status'] == "firing":
            if 'startsAt' in alert:
                a = parser.parse(alert['startsAt']).astimezone(pytz.timezone('Europe/Moscow'))
                correctDate = a.strftime('%Y-%m-%d %H:%M:%S')
                message += "\ud83d\udcc6: "+correctDate
            bot.sendMessage(chat_id=chatID, text=message)
            return "Alert OK", 200
    except RetryAfter:
        sleep(30)
        bot.sendMessage(chat_id=chatID, text=message)
        return "Alert OK", 200
    # except TimedOut as e:
    #     sleep(60)
    #     bot.sendMessage(chat_id=chatID, text=message)
    #     return "Alert OK", 200
    except NetworkError:
        sleep(60)
        bot.sendMessage(chat_id=chatID, text=message)
        return "Alert OK", 200
    except Exception as error:
        bot.sendMessage(chat_id=chatID, text="Error: "+str(error))
        app.logger.info("\t%s", error)
        return "Alert fail", 200


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=9119)
