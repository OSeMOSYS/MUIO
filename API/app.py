#import sys
import os
import sys

from flask import Flask, Response, jsonify, request, session, render_template
from flask_cors import CORS
from datetime import timedelta
# from pathlib import Path

#import json
from Classes.Base import Config
# from API.Classes.Base.SyncS3 import SyncS3
from Routes.Upload.UploadRoute import upload_api
from Routes.Case.CaseRoute import case_api
from Routes.Case.SyncS3Route import syncs3_api
from Routes.Case.ViewDataRoute import viewdata_api
from Routes.DataFile.DataFileRoute import datafile_api

import logging
import warnings
from logging.handlers import TimedRotatingFileHandler, QueueHandler
from queue import Queue, Empty

from threading import Event

#RADI
template_dir = os.path.abspath('WebAPP')
static_dir = os.path.abspath('WebAPP')


# ========================= DELETE LOG FILE ON START =========================
logfile =  os.path.join(static_dir, "app.log")

if os.path.exists(logfile):
    try:
        os.remove(logfile)
    except PermissionError:
        pass


# ============= File + Console Logger ============
logger = logging.getLogger()
logger.setLevel(logging.INFO)

fmt = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")

# file (daily rotation, keep 7 days)
fh = TimedRotatingFileHandler(
    logfile, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
fh.setFormatter(fmt)
logger.addHandler(fh)

# console
ch = logging.StreamHandler()
ch.setFormatter(fmt)
logger.addHandler(ch)



# ============= Capture warnings (Pandas etc.) ============
logging.captureWarnings(True)
warnings.simplefilter("default")  # show all FutureWarning, DeprecationWarning...

# ============= Flask / Werkzeug ============
# logging.getLogger("werkzeug").setLevel(logging.INFO)
# logging.getLogger("werkzeug").propagate = True

# logging.getLogger("flask.app").setLevel(logging.INFO)
# logging.getLogger("flask.app").propagate = True

# ============= Capture unhandled exceptions ============
def log_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("UNCAUGHT EXCEPTION", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = log_exception

# OPTIONAL: capture stdout and stderr
# sys.stdout = open("app.log", "a", encoding="utf-8")
# sys.stderr = open("app.log", "a", encoding="utf-8")

# ============= end logger             ============



app = Flask(__name__, static_url_path='', static_folder=static_dir,  template_folder=template_dir)

app.permanent_session_lifetime = timedelta(days=5)
app.config['SECRET_KEY'] = '12345'
app.config["MAX_CONTENT_LENGTH"] = None

app.register_blueprint(upload_api)
app.register_blueprint(case_api)
app.register_blueprint(viewdata_api)
app.register_blueprint(datafile_api)
app.register_blueprint(syncs3_api)

CORS(app)

#potrebno kad je front end na drugom serveru 127.0.0.1
@app.after_request
def add_headers(response):
    if Config.HEROKU_DEPLOY == 0: 
        #localhost
        response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1')
    else:
        #HEROKU
        response.headers.add('Access-Control-Allow-Origin', 'https://osemosys.herokuapp.com/')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    #response.headers['Content-Type'] = 'application/javascript'
    return response

# @app.errorhandler(CustomException)
# def handle_invalid_usage(error):
#     response = jsonify(error.to_dict())
#     response.status_code = error.status_code
#     return response

#entry point to frontend
@app.route("/", methods=['GET'])
def home():
    #sync bucket with local storage
    # if Config.AWS_SYNC == 1:
    #     syncS3 = SyncS3()
    #     cases = syncS3.getCasesSyncInit()
    #     for case in cases:
    #         syncS3.downloadSync(case, Config.DATA_STORAGE, Config.S3_BUCKET)
    #     #downoload param file from S3 bucket
    #     syncS3.downloadSync('Parameters.json', Config.DATA_STORAGE, Config.S3_BUCKET)
    return render_template('index.html')

@app.route("/getSession", methods=['GET'])
def getSession():
    try:
        ses = session.get('osycase', None) or None
        response = {
            "session":ses
        }
        return jsonify(response), 200
    except( KeyError ):
        return jsonify('No selected parameters!'), 404

@app.route("/setSession", methods=['POST'])
def setSession():
    try:
        cs = request.json['case']
        #session.permanent= True
        session['osycase'] = cs
        response = {"osycase": session['osycase']}
        return jsonify(response), 200
    except( KeyError ):
        return jsonify('No selected parameters!'), 404


if __name__ == '__main__':
# if __name__ == 'app':
    #potrebno radi module js importa u index.html ES6 modules
    #Flask.__version__
    import mimetypes
    mimetypes.add_type('application/javascript', '.js')
    port = int(os.environ.get("PORT", 5002))
    if Config.HEROKU_DEPLOY == 0: 
        from waitress import serve
        serve(app, host='127.0.0.1', port=port,  threads=8)
    else:
        #HEROKU
        app.run(host='0.0.0.0', port=port, debug=True)
        #app.run(host='127.0.0.1', port=port, debug=True)

