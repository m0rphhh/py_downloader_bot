from flask import Flask, render_template, url_for, redirect, request
from decouple import config

app = Flask(__name__)


@app.route('/')
def index():
    token = request.headers.getlist('access_token')
    print(token)
    return render_template('index.html', token=token)


if __name__ == "__main__":
    app.run(debug=True, host=config('WEB_HOST'), port=4996)
