# encoding:utf-8
import json, redis, settings, os, csv, time
from models import CPU
from flask import Flask
from flask import request
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta

app = Flask(__name__)
scheduler = APScheduler()

db = redis.Redis(host=settings.REDIS_SERVER, port=settings.REDIS_PORT, db=0)

def job1(a, b):
    print(str(a) + ' ' + str(b))

@app.route('/gettask')
def gettask():
    ret = {}
    carrier = request.args.get('carrier').lower()
    num = int(request.args.get('num', 1))
    if not db.llen(carrier):
        ret['status'] = 1
        ret['msg'] = 'this carrier is not exist'
        ret['data'] = []
    else:
        data = []
        min_num = db.llen(carrier) if db.llen(carrier) < num else num
        for i in range(0, min_num):
            data.append(db.lpop(carrier))
        ret['status'] = 0
        ret['data'] = data
    return json.dumps(ret)

# @app.route('/pushtask', methods=['POST'])
def pushtask(carrier=None):
    if not carrier:
        return
    print('start')
    if not db.llen(carrier) or db.llen(carrier) < 1000:
        inputFile = open(os.path.join('src', '%s.csv' % carrier), 'r')
        inputReader = csv.reader(inputFile)
        ports = list(inputReader)
        inputFile.close()
        today = datetime.utcfromtimestamp(time.time())
        for diff in range(1, 11):
            date_str = (today + timedelta(days=diff)).strftime('%Y%m%d')
            for port in ports:
                print('%s-%s:%s' % (port[0], port[1],date_str))
                db.rpush(carrier, '%s-%s:%s:1' % (port[0], port[1],date_str))
    else:
        print('it is full')




@app.route('/pause')
def pausejob():
    carrier = request.args.get('carrier').lower()
    scheduler.pause_job(carrier)
    return "Success!"

@app.route('/jobstatu')
def getstatu():
    carrier = request.args.get('carrier').lower()
    job = scheduler.get_job(carrier)
    print(dir(job))

@app.route('/resume')
def resumejob():
    scheduler.resume_job('job1')
    return "Success!"

@app.route('/addjob', methods=['GET', 'POST'])
def addjob():
    data = {}
    carrier = request.args.get('carrier').lower()
    if not carrier:
        data['status'] = 1
        data['msg'] = 'no carrier, add job error!!!'
    else:
        jobs = scheduler.get_jobs()
        for job in jobs:
            if job.id == carrier:
                break
        else:
            scheduler.add_job(func=pushtask, id=carrier, trigger='interval', seconds=10, args=[carrier])
            data['status'] = 0
            data['msg'] = 'carrier %s has added !' % carrier
        data.setdefault('status', 2)
        data.setdefault('msg', "carrier '%s' had existed !!!" % carrier)
    return json.dumps(data)

@app.route("/")
def index():
    return 'hello world'


@app.route('/showData')
def showData():
    cpus = CPU.select()
    result = {}
    return json.dumps(result)

@app.route("/saveData", methods = ['GET', 'POST'])
def saveData():
    result = {
        'statue': 'error',
        'data': "",
    }
    if request.method == "POST":
        data = request.form # 用来接收请求的数据
        try:
            model = data['model']
            model_name = data['model_name']
            stepping = data['stepping']
            microcode = data['microcode']
            cpu_MHz = data['cpu_MHz']

            cpu = CPU()
            cpu.model = model
            cpu.model_name = model_name
            cpu.stepping = stepping
            cpu.microcode = microcode
            cpu.cpu_MHz = cpu_MHz
            cpu.save()
            result['statue'] = 'success'
            result['data'] = 'your data is saved'
        except Exception as e:
            result['data'] = str(e)
    else:
        result['data'] = 'the request must be post'
    return json.dumps(result)



if __name__ == "__main__":
    scheduler.start()
    app.run(host = "0.0.0.0", port = 8000, debug = True)