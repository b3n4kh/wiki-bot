#!/usr/bin/env python3

from flask import Flask
from flask_bootstrap import Bootstrap
from flask import render_template
import os


app = Flask(__name__)
Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True


@app.route("/")
def init():
    baseurl = os.environ['BOT_HOST']
    return render_template('index.html', baseurl=baseurl)
