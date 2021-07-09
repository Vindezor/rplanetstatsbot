from flask import Flask, request
from views.bot_views import bot, KEY

import telebot
import os

URL_BOT = os.getenv('URL_BOT')

app = Flask(__name__)

@app.route('/' + KEY, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=URL_BOT + KEY)
    return "!", 200