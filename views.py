# encoding:utf-8
import json, redis, settings, os, csv, time, logging
from flask import Flask
from flask import request
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta

app = Flask(__name__)
scheduler = APScheduler()

db = redis.Redis(host=settings.REDIS_SERVER, port=settings.REDIS_PORT, db=0)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)


@app.route('/heartbeat')
def heartbeat():
    ret = {}
    carrier = request.args.get('carrier').lower()
    permins = request.args.get('permins')
    host = request.args.get('host')
    num = request.args.get('num')
    key = '%s:%s:%s' % (host, carrier, num)
    db.set(settings.SPIDER + key, time.time())
    db.set(settings.PER_MINS + key, permins)
    ret['status'] = 0
    return json.dumps(ret)

@app.route('/getspiders')
def get_spiders():
    ret = {}
    keys = db.keys(settings.SPIDER + '*')
    ret['data'] = []
    for key in keys:
        last_time = db.get(key)
        index = key.find(':') + 1
        pure_key = key[index:]
        permins = db.get(settings.PER_MINS + pure_key)
        item = dict(
            name=pure_key,
            last_time=last_time,
            permins=permins,
        )
        ret['data'].append(item)
    return json.dumps(ret)


# 0为正在运行，1为暂停，　2为还没添加
@app.route('/getstatic')
def get_static():
    logging.debug('get static')
    ret = {}
    ret['status'] = 0
    keys = db.keys(settings.STATIC + '*')
    ret['data'] = []
    for carrier in settings.CARRIER:
        static = db.get(settings.STATIC + carrier)
        task_key = settings.TASK + carrier
        item = dict(
            carrier=carrier,
            num=db.llen(task_key),
            static=static if static else 2,
        )
        ret['data'].append(item)
    return json.dumps(ret)


@app.route('/removetask')
def remove_task():
    ret = {}
    carrier = request.args.get('carrier').lower()
    static_key = settings.STATIC + carrier
    db.set(static_key, 2)
    scheduler.remove_job(id=carrier)
    ret['status'] = 0
    return json.dumps(ret)



@app.route('/gettask')
def get_task():
    ret = {}
    carrier = request.args.get('carrier').lower()
    num = int(request.args.get('num', 1))
    key = settings.TASK + carrier
    if not db.llen(key):
        ret['status'] = 1
        ret['msg'] = 'this carrier is not exist'
        ret['data'] = []
    else:
        data = []
        min_num = db.llen(key) if db.llen(key) < num else num
        for i in range(0, min_num):
            data.append(db.lpop(key))
        ret['status'] = 0
        ret['data'] = data
    return json.dumps(ret)


# @app.route('/pushtask', methods=['POST'])
def push_task(carrier=None):
    if not carrier:
        return
    key = settings.TASK + carrier
    if not db.llen(key) or db.llen(key) < 1000:
        # inputFile = open(str(settings.BASE_DIR + 'src/' + '%s.csv' % carrier), 'r')
        inputFile = open(os.path.join('src', '%s.csv' % carrier), 'r')
        inputReader = csv.reader(inputFile)
        ports = list(inputReader)
        inputFile.close()
        today = datetime.utcfromtimestamp(time.time())
        for diff in range(1, 11):
            date_str = (today + timedelta(days=diff)).strftime('%Y%m%d')
            for port in ports:
                print('%s-%s:%s' % (port[0], port[1], date_str))
                db.rpush(key, '%s-%s:%s:1' % (port[0], port[1], date_str))
    else:
        print('%s is full' % carrier)


@app.route('/pushcmd', methods=['GET', 'POST'])
def push_cmd():
    ret = {}
    data = request.get_data()
    json_dict = json.loads(data)
    # devices = request.form.get('devices', None)
    # cmds = request.form.get('cmds', None)
    devices = json_dict.get('devices', None)
    cmds = json_dict.get('cmds', None)

    if not devices or not len(devices) or not cmds or not len(cmds):
        ret['status'] = 2
        ret['msg'] = 'data is empty !'
    elif len(devices) > 100 or len(cmds) > 100:
        ret['status'] = 1
        ret['msg'] = 'data is too much!'
    else:
        item = 0
        for cmd in cmds:
            for device in devices:
                item += 1
                db.rpush(settings.CMD + device, cmd)
        ret['status'] = 0
        ret['msg'] = 'has pushed %s items' % item
    return json.dumps(ret)


@app.route('/getcmd')
def getcmd():
    ret = {}
    host = request.args.get('host').lower()
    cmd = []
    key = settings.CMD + host
    while db.llen(key):
        cmd.append(db.lpop(key))
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
def pause_job():
    ret = {}
    carrier = request.args.get('carrier').lower()
    scheduler.pause_job(carrier)
    ret['status'] = 0
    key = settings.STATIC + carrier
    db.set(key, 1)
    ret['msg'] = 'pause success!'
    return json.dumps(ret)


@app.route('/resume')
def resume_job():
    ret = {}
    carrier = request.args.get('carrier').lower()
    scheduler.resume_job(carrier)
    key = settings.STATIC + carrier
    db.set(key, 0)
    ret['status'] = 0
    ret['msg'] = 'resume success!'
    return json.dumps(ret)


@app.route('/addjob', methods=['GET', 'POST'])
def add_job():
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
            key = settings.STATIC + carrier
            db.set(key, 0)
            scheduler.add_job(func=push_task, id=carrier, trigger='interval', seconds=10, args=[carrier])
            data['status'] = 0
            data['msg'] = 'carrier %s has added !' % carrier
        data.setdefault('status', 2)
        data.setdefault('msg', "carrier '%s' had existed !!!" % carrier)
    return json.dumps(data)


@app.route("/")
def index():
    return 'hello world'


def refresh_static():
    keys = db.keys(settings.STATIC + '*')
    for key in keys:
        db.set(key, 2)


if __name__ == "__main__":
    scheduler.start()
    refresh_static()
    app.run(host="0.0.0.0", port=settings.PORT, debug=True)
