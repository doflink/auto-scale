import redis
import os
import sys
import time
import signal
import logging
import socket
import json
from os.path import expanduser
from infrastructure import *
import urllib2
import subprocess
from random import randint


def createLogger(vmname):
    logger = logging.getLogger('mylogger')
    hdlr = logging.FileHandler('logger_'+ str(vmname) + '.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    return logger

def addToStr(stats, value, delim = ','):
    if stats == '':
        stats = value
    else:
        stats = delim.join([str(stats), str(value)])
    return stats

def metricHistory(cloud, vm, daemon, startTime, endTime):
    key = ":".join([str(cloud), str(vm), str(daemon)])
    rServer = redis.Redis(connection_pool=POOL)
    response = rServer.zrangebyscore(key, startTime, endTime)
    return response


def metricRealtimeParsed(cloud, vm, sources, startTime, endTime):
    history = {}
    for source in sources:
        result = metricHistory(cloud, vm, source, startTime, endTime)
        for line in result:
            data  = {}
            elements = line.split(',')
            for elem in elements:
                parameterData = elem.split(':')
                parameterName = parameterData[0]
                parameterValue = parameterData[1]
                if 'timestamp' == parameterName:
                    timestamp = int(float(parameterValue))##round time to seconds
                    data[parameterName] = timestamp
                else:
                    data[parameterName] = parameterValue
            if timestamp in history:
                oldData = history[timestamp]
                oldData.update(data)
                history = oldData
            else:
                history = data
    return history

def getHeaders(history):
    headers = {}
    for timestamp in history:
        currHeaders = history[timestamp]
        if len(currHeaders) > len(headers):
            headers = currHeaders
    return headers

#Vertical Scaling 
def verticalScaling(logger, urlrest):
    timewindow = 1
    idletime = 180 #3 minutes for creating a new VM if it is necessary
    coolingtime = 120 #need an interval time between allocatings
    stats  = {}
    clouds = ['0']
    sources = {'vm':None, 'host':None}
    cpu = 0
    ram = 0
    allocatetime = time.time() - 100

    while True:
        try:
	        vms = listVMs()
	        now = time.time()
            f = open("setting.json")
            settings = json.load(f)
            cputhreshold = settings['cputhreshold']

	        for cloud in clouds:
                ram = 0
                cpu = 0
                microcloud = "MicroCloud" + str(cloud)
                cpuquota = getCPUQuota(logger, microcloud, urlrest)
                cpuquota_avg = 0

		    for vm in vms:
		        history = metricRealtimeParsed(cloud, vm, sources, now - timewindow -10, now - 10)
		        ram = ram + (int(history["MemTotal"]) - int(history["MemFree"]))
		        cpu = cpu + float(history["CPU"])
                cpuquota_avg = cpuquota_avg + float(cpuquota[vm])
		    vmcount = len(vms)
		    ram = ram/1000 #MB
		    ram = ram/vmcount
		    cpu = cpu/vmcount
            cpuquota_avg = cpuquota_avg/vmcount

            #Scaling
		    if (cpu >= float(cputhreshold))and((now - allocatetime) > coolingtime):
                print "Start for Vertical scaling"
                cpuquota_add = float(cpuquota["total"])*5/100 #5 % of the total of cpu quota for a microcloud
                cpuquota_value = cpuquota_avg + cpuquota_add
                print "Adding CPU quota ..."
            if setCPUQuota(logger, microcloud, urlrest, cpuquota_value) == 0:
                print "Success add more CPU quota!"
            else:
                print "Unsuccess add CPU quota, please look at logs for more detail!"
                sleep(5)

        except Exception, e:
            logger.error("Error in Monitoring and Scaling VMs, please check monitoring report method : " + str(e))
            continue

        time.sleep(1)
     

def listVMs():
    fvms = open("vms/vms.json")
    vmlist = json.load(fvms)
    vms = []
    for vm in vmlist:
        vms.append(str(vm))
    return vms


def listVMId(logger, microcloud):
    try:
        vm = VirtualMachine()
        vms = vm.listInstances(microcloud)
        listvmid={}
        for vm in vms:
            listvmid[vm.name] = vm.id
        return listvmid
    except Exception, e:
        logger.error("Error in contacting with Cloud&Heat (List VmID): " + str(e))


def getCPUQuota(logger, microcloud, urlrest):
    try:
        vmsid = listVMId(logger, microcloud)
        cpuquota = {}
        total = 0
        vms = listVMs()
        for vm in vms:
            url = str(urlrest) + "/getcpuquota/"+ vmsid[vm]
            quota = json.load(urllib2.urlopen(str(urlrest) + "/getcpuquota/"+ vmsid[vm]))
            total = total + quota["vcpu_period"]
            cpuquota[vm] = quota["vcpu_quota"]
        total = total/(len(vms))
        cpuquota["total"] = total
        return cpuquota
    except Exception, e:
        logger.error("Error in getCPUQuota from Cloud&Heat: " + str(e))


def setCPUQuota(logger, microcloud, urlrest, value):
    try:
        vmsid = listVMId(logger, microcloud)     
        vms = listVMs()
        for vm in vms:
            result = json.load(urllib2.urlopen(str(urlrest) + "/setcpuquota/"+ vmsid[vm] + "/" + str(value)))
            print result
            if str(result) != "ok":
                logger.error("Error in setCPUQuota from Cloud&Heat for VM " + str(vm) + " with error: " + str(result))    
                return -1
        return 0

    except Exception, e:
        logger.error("Error in getCPUQuota from Cloud&Heat: " + str(e))

if __name__ == '__main__':
    logger = createLogger('localhost')
    f = open("setting.json")
    settings = json.load(f)
    urlrest = settings['cpuquotaservice']
    redis_server = settings['redis_server']
    redis_port = settings['redis_port']

    POOL = redis.ConnectionPool(host=redis_server, port=redis_port, db=0)
    setCPUQuota(logger, "MicroCloud0", urlrest, -1)
    verticalScaling(logger, urlrest)

