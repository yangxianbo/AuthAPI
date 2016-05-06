#!/usr/bin/python2.7
#coding:utf-8
#AUTHOR: yangxb
#CREATER: 2015-07-06 11:01:53
#FILENAME: APIproxy.py
#DESCRIPTION: 
#===============================================================


import logging
import logging.config

logging.config.fileConfig("./config/logging.conf")
logger = logging.getLogger("MyLogHandler")

import json
from xmlrpclib import ServerProxy
from xmlrpclib import Fault
import multiprocessing
import socket

def connect_client(ip,func,msg):
    s=ServerProxy('http://%s:19999'%ip)
    FUNC=getattr(s,func)
    print msg
    result=FUNC(msg)
    return result

def connect_longclient(ips,msg):
    try:
        connFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except socket.error, msg:
        logger.error(msg)
        return -5000
    try:
        connFd.connect(("127.0.0.1", 2003))
        logger.debug("connect to localserver success")
    except socket.error,msg:
        logger.error(msg)
        return -5001
    messages['data']={'ips':ips,'msg':msg}
#    messages['data']={'ips':['10.0.2.22','10.0.2.241'],'msg':{'script':'test.py','args':[]}}
    messages['ip']='127.0.0.1'

    data=json.dumps(messages)
    if connFd.send(data) != len(data):
        logger.error("send data to localserver failed")
    time.sleep(1)
    connFd.close()
    return 0

def multi_contact_client(jsonstring):
    try:
        arg_dict=json.loads(jsonstring)
        if arg_dict.has_key('func') and arg_dict.has_key('msg') and arg_dict.has_key('ips'):
            if isinstance(arg_dict['func'], unicode) and isinstance(arg_dict['msg'], dict) and isinstance(arg_dict['ips'], list):
                func=arg_dict['func']
                ip_list=arg_dict['ips']
                msg=json.dumps(arg_dict['msg'])
                #------------multiprocess--------------#
                pool = multiprocessing.Pool(processes=8)
                result = {}
                for ip in ip_list:
                    result[ip]=(pool.apply_async(connect_client, (ip,func,msg, )))
                    logger.info('%s request %s ,messages is %s'%(ip,func,msg))
                pool.close()
                pool.join()
                redict={}
                for k,v in result.items():
                    try:
                        redict[k]=v.get()
                    except socket.error,error:
                        logger.error('%s request %s ,messages is %s,return %s'%(ip,func,msg,error))
                        redict[k]=json.dumps({'error':str(error)})
                return json.dumps(redict)
                #------------multiprocess--------------#
            else:return -4001
        else:return -4002
    except ValueError:
        return -4000

def contact_longclient(jsonstring):
    try:
        arg_dict=json.loads(jsonstring)
        if arg_dict.has_key('func') and arg_dict.has_key('msg') and arg_dict.has_key('ips'):
            if isinstance(arg_dict['func'], unicode) and isinstance(arg_dict['msg'], dict) and isinstance(arg_dict['ips'], list):
                func=arg_dict['func']
                ip_list=arg_dict['ips']
                msg=arg_dict['msg']
                num=connect_longclient(ip_list,msg)
                return num
            else:return -4001
        else:return -4002
    except ValueError:
        return -4000
