from flask import Blueprint, jsonify, request, send_file, session
from pathlib import Path
import shutil, datetime, time, os
from Classes.Case.DataFileClass import DataFile
from Classes.Base import Config
from Classes.Base.Response import api_response

datafile_api = Blueprint('DataFileRoute', __name__)

@datafile_api.route("/generateDataFile", methods=['POST'])
def generateDataFile():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']

        if casename != None:
            txtFile = DataFile(casename)
            txtFile.generateDatafile(caserunname)
            response = {
                "message": "You have created data file!",
                "status_code": "success"
            }      
        return api_response(success=True, message=response["message"], data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/createCaseRun", methods=['POST'])
def createCaseRun():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        data = request.json['data']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.createCaseRun(caserunname, data)
     
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/updateCaseRun", methods=['POST'])
def updateCaseRun():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        oldcaserunname = request.json['oldcaserunname']
        data = request.json['data']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.updateCaseRun(caserunname, oldcaserunname, data)
     
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/deleteCaseRun", methods=['POST'])
def deleteCaseRun():
    try:        
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        resultsOnly = request.json['resultsOnly']
        
        casePath = Path(Config.DATA_STORAGE, casename, 'res', caserunname)
        if not resultsOnly:
            shutil.rmtree(casePath)
        else:
            for item in os.listdir(casePath):
                item_path = os.path.join(casePath, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)  # delete file
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)  # delete subfolder

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.deleteCaseRun(caserunname, resultsOnly)    
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)
    except OSError:
        return api_response(success=False, message="OS Error deleting case run", status_code=500)

@datafile_api.route("/deleteScenarioCaseRuns", methods=['POST'])
def deleteScenarioCaseRuns():
    try:
        scenarioId = request.json['scenarioId']
        casename = request.json['casename']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.deleteScenarioCaseRuns(scenarioId)
     
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/saveView", methods=['POST'])
def saveView():
    try:
        casename = request.json['casename']
        param = request.json['param']
        data = request.json['data']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.saveView(data, param)
     
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/updateViews", methods=['POST'])
def updateViews():
    try:
        casename = request.json['casename']
        param = request.json['param']
        data = request.json['data']

        if casename != None:
            caserun = DataFile(casename)
            response = caserun.updateViews(data, param)
     
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/readDataFile", methods=['POST'])
def readDataFile():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        if casename != None:
            txtFile = DataFile(casename)
            data = txtFile.readDataFile(caserunname)
            response = data    
        else:  
            response = None     
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)
    
@datafile_api.route("/validateInputs", methods=['POST'])
def validateInputs():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        if casename != None:
            df = DataFile(casename)
            validation = df.validateInputs(caserunname)
            response = validation    
        else:  
            response = None     
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/downloadDataFile", methods=['GET'])
def downloadDataFile():
    try:
        #casename = request.json['casename']
        #casename = 'DEMO CASE'
        # txtFile = DataFile(casename)
        # downloadPath = txtFile.downloadDataFile()
        # response = {
        #     "message": "You have downloaded data.txt to "+ str(downloadPath) +"!",
        #     "status_code": "success"
        # }         
        # return jsonify(response), 200
        #path = "/Examples.pdf"
        case = session.get('osycase', None)
        caserunname = request.args.get('caserunname')
        dataFile = Path(Config.DATA_STORAGE,case, 'res',caserunname, 'data.txt')
        return send_file(dataFile.resolve(), as_attachment=True, max_age=0)
    
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/downloadFile", methods=['GET'])
def downloadFile():
    try:
        case = session.get('osycase', None)
        file = request.args.get('file')
        dataFile = Path(Config.DATA_STORAGE,case,'res','csv',file)
        return send_file(dataFile.resolve(), as_attachment=True, max_age=0)
    
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/downloadCSVFile", methods=['GET'])
def downloadCSVFile():
    try:
        case = session.get('osycase', None)
        file = request.args.get('file')
        caserunname = request.args.get('caserunname')
        dataFile = Path(Config.DATA_STORAGE,case,'res',caserunname,'csv',file)
        return send_file(dataFile.resolve(), as_attachment=True, max_age=0)
    
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/downloadResultsFile", methods=['GET'])
def downloadResultsFile():
    try:
        case = session.get('osycase', None)
        caserunname = request.args.get('caserunname')
        dataFile = Path(Config.DATA_STORAGE,case, 'res', caserunname,'results.txt')
        return send_file(dataFile.resolve(), as_attachment=True, max_age=0)
    
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)

@datafile_api.route("/run", methods=['POST'])
def run():
    try:
        casename = request.json['casename']
        caserunname = request.json['caserunname']
        solver = request.json['solver']
        txtFile = DataFile(casename)
        response = txtFile.run(solver, caserunname)     
        return api_response(success=True, data=response, status_code=200)
    
    except(IOError):
        return api_response(success=False, message="No existing cases!", status_code=404)
    
@datafile_api.route("/batchRun", methods=['POST'])
def batchRun():
    try:
        start = time.time()
        modelname = request.json['modelname']
        cases = request.json['cases']

        if modelname != None:
            txtFile = DataFile(modelname)
            for caserun in cases:
                txtFile.generateDatafile(caserun)

            response = txtFile.batchRun( 'CBC', cases) 
        end = time.time()  
        response['time'] = end-start 
        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="Error during batch run", status_code=500)
    
@datafile_api.route("/cleanUp", methods=['POST'])
def cleanUp():
    try:
        modelname = request.json['modelname']

        if modelname != None:
            model = DataFile(modelname)
            response = model.cleanUp()    

        return api_response(success=True, data=response, status_code=200)
    except(IOError):
        return api_response(success=False, message="Error during cleanup", status_code=500)