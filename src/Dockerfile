FROM alpine:latest
FROM python:3.10
WORKDIR ./scripts/
COPY . /scripts/
RUN pip install --user aiogram && pip install flask && pip install python-telegram-bot && pip install Flask-BasicAuth && pip install gunicorn && pip install python-dateutil
EXPOSE 9119
CMD ["python", "flask_bot.py"]
