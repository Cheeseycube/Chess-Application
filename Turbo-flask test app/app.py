import random
import re
import sys
from flask import Flask, render_template, request
import threading
import os
from turbo_flask import Turbo

app = Flask(__name__)
turbo = Turbo(app)


@app.route('/',  methods=["GET", "POST"])
def index():
    if request.method == "POST":
        print("post happened")
        #update_load()
        with app.app_context():
            turbo.push(turbo.replace(render_template('loadavg.html'), 'num'))
        #return render_template('index.html')
    return render_template('index.html')


@app.route('/page2')
def page2():
    return render_template('page2.html')


@app.context_processor
def inject_load():
    return {'num': random.random()}


'''def update_load():
    with app.app_context():
        while True:
            time.sleep(5)
            turbo.push(turbo.replace(render_template('loadavg.html'), 'load'))'''

if __name__ == "__main__":

    #with app.app_context():
    #    threading.Thread(target=update_load).start()

    # Start a webserver
    app.run(port=int(os.environ.get('PORT', '8080')))
