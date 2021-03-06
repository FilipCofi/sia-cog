import simplejson as json
from flask import jsonify, request
from dateutil import parser
from Interface import utility, app, dataanalyzer, sysinfo, projectmgr, logmgr, dumpmgr
import jsonpickle
import pickle
import pandas
from pandas import DataFrame, Series
import numpy



@app.route('/api/status', methods=['GET'])
def apistatus():
    message = "All Good!"
    code = 200

    return jsonify({"statuscode": code, "message": message})

@app.route('/api/server/<infotype>', methods=['GET'])
def systeminfo(infotype):
    message = "Success"
    code = 200
    try:
        result = {}
        if infotype == "info":
            result = sysinfo.getSystemInfo()
        elif infotype == "cpu":
            result = sysinfo.getCPUUsage()
        elif infotype == "gpu":
            result = sysinfo.getGPUUsage()
        elif infotype == "module":
            result = sysinfo.getModuleInfo()
    except Exception as e:
        message = str(e)
        code = 500

    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/list/<srvtype>', methods=['GET'])
def apilist(srvtype):
    message = "Success"
    code = 200
    result = []
    try:
        services = projectmgr.GetServices(srvtype)
        for s in services:
            result.append(json.loads(s.servicedata));

    except Exception as e:
        code = 500
        message = str(e)

    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/list/<srvtype>/<srvname>', methods=['GET'])
def apilistwithname(srvtype, srvname):
    message = "Success"
    code = 200
    result = []
    try:
        service = projectmgr.GetService(srvtype, srvname)
        if service is None:
            raise Exception("Service API not found")

        result = json.loads(service.servicedata)

    except Exception as e:
        code = 500
        message = str(e)

    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/jobs/<id>', methods=['GET'])
def jobswithid(id):
    message = "Success"
    result = None
    code = 200
    try:
        job = projectmgr.GetJob(id)
        result = {"id": job.id, "start": job.start, "end": job.end, "message": job.message,
                  "totalepoch": job.totalepoch, "status": job.status, "createdon": job.createdon, "resultdata": {}}

        if job.status == "Running":
            epoches = []
            metrices = {}
            metricesParamAdded = False
            epochData = projectmgr.GetCurrentTraining(id)
            for e in epochData:
                epoches.append(e.epoch)
                mjson = json.loads(e.metrices)
                if metricesParamAdded == False:
                    for m in mjson:
                        metrices[m] = []
                    metricesParamAdded = True
                for m in mjson:
                   metrices[m].append(mjson[m])

            result["resultdata"] = {"epoches": epoches, "metrices": metrices}
        elif job.status == "Completed":
            if not job.result is None:
                result["resultdata"] = json.loads(job.result)

    except Exception as e:
        code = 500
        message = str(e)

    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/jobs/<srvtype>/<srvname>', methods=['GET'])
def listjobs(srvtype, srvname):
    message = "Success"
    result = []
    code = 200
    try:
        jobs = projectmgr.GetJobs(srvname, srvtype)
        for j in jobs:
            result.append({"id": j.id, "servicename": j.servicename, "servicetype": j.servicetype, "start": j.start, "end": j.end, "message": j.message, "totalepoch": j.totalepoch, "status": j.status, "createdon": j.createdon})

    except Exception as e:
        code = 500
        message = str(e)

    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/pipelinesnap/<name>/<id>', methods=['GET'])
def getpipelinesnap(name, id):
    message = "Success"
    result = None
    code = 200
    try:
        dump = dumpmgr.GetPipelineDump(id, name)
        if not dump is None:
            result = json.loads(dump.pipeline)

    except Exception as e:
        code = 500
        message = str(e)

    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/pipelinelog/<name>/<id>/<module>', methods=['GET'])
def getpipelinelog(name, id, module):
    message = "Success"
    result = None
    dtype = ""
    code = 200
    try:
        dump = dumpmgr.GetPipelineDump(id, name)
        dumpresult = pickle.loads(dump.result)

        for d in dumpresult:
            if "output->" + module  in d:
                data = dumpresult[d]
                if type(data) is DataFrame:
                    data = data.head(20).to_html()
                    dtype = "frame"
                elif type(data) is dict:
                    data = json.loads(jsonpickle.encode(data, unpicklable=False))
                    dtype = "dict"
                elif type(data) is Series:
                    data = data.to_frame()
                    data = data.head(20).to_html()
                    dtype = "frame"
                else:
                    data = json.loads(data)

                result.append({"name": d, "result": data, "dtype": dtype})

    except Exception as e:
        code = 500
        message = str(e)

    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/data/info', methods=['POST'])
def databasicinfo():
    message = "Success"
    code = 200
    result = []
    try:
        rjson = request.json
        if not "name" in rjson:
            raise Exception("Please provide name of the service")

        if not "filename" in rjson:
            raise Exception("Please provide filename")

        columns = None
        count = 5
        if "columns" in rjson:
            columns = rjson["columns"]

        if "count" in rjson:
            count = rjson["count"]

        result = dataanalyzer.basic_info(rjson["name"], rjson["filename"], columns, count)

    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/data/columns', methods=['POST'])
def datacolumns():
    message = "Success"
    code = 200
    result = []
    try:
        rjson = request.json
        if not "name" in rjson:
            raise Exception("Please provide name of the service")

        if not "filename" in rjson:
            raise Exception("Please provide filename")

        result = dataanalyzer.data_columns(rjson["name"], rjson["filename"])

    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/data/plot', methods=['POST'])
def dataplot():
    message = "Success"
    code = 200
    result = []
    try:
        rjson = request.json
        utility.validateParam(rjson, "name")
        utility.validateParam(rjson, "filename")
        utility.validateParam(rjson, "method")
        options = utility.getVal(rjson, "options")
        result = dataanalyzer.plot(rjson["name"], rjson["filename"], rjson["method"], options)

    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/logs/pred', methods=['POST'])
def predlogs():
    message = "Success"
    code = 200
    result = []
    try:
        rjson = request.get_json()
        utility.validateParam(rjson, "category")
        utility.validateParam(rjson, "servicename")
        utility.validateParam(rjson, "status")
        utility.validateParam(rjson, "start")
        utility.validateParam(rjson, "end")
        start = parser.parse(rjson["start"] + " 00:00")
        end = parser.parse(rjson["end"] + " 23:59")

        logs = logmgr.GetLogs(rjson["servicename"], rjson["category"], start, end, rjson["status"])
        for l in logs:
            result.append({"cat": l.servicetype, "name": l.servicename, "start": l.start, "end": l.end, "duration": l.duration, "status": l.status, "message": l.message})

    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/users/create', methods=['POST'])
def createuser():
    message = "Success"
    code = 200
    result = []
    try:
        rjson = request.get_json()
        utility.validateParam(rjson, "username")
        utility.validateParam(rjson, "password")
        utility.validateParam(rjson, "name")
        projectmgr.CreateUser(rjson["username"], rjson["password"], rjson["name"], rjson["email"])

    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/users/update/<username>', methods=['POST'])
def updateuser(username):
    message = "Success"
    code = 200
    result = []
    try:
        rjson = request.get_json()
        utility.validateParam(rjson, "name")
        projectmgr.UpdateUser(username, rjson["name"], rjson["email"])

    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/users/changepwd/<username>', methods=['POST'])
def updateuserpassword(username):
    message = "Success"
    code = 200
    result = []
    try:
        rjson = request.get_json()
        utility.validateParam(rjson, "currentpassword")
        utility.validateParam(rjson, "password")
        valid = projectmgr.ValidateUser(username, rjson["currentpassword"])
        if valid:
            projectmgr.UpdateUserPassword(username, rjson["password"])
        else:
            raise Exception("Please enter valid current password")

    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/users/validate', methods=['POST'])
def validateuser(username):
    message = "Success"
    code = 200
    result = False
    try:
        rjson = request.get_json()
        utility.validateParam(rjson, "username")
        utility.validateParam(rjson, "password")
        result = projectmgr.ValidateUser(rjson["username"], rjson["password"])
    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/logs/topcalls', methods=['GET'])
def topcalls():
    message = "Success"
    code = 200
    result = []
    try:
        logs = logmgr.GetTopCalls()
        for l in logs:
            result.append({"servicename": l.servicename, "servicetype": l.servicetype, "count": l.count})
        result = json.loads(json.dumps(result))
    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})

@app.route('/api/logs/toperrors', methods=['GET'])
def toperrors():
    message = "Success"
    code = 200
    result = []
    try:
        logs = logmgr.GetTopErrors()
        for l in logs:
            result.append({"servicename": l.servicename, "servicetype": l.servicetype, "count": l.count})
        result = json.loads(json.dumps(result))
    except Exception as e:
        message = str(e)
        code = 500
    return jsonify({"statuscode": code, "message": message, "result": result})
