from flask import Flask
from os import getenv

app = Flask(__name__)


@app.route("/", methods=["GET", "HEAD"])
def index():
    return '<h1>Telegram Bot by Vlad Synytsyn</h1>'


if __name__ == '__main__':
    context = ('cert.pem', 'key.pem')
    app.run(host='0.0.0.0', port=getenv('PORT', 80), ssl_context=context)
