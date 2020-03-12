from flask import Flask, request
from os import getenv

from telebot.types import Update

from spacebot.app.bot import restore_users, bot

app = Flask(__name__)


@app.route("/", methods=["GET", "HEAD"])
def index():
    return '<h1>Telegram Bot by Vlad Synytsyn</h1>'


@app.route('/', methods=['POST'])
def webhook():
    json_request = request.get_json()
    update = Update.de_json(json_request)
    bot.process_new_updates([update])
    return ''


if __name__ == '__main__':
    restore_users()
    app.run(host='0.0.0.0', port=getenv('PORT', 80))
