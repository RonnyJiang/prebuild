#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 @desc:
 @author: ronny
 @contact: set@aliyun.com
 @site: www.lemon.pub
 @software: PyCharm  @since:python 3.5.2(32bit) on 2016/11/28.14:00
"""

import os
import logging
import commands
import sys
import shutil
import smtplib
import time
import socket, fcntl, struct
from email.mime.text import MIMEText

CCACHE_FOLDER_NAME = ".ccache"
PRE_BUILD_EMAIL = 'pre_build@xxx.com'
PRE_BUILD_PSSWORD = 'xxx'
LT_SMTP_SERVER = 'smtp.xxx.com'
GERRIT_URL = "http://gerrit.xxx.com:2089/"
MAIL_CC = ["aaa@xxx.com", "bbb@xxx.com", "ccc@xxx.com"]
BUILD_LOG = "clean_build_log.txt"

def GetLog():
    """Initialize the global log
    """
    logger = logging.getLogger(__name__)
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s(%(thread)d)    \
        : %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

    file = logging.FileHandler(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'clean_build.log'))
    file.setFormatter(formatter)
    logger.addHandler(file)
    logger.setLevel(logging.INFO)
    return logger

LOG = GetLog()

def send_mail(receiver, subject, content):
    sender = PRE_BUILD_EMAIL
    cc = MAIL_CC
    if receiver in cc:
        cc.remove(receiver)
    msg = MIMEText(content, _subtype='plain', _charset='utf-8') # _subtype='html'
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg['Cc'] = '; '.join(cc)
    receivers = cc[:]
    receivers.append(receiver)
    server = smtplib.SMTP()
    server.connect(LT_SMTP_SERVER)
    server.login(PRE_BUILD_EMAIL, PRE_BUILD_PSSWORD)
    try:
        LOG.info("send email to: %s , cc: %s" % (receiver, cc))
        server.sendmail(sender, receivers, msg.as_string())
        return True
    except smtplib.SMTPException:
        LOG.error("unable to send email")
        return False
    finally:
        server.close()

def run_shell_command(cmd):
    sys = os.name
    if sys == 'posix':
        LOG.info(cmd)
        return commands.getstatusoutput(cmd)
    else:
        return 'System of The PC is not a posix'

def get_top_containerid(image_name):
    status, output = run_shell_command("docker ps -a | grep %s | head -n 1 | awk '{print $1}'" % (image_name))
    if status == 0:
        return output
    else:
        LOG.error("get_top_containerid fail")
        return None

def get_running_containerid(image_name):
    _, output = run_shell_command("docker ps | grep %s | head -n 1 | awk '{print $1}'" % (image_name))
    if output:
        return output
    else:
        top_containerid = get_top_containerid(image_name)
        start_status, _ = run_shell_command('docker start %s' % (top_containerid))
        if start_status == 0:
            LOG.info("docker start %s success" % (top_containerid))
            return top_containerid
        else:
            LOG.error("docker start %s fail" % (top_containerid))
            sys.exit(-1)

def init_ccache(docker_containerid, path):
    LOG.info("init_ccache in")
    ccache_path = os.path.join(path, CCACHE_FOLDER_NAME)
    LOG.info("init_cache cache_path = %s" % ccache_path)
    if os.path.exists(ccache_path) is False:
        os.mkdir(ccache_path)

    run_shell_command("docker exec -u pre_build:pre_build %s sh -c 'export USE_CCACHE=1 && export CCACHE_DIR=%s && ccache -M 50G'" % (docker_containerid, ccache_path))
    LOG.info("init_ccache out")

def building_lock(path):
    try:
        output = os.listdir(path)
        if 'building-lock' in output:
            return False
        os.mkdir(os.path.join(path, 'building-lock'))
    except Exception, exp:
        LOG.info('building_lock Exception:%s', exp)
        return False
    return True

def building_unlock(path):
    try:
        os.rmdir(os.path.join(path, 'building-lock'))
    except Exception, exp:
        LOG.info('building_unlock Exception:%s', exp)
        return False
    return True

def last_lines(filename, lines = 20):
    #print the last line(s) of a text file
    block_size = 1024
    block = ''
    nl_count = 0
    start = 0
    fsock = file(filename, 'rU')
    try:
        #seek to end
        fsock.seek(0, 2)
        #get seek position
        curpos = fsock.tell()
        while(curpos > 0): #while not BOF
            #seek ahead block_size+the length of last read block
            curpos -= (block_size + len(block));
            if curpos < 0: curpos = 0
            fsock.seek(curpos)
            #read to end
            block = fsock.read()
            nl_count = block.count('/n')
            #if read enough(more)
            if nl_count >= lines: break
        #get the exact start position
        for n in range(nl_count-lines+1):
            start = block.find('/n', start)+1 
    finally:        
        fsock.close()
    #print it out  
    return block[start:]

def get_local_ip(ifname):  
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))  
    ret = socket.inet_ntoa(inet[20:24])  
    return ret

def build(path, build_name, image_name):
    init_ccache(get_running_containerid(image_name), path)
    os.system('repo sync')
    
    build_result_path = os.path.join(path, BUILD_LOG)
    if os.path.exists(build_result_path):
            os.remove(build_result_path)
    
    cmd = "docker exec -u pre_build:pre_build %s sh -c 'cd %s && ./%s >> %s'" % (get_running_containerid(image_name), path, build_name, BUILD_LOG)
    LOG.info(cmd)
    status = os.system(cmd)
    if status == 0:
        LOG.info("clean build success")
        return True
    else:
        # build fail
        LOG.error("clean build fail")
        mail_content = """
        The error log is as follows:
        
        %s
        """ % last_lines(build_result_path)
        ISOTIMEFORMAT='%Y-%m-%d %X'
        current_time = time.strftime(ISOTIMEFORMAT,time.localtime())
        send_mail(PRE_BUILD_EMAIL,
             "clean build fail -- %s|%s|%s" % (get_local_ip("eth0"), image_name.split('/')[-1], current_time),
              mail_content)
        return False

def clean_build():
    LOG.info("repo_path=%s;repo_build_shell=%s;docker_image=%s" %(sys.argv[1], sys.argv[2], sys.argv[3]))
    try:
        if building_lock(sys.argv[1]) is False:
            LOG.info("pre_build is running...")
            return

        os.chdir(sys.argv[1])
        out_path = os.path.join(sys.argv[1], "out")
        if os.path.exists(out_path):
            shutil.rmtree(out_path)
            build(sys.argv[1], sys.argv[2], sys.argv[3])
    finally:
        building_unlock(sys.argv[1])

def main():
    clean_build()

if __name__ == '__main__':
    main()