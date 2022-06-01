from flask import Flask, render_template, url_for, redirect, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/send', methods=['POST'])
def send():
    print(request.args.get('name_of_file'))
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=4996)
