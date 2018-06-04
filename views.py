# encoding:utf-8
import json, redis, settings, os, csv, time
from flask import Flask
from flask import request
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta

app = Flask(__name__)
scheduler = APScheduler()

db = redis.Redis(host=settings.REDIS_SERVER, port=settings.REDIS_PORT, db=0)

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

@app.route('/pushcmd', method=['GET', 'POST'])
def pushcmd():
    host = request.args.get('carrier').lower()
    datas = request.form
    ret = {}
    if not datas or not len(datas):
        ret['status'] = 2
        ret['msg'] = 'data is empty !'
    elif len(datas) > 100:
        ret['status'] = 1
        ret['msg'] = 'data is too much!'
    else:
        item = 0
        for data in datas:
            cmds = data.get('cmds')
            devices = data.get('devices')
            if not cmds or not devices or not len(cmds) or not len(devices):
                continue
            for cmd in cmds:
                for device in devices:
                    item += 1
                    db.rpush(device, cmd)
        ret['status'] = 0
        ret['msg'] = 'has pushed %s items' % item
    return json.dumps(ret)

@app.route('/getcmd')
def getcmd():
    ret = {}
    host = request.args.get('host').lower()
    cmd = []
    while db.llen(host):
        cmd.append(db.lpop())
    if not len(cmd):
        ret['status'] = 1
        ret['msg'] = 'there is no command!'
        ret['data'] = []
    else:
        ret['status'] = 0
        ret['msg'] = ''
        ret['data'] = cmd
    return json.dumps(ret)

@app.route('/pause')
def pausejob():
    ret = {}
    carrier = request.args.get('carrier').lower()
    scheduler.pause_job(carrier)
    ret['status'] = 0
    ret['msg'] = 'pause success!'
    return json.dumps(ret)

@app.route('/getjobs')
def getstatus():
    ret = {}
    jobs = scheduler.get_jobs()
    ret['status'] = 0
    ret['jobs'] = jobs
    return json.dumps(ret)

@app.route('/resume')
def resumejob():
    ret = {}
    carrier = request.args.get('carrier').lower()
    scheduler.resume_job(carrier)
    ret['status'] = 0
    ret['msg'] = 'resume success!'
    return json.dumps(ret)

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

if __name__ == "__main__":
    scheduler.start()
    app.run(host = "0.0.0.0", port = 8000, debug = True)