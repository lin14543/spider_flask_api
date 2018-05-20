#!/usr/bin/python
#coding:utf-8

def cpuInfo():
    result = {}
    with open("/proc/cpuinfo", 'r') as f:
        lines = f.readlines()
        for line in lines:
            splitline = line.split(":")
            keys = splitline[0].strip()
            if len(splitline) < 2:
                value = ''
            else:
                value = splitline[1].strip(' \t\n')
            result[keys] = value
    return result

if __name__ == '__main__':
    result = cpuInfo()
    print(result)
    data = dict(
        model=result.get('model'),
        model_name=result.get("model name"),
        stepping=result.get('stepping'),
        microcode=result.get('microcode'),
        cpu_MHz=result.get('cpu MHz')
    )
    print(data)
    url =
    sendData = urllib.urlencode(data)
    response = urllib2.urlopen()