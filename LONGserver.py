#!/usr/bin/python2.7
#coding:utf-8
#AUTHOR: yangxb
#CREATER: 2015-08-21 11:45:01
#FILENAME: testepoll.py
#DESCRIPTION: 
#===============================================================

 
import socket
import select, errno
import json
import logging
import logging.config
import sys
from daemon import Daemon

logging.config.fileConfig("./config/logging.conf")
logger = logging.getLogger("MyLogHandler")     

         
def _start(): 
    try:
        listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except socket.error, msg:
        logger.error("create socket failed")
 
    try:
        listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error, msg:
        logger.error("setsocketopt SO_REUSEADDR failed")
 
    try:
        listen_fd.bind(('', 2003))
    except socket.error, msg:
        logger.error("bind failed")
 
    try:
        listen_fd.listen(1000)
    except socket.error, msg:
        logger.error(msg)
     
    try:
        epoll_fd = select.epoll()
        epoll_fd.register(listen_fd.fileno(), select.EPOLLIN)
    except select.error, msg:
        logger.error(msg)
         
    connections = {}
    addresses = {}
    datalist = {}

    fd_dict={}
    while True:
        epoll_list = epoll_fd.poll()
 
        for fd, events in epoll_list:
            if fd == listen_fd.fileno():
                conn, addr = listen_fd.accept()
                logger.info("accept connection from %s, %d, fd = %d" % (addr[0], addr[1], conn.fileno()))
                conn.setblocking(0)
                epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                connections[conn.fileno()] = conn
                addresses[conn.fileno()] = addr
            elif select.EPOLLIN & events:
                datas = ''
                while True:
                    try:
                        data = connections[fd].recv(1024)
                        if not data and not datas:
                            epoll_fd.unregister(fd)
                            connections[fd].close()
                            for key,value in fd_dict.items():
                                if value == fd:
                                    del fd_dict[key]
                            logger.info("%s, %d closed" % (addresses[fd][0], addresses[fd][1]))
                            break
                        else:
                            datas=json.loads(data)
                            if datas['ip'] == "127.0.0.1":
                                if datas['data'] == "heartbeat":
                                    pass
                                else:
                                    epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                                    ip_list=datas['data']['ips']
                                    message=datas['data']['msg']
                                    for ip in ip_list:
                                        if fd_dict.has_key(ip):
                                            sendfd=fd_dict[ip]
                                            connections[sendfd].send(json.dumps(message))
                                            logger.info("fd:%s,ip:%s send message %s success"%(sendfd,ip,json.dumps(message)))
                                        else:
                                            logger.warning("ip:%s not found"%ip)
                            else:
                                if datas['key'] == "6af50cd1e1d57ffc845ecb157c8faf01":
                                    if not fd_dict.has_key(datas['ip']):
                                        if datas['ip'] != addresses[conn.fileno()][0]:
                                            old_info=list(addresses[conn.fileno()])
                                            old_info[0]=datas['ip']
                                            new_info=tuple(old_info)
                                            addresses[conn.fileno()]=new_info
                                            fd_dict[datas['ip']]=conn.fileno()
                                else:
                                    connections[fd].close()
                                    logger.error("%s, %d is refuse connect" % (addresses[fd][0], addresses[fd][1]))
                                
                    except socket.error, msg:
                        if msg.errno == errno.EAGAIN:
                            datalist[fd] = datas['data']
                            if isinstance(datalist[fd], unicode) or isinstance(datalist[fd], int):
                                if datalist[fd] == 'heartbeat':
                                    logger.debug("fd:%s,ip:%s receive heartbeat" % (fd,datas['ip']))
                                elif datalist[fd] == 0:
                                    logger.info("fd:%s,ip:%s execute success!"% (fd,datas['ip']))
                                else:
                                    logger.error("fd:%s,ip:%s execute error number is:%s"% (fd,datas['ip'],datas['data']))
                            else:
                                pass
                            epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                            break
                        else:
                            epoll_fd.unregister(fd)
                            connections[fd].close()
                            logger.error(msg)
                            break
            elif select.EPOLLHUP & events:
                epoll_fd.unregister(fd)
                connections[fd].close()
                logger.debug("%s, %d closed" % (addresses[fd][0], addresses[fd][1]))
            elif select.EPOLLOUT & events:
                sendLen = 0
                while True:
                    if datalist[fd] == "heartbeat":
                        sendLen += connections[fd].send(datalist[fd][sendLen:])
                        if sendLen == len(datalist[fd]):
                            break
                    else:
                         break
                epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)
            else:
                continue

class MyDaemon(Daemon):
    def run(self):
        _start()

if __name__ == "__main__":
    daemon = MyDaemon('/tmp/daemon-Longserver.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.stop()
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
