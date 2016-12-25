# -*- coding: utf-8 -*-

"""
 @desc:
 @author: ronny
 @contact: set@aliyun.com
 @site: www.lemon.pub
 @software: PyCharm  @since:python 3.5.2(32bit) on 2016/11/28.14:00
"""

import logging
import os
import sqlite3
import time
import sys
import pexpect
import re
import commands
import smtplib
import shutil
import stat
import urllib2
import json
from email.mime.text import MIMEText
from xml.etree import ElementTree

class db_schema:
    project_name = 0
    ref_spec = 1
    issue_id = 2
    author = 3

POST_BUILD_DELAY_SEC = 5*60
ERROR_FILE_NAME = 'pre-build-error.db'
PRE_BUILD_EMAIL = 'aa@xxx.com'
PRE_BUILD_PSSWORD = 'xxxx'
LT_SMTP_SERVER = 'smtp.xxx.com'
CCACHE_FOLDER_NAME = ".ccache"
GERRIT_URL = "http://gerrit.xxx.com:2089/"
MAIL_CC = ["aaa@xxx.com", "bbb@xxx.com", "ccc@xxx.com"]
CLEAN_BUILD_CRON_FILE = "clean_build.cron"
CLEAN_BUILD_PYTHON_FILE = "clean_build.py"

def GetLog():
    """Initialize the global log
    """
    logger = logging.getLogger(__name__)
    console = logging.StreamHandler()
    # formatter = logging.Formatter('%(asctime)s'
    #   ' %(filename)s %(lineno)d %(levelname)s: %(message)s')
    formatter = logging.Formatter('%(asctime)s %(levelname)s(%(thread)d)    \
        : %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

    file = logging.FileHandler(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pre-build.log'))
    file.setFormatter(formatter)
    logger.addHandler(file)
    # logger.setLevel(logging.DEBUG)
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


def run_ssh_command(ip, user, password, command, retry=3):
    cmdline = 'ssh %s@%s %s' % (user, ip, command)
    return run_romate_command(password, cmdline)


def scp_to_server(ip, user, password, local_file, server_dir):
    if os.path.isdir(local_file):
        cmdline = 'scp -r %s %s@%s:%s' % (local_file, user, ip, server_dir)
    else:
        cmdline = 'scp %s %s@%s:%s' % (local_file, user, ip, server_dir)
    return run_romate_command(password, cmdline)


def scp_form_server(ip, user, password, server_file, local_dir, server_file_is_dir=False):
    if server_file_is_dir:
        cmdline = 'scp -r %s@%s:%s %s' % (user, ip, server_file, local_dir)
    else:
        cmdline = 'scp %s@%s:%s %s' % (user, ip, server_file, local_dir)
    return run_romate_command(password, cmdline)


def run_romate_command(password, cmdline):
    ssh_newkey = '.*(yes/no).*'
    passwd_key = '.*assword.*'
    LOG.info('run_romate_command start, cmd: %s', cmdline)
    child = pexpect.spawn(cmdline)

    i = child.expect([pexpect.TIMEOUT, ssh_newkey, passwd_key])

    if i == 0:
        raise WaitForResponseTimedOutError(
            'time out, child.before=%s, child.after=%s' % (child.before, child.after))
    if i == 1:
        child.sendline('yes')
        i = child.expect([pexpect.TIMEOUT, passwd_key])
        if i == 0:
            raise WaitForResponseTimedOutError(
                'time out, child.before=%s, child.after=%s' % (child.before, child.after))
    child.sendline(password)
    i = child.expect([pexpect.TIMEOUT, pexpect.EOF])
    if i == 0:
        raise WaitForResponseTimedOutError(
            'time out, child.before=%s, child.after=%s' % (child.before, child.after))
    LOG.info('run_romate_command end, cmd: %s', cmdline)
    return child.before


class MsgException(Exception):
    """Generic exception with an optional string msg."""

    def __init__(self, msg=""):
        self.msg = msg


# also need the timeout info
class WaitForResponseTimedOutError(MsgException):
    """We sent a command and had to wait too long for response."""


class SQLiteDatabase():
    def __init__(self, dbPath):
        self.init(dbPath)

    def init(self, dbPath):
        # dbPath = os.path.join(os.path.abspath(dir), ERROR_FILE_NAME)
        craetTable = False
        if not os.path.exists(dbPath):
            craetTable = True
        self.connect = sqlite3.connect(dbPath)
        cursor = self.connect.cursor()
        if craetTable:
            cursor.execute(
                "create table error_table (project_name text, ref_spec text, issue_id text, author text)")
            cursor.close()
            self.connect.commit()

    def close(self):
        if self.connect is not None:
            self.connect.close()

    def addRecord(self, project_name, ref_spec, issue_id, author):
        if self.connect is None:
            return
        cursor = self.connect.cursor()
        cmd = 'insert into error_table values("%s","%s","%s","%s")' % (
            project_name, ref_spec, issue_id, author)
        cursor.execute(cmd)
        cursor.close()
        self.connect.commit()

    def getRecord(self, issue_id):
        if self.connect is None:
            return None, None, None, None
        cursor = self.connect.cursor()
        cmd = "SELECT * FROM error_table WHERE issue_id = '%s'" % (issue_id)
        cursor.execute(cmd)
        output = cursor.fetchall()
        cursor.close()
        return output

    def deleteRecord(self, issue_id):
        if self.connect is None:
            return
        cursor = self.connect.cursor()
        cmd = 'DELETE FROM error_table WHERE issue_id = "%s"' % (issue_id)
        cursor.execute(cmd)
        self.connect.commit()
        cursor.close()


class DataServer():
    def __init__(self, local_dir, dir, ip, user, password):
        # self.db = None
        self.local_dir = local_dir
        self.dir = dir
        self.ip = ip
        self.user = user
        self.password = password
        self.downloadPath = '%s/download_%s' % (local_dir, ERROR_FILE_NAME)
        self.uploadPath = '%s/upload_%s' % (self.dir, ERROR_FILE_NAME)

    def delete_db(self):
        if os.path.exists(self.downloadPath):
            LOG.info('delete %s' % self.downloadPath)
            os.remove(self.downloadPath)

    def get_and_delete_build_record(self, issue_id):
        try:
            LOG.info('get_and_delete_build_record in')
            self.delete_db()
            if self.data_server_lock() is False or self.download_data_file() is False:
                return False
            if not os.path.exists(self.downloadPath):
                return False
            db = SQLiteDatabase(self.downloadPath)
            output = db.getRecord(issue_id)
            db.deleteRecord(issue_id)
            db.close()
            self.upload_data_file()
            LOG.info('get_and_delete_build_record out(data = %s)' % output)
            return output
        except Exception, exp:
            LOG.info('get_and_delete_build_record Exception:%s', exp)
            return False
        finally:
            self.data_server_unlock()

    def delete_build_record(self, issue_id):
        try:
            self.delete_db()
            if self.data_server_lock() is False or self.download_data_file() is False:
                return False
            if not os.path.exists(self.downloadPath):
                return False
            db = SQLiteDatabase(self.downloadPath)
            db.deleteRecord(issue_id)
            db.close()
            self.upload_data_file()
            return True
        except Exception, exp:
            LOG.info('delete_build_record Exception:%s', exp)
            return False
        finally:
            self.data_server_unlock()

    def get_build_record(self, issue_id):
        try:
            self.delete_db()
            if self.data_server_lock() is False or self.download_data_file() is False:
                return None
            if not os.path.exists(self.downloadPath):
                return None
            db = SQLiteDatabase(self.downloadPath)
            output = db.getRecord(issue_id)
            db.close()
            return output
        except Exception, exp:
            LOG.info('get_build_record Exception:%s', exp)
            return None
        finally:
            self.data_server_unlock()

    def has_build_record(self, issue_id):
        try:
            self.delete_db()
            if self.data_server_lock() is False or self.download_data_file() is False:
                return False
            if not os.path.exists(self.downloadPath):
                return False
            db = SQLiteDatabase(self.downloadPath)
            output = db.getRecord(issue_id)
            db.close()
            return_flag = True
            if output is None or len(output) < 1:
                return_flag = False
            return return_flag
        except Exception, exp:
            LOG.info('has_build_record Exception:%s', exp)
            return False
        finally:
            self.data_server_unlock()

    def add_build_record(self, project_name, ref_spec, issue_id, author):
        try:
            if os.path.exists(self.downloadPath):
                os.remove(self.downloadPath)
            self.data_server_lock()
            self.download_data_file()
            db = SQLiteDatabase(self.downloadPath)
            db.addRecord(project_name, ref_spec, issue_id, author)
            db.close()
            self.upload_data_file()
        except Exception, exp:
            LOG.info('add_build_record Exception:%s', exp)
        finally:
            self.data_server_unlock()

    def download_data_file(self):
        try:
            LOG.info('download_data_file in')
            scp_form_server(
                self.ip, self.user, self.password, self.uploadPath, self.downloadPath)
            LOG.info('download_data_file out')
        except WaitForResponseTimedOutError, error:
            LOG.info('download_data_file WaitForResponseTimedOutError:%s', error.msg)
            return False
        except Exception, exp:
            LOG.info('download_data_file Exception:%s', exp)
            return False
        return True

    def upload_data_file(self):
        try:
            LOG.info('upload_data_file in')
            scp_to_server(
                self.ip, self.user, self.password, self.downloadPath, self.uploadPath)
            LOG.info('upload_data_file out')
        except WaitForResponseTimedOutError, error:
            LOG.info(
                'upload_data_file WaitForResponseTimedOutError:%s', error.msg)
            return False
        except Exception, exp:
            LOG.info('upload_data_file Exception:%s', exp)
            return False
        return True

    def data_server_lock(self):
        try:
            time_out = 0
            while True:
                output = self.romate_command('ls %s' % self.dir)
                if output.find('pre-build-lock') == -1:
                    break
                time.sleep(0.5)
                time_out += 1
                if time_out > 60:
                    LOG.info('data_server_lock time out')
                    return False
            self.romate_command('mkdir %s/pre-build-lock' % self.dir)
        except WaitForResponseTimedOutError, error:
            LOG.info('data_server_lock WaitForResponseTimedOutError:%s', error.msg)
            return False
        except Exception, exp:
            LOG.info('data_server_lock Exception:%s', exp)
            return False
        return True

    def data_server_unlock(self):
        try:
            self.romate_command('rmdir %s/pre-build-lock' % self.dir)
        except WaitForResponseTimedOutError, error:
            LOG.info(
                'data_server_unlock WaitForResponseTimedOutError:%s', error.msg)
            return False
        except Exception, exp:
            LOG.info('data_server_unlock Exception:%s', exp)
            return False
        return True

    def romate_command(self, cmd):
        return run_ssh_command(self.ip, self.user, self.password, cmd)


def run_shell_command(cmd):
    sys = os.name
    if sys == 'posix':
        return commands.getstatusoutput(cmd)
    else:
        return 'System of The PC is not a posix'

def run_gerrit_command(project, verified, comments, patch_set, gerrit_ip="10.27.254.101", gerrit_port="29000"):
    command = "ssh -p %s %s gerrit review --project %s --verified %s --message \'\"%s\"\' %s" % (
        gerrit_port, gerrit_ip, project, verified, comments, patch_set)
    LOG.info('run_gerrit_command(%s)' % command)
    run_shell_command(command)

def run_gerrit_submit_command(patch_set, gerrit_ip="10.27.254.101", gerrit_port="29000"):
    command = "ssh -p %s %s gerrit review --submit %s" % (
        gerrit_port, gerrit_ip, patch_set)
    LOG.info('run_gerrit_submit_command(%s)' % command)
    run_shell_command(command)    

def get_env(ev):
    return os.environ.get(ev)


def get_change_subject():
    return get_env("GERRIT_CHANGE_SUBJECT")


def get_commiter_email():
    return get_env("GERRIT_CHANGE_OWNER_EMAIL")


def get_project_name():
    return get_env("GERRIT_PROJECT")


def get_refspec():
    return get_env("GERRIT_REFSPEC")


def get_project_path(path, project):
    os.chdir(path)
    status, projects = run_shell_command("find * -name .git")
    project_paths = projects.split('\n')
    if status == 0:
        for project_path in project_paths:
            os.chdir(path + "/" + project_path + "/..")
            status, local_project = run_shell_command(
                "git config --get remote.origin.projectname")
            if status == 0 and local_project == project:
                return run_shell_command("pwd")[1]
        LOG.error("there is no %s git repository in %s" % (project, path))
    return None


def update_code(path, project_name, ref_spec):
    LOG.info('update_code in(ref_spec=%s)' % ref_spec)
    project_path = get_project_path(path, project_name)
    os.chdir(project_path)
    status, origin_url = run_shell_command(
        "git config --get remote.origin.url")
    if status == 0:
        status, output = run_shell_command(
            "git pull " + origin_url + " " + ref_spec)
        LOG.info('update_code out')
        return status == 0
    else:
        LOG.error("there is no %s git repository in %s" % (project_name, path))

def clean_build_lock(dir):
    try:
        time_out = 0
        while True:
            output = os.listdir(dir)
            if 'clean-build-lock' not in output:
                break
            time.sleep(0.5)
            time_out += 1
            if time_out > 60:
                LOG.info('clean_build_lock time out')
                return False
        os.mkdir(os.path.join(dir, 'clean-build-lock'))
    except Exception, exp:
        LOG.info('clean_build_lock Exception:%s', exp)
        return False
    return True

def clean_build_unlock(dir):
    try:
        os.rmdir(os.path.join(dir, 'clean-build-lock'))
    except Exception, exp:
        LOG.info('clean_build_unlock Exception:%s', exp)
        return False
    return True

def get_cron_time(cron_count):
    if 22 + 1.5*cron_count >= 24:
        time = 1.5*cron_count - 2
    else:
        time = 22 + 1.5*cron_count

    hour = int(time)
    minutes = int(60*(time - hour))
    
    return '%s %s * * *' % (minutes, hour)

def init_clean_build(path):
    LOG.info('init_clean_build in')
    status, crontab_list = run_shell_command("crontab -l")
    if status == 0 and crontab_list.find(path) >= 0:
        LOG.info("clean build thread is running")
    else:
        try:
            if clean_build_lock(os.path.dirname(__file__)) is False:
                return
    
            cron_count = 0
            cron_old_content = ''
            cron_new_content = ''
            clean_build_path = os.path.join(os.path.dirname(__file__), 'tools', CLEAN_BUILD_PYTHON_FILE)
            clean_build_file = os.path.join(os.path.dirname(__file__), 'tools', CLEAN_BUILD_CRON_FILE)
            LOG.info("init_clean_build clean_build_path = %s" % clean_build_path)
            LOG.info("init_clean_build clean_build_file = %s" % clean_build_file)
    
            if os.path.exists(clean_build_file) is True:
                with open(clean_build_file,"r") as file_r:
                    cron_old_content = file_r.read()
                    file_r.close()
    
            cron_count = cron_old_content.count(CLEAN_BUILD_PYTHON_FILE)
            if cron_old_content.find(path) == -1:
                cron_new_content = "%s%s /usr/bin/python %s %s %s %s\n" %(cron_old_content, get_cron_time(cron_count), clean_build_path, path, sys.argv[5], sys.argv[6])
            else:
                cron_new_content = cron_old_content
    
            with open(clean_build_file,"w") as file_w:
                LOG.info('cron_new_content = %s' % cron_new_content)
                file_w.write(cron_new_content)
                file_w.close()
        finally:
            clean_build_unlock(os.path.dirname(__file__))

        status, _ = run_shell_command("crontab -u pre_build %s" %(clean_build_file))
        if status == 0:
            LOG.info("crontab clean build thread success")
        else:
            LOG.info("crontab clean build thread fail")
    LOG.info('init_clean_build out')

def init_ccache(docker_containerid, path):
    LOG.info("init_ccache in")
    ccache_path = os.path.join(path, CCACHE_FOLDER_NAME)
    LOG.info("init_cache cache_path = %s" % ccache_path)
    if os.path.exists(ccache_path) is False:
        os.mkdir(ccache_path)

    run_shell_command("docker exec -u pre_build:pre_build %s sh -c 'export USE_CCACHE=1 && export CCACHE_DIR=%s && ccache -M 50G'" % (docker_containerid, ccache_path))
    LOG.info("init_ccache out")

def init_timeZone(docker_containerid):
    LOG.info("init_timeZone in")
    run_shell_command("docker exec %s sh -c 'cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime'" % (docker_containerid))
    LOG.info("init_timeZone out")

def get_top_containerid():
    status, output = run_shell_command("docker ps -a | grep %s | head -n 1 | awk '{print $1}'" % (sys.argv[6]))
    if status == 0:
        return output
    else:
        LOG.error("get_top_containerid fail")
        return None

def get_running_containerid():
    _, output = run_shell_command("docker ps | grep %s | head -n 1 | awk '{print $1}'" % (sys.argv[6]))
    if output:
        return output
    else:
        top_containerid = get_top_containerid()
        start_status, _ = run_shell_command('docker start %s' % (top_containerid))
        if start_status == 0:
            LOG.info("docker start %s success" % (top_containerid))
            return top_containerid
        else:
            LOG.error("docker start %s fail" % (top_containerid))
            sys.exit(-1)

def reset_code(path, error_datas):
    LOG.info('reset_code in')
    for row in error_datas:
        os.chdir(get_project_path(path, row[db_schema.project_name]))
        run_shell_command("git reset --hard HEAD~1")
    
    os.chdir(path)
    status, projects = run_shell_command("find * -name .git")
    project_paths = projects.split('\n')
    if status == 0:
        for project_path in project_paths:
            os.chdir(path + "/" + project_path + "/..")
            status,change = run_shell_command("git status")
            #LOG.info("%s"%change)
            if change.find("Untracked files:") >=0 or change.find('use "git push" to publish your local commits') >= 0 or change.find("nothing to commit") == -1:
                os.system("git clean -xfd && git reset --hard HEAD~1")
    LOG.info('reset_code out')

def copy_xml_file():
    copy_list = {}
    status, result = run_shell_command('repo manifest -o - -r')
    if status == 0:
        root = ElementTree.fromstring(result)
        project_node = root.findall('project')
        for project_node_item in project_node:
            copy_node = project_node_item.findall('copyfile')
            if len(copy_node) == 0:
                continue

            project_path = project_node_item.get('path')
            for copy_node_item in copy_node:
                copy_src = os.path.join(project_path, copy_node_item.get('src'))
                copy_dest = copy_node_item.get('dest')
                copy_list[copy_src] = copy_dest
    else:
        LOG.error('copy_xml_file error')

    LOG.info('copy_xml_file = %s' % (copy_list))
    return copy_list

def repo_copy_files(path):
    LOG.info('repo_copy_files in')
    copy_list = copy_xml_file()
    if len(copy_list) == 0:
        return

    for (src,dest) in copy_list.items():
        try:
            if os.path.exists(os.path.join(path, dest)) and os.path.isfile(os.path.join(path, dest)):
                os.remove(os.path.join(path, dest))
            shutil.copyfile(os.path.join(path, src), os.path.join(path, dest))
            os.chmod(os.path.join(path, dest), stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        except Exception, e:
            LOG.error(e)
    LOG.info('repo_copy_files out')

def building_lock(path):
    try:
        time_out = 0
        while True:
            output = os.listdir(path)
            if 'building-lock' not in output:
                break
            time.sleep(10)
            time_out += 10
            if time_out > 9000:
                LOG.info('building_lock time out')
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

def save_data(httpurl, data):
    response = None
    try:
        headers = {'Content-Type': 'application/json'}
        request = urllib2.Request(url=httpurl, headers=headers, data=json.dumps(data))
        response = urllib2.urlopen(request)
        LOG.info("url = %s;params=%s;response=%s" %(httpurl, data, response.getcode()))
    except urllib2.URLError as e:
        if hasattr(e, 'code'):
            LOG.info("url = %s;params=%s;error code=%s" %(httpurl, data, e.code))
        elif hasattr(e, 'reason'):
            LOG.info("url = %s;params=%s;error reason=%s" %(httpurl, data, e.reason))
    finally:
        if response:
            response.close()
            
def save_build_result(host, repo_name, issue_id, build_time, build_result):
    data = {}
    data['repo_name'] = repo_name
    data['issue_id'] = issue_id
    data['build_time'] = build_time
    data['build_result'] = build_result
     
    save_data('http://%s/pre_build/note_build_result.do' % host, data)
    
def save_commit(host, issue_id, gerrit, build_result):
    data = {}
    data['issue_id'] = issue_id
    data['gerrit'] = gerrit
    data['build_result'] = build_result
     
    save_data('http://%s/pre_build/note_commit.do' % host, data)    
            
def build(path, clean_build):
    try:
        building_lock(path)
        os.chdir(path)

        init_timeZone(get_running_containerid())
        init_ccache(get_running_containerid(), path)
        init_clean_build(path)
        repo_copy_files(path)

        out_path = os.path.join(path, "out")
        if clean_build and os.path.exists(out_path):
            shutil.rmtree(out_path)
            LOG.info('start clean build...')
            
        cmd = "docker exec -u pre_build:pre_build %s sh -c 'cd %s && ./%s'" % (get_running_containerid(), path, sys.argv[5])
        LOG.info(cmd)
        status = os.system(cmd)
        if status == 0:
            LOG.info("pre build success")
            return True
        else:
            # build fail
            LOG.error("pre build fail")
            return False
    finally:
        building_unlock(path)

def get_change_content(patch_set, gerrit_ip="10.27.254.101", gerrit_port="29000"):
    command = "ssh -p %s %s gerrit query %s --files --current-patch-set" % (gerrit_port, gerrit_ip, patch_set)
    status,content = run_shell_command(command)
    if status == 0:
        return content
    else:
        LOG.error("git change content error")
        return None    
            
def get_clean_build(patch_set):
    commit_message = get_change_content(patch_set).upper()
    m = re.search(r'FILE:\s*(?:[^\\\?\/\*\|<>:"]+\/)*[^\\\?\/\*\|<>:"]+.MK', commit_message)
    if m:
        return 1
    else:
        return 0 
    
def post_build(dataServer, issue_id, base_path):
    LOG.info('post_build in')
    time.sleep(POST_BUILD_DELAY_SEC)
    error_datas = dataServer.get_and_delete_build_record(issue_id)
    if error_datas is False or len(error_datas) == 0:
        LOG.error("error_datas is Null")
        return
    clean_build = 0
    for row in error_datas:
        project_name = row[db_schema.project_name]
        ref_spec = row[db_schema.ref_spec]
        patch_set = ref_spec.split('/')[-2]
        clean_build += get_clean_build(patch_set)
        run_gerrit_command(project_name, "0", 'Build Start ' + get_env('BUILD_URL') + 'console', ','.join(ref_spec.split('/')[-2:]))
        update_code(base_path, project_name, ref_spec)
    mail_info_list = []
    build_start_time =  time.strftime("%Y-%m-%d %X", time.localtime())
    build_result = build(base_path, clean_build)
    if build_result:
        for row in error_datas:
            mail_info_item = {}
            project_name = row[db_schema.project_name]
            ref_spec = ','.join(row[db_schema.ref_spec].split('/')[-2:])
            change = row[db_schema.ref_spec].split('/')[-2]
            commiter_email = row[db_schema.author]
            user_name = commiter_email.split('@')[0]
            mail_content = """
              Hi %s,
              Your commit build successful
              %s
              see the build detail
              %s
               """% (user_name, GERRIT_URL + change, get_env('BUILD_URL') + 'console')
            mail_info_item['commiter_email'] = commiter_email
            mail_info_item['change'] = change
            mail_info_item['mail_content'] = mail_content
            mail_info_item['gerrit'] = GERRIT_URL + change
            mail_info_list.append(mail_info_item)
            run_gerrit_command(project_name, "+1", 'Build Successful ' + get_env('BUILD_URL') + 'console', ref_spec)
            run_gerrit_submit_command(ref_spec)
    else:
        for row in error_datas:
            mail_info_item = {}
            project_name = row[db_schema.project_name]
            ref_spec = ','.join(row[db_schema.ref_spec].split('/')[-2:])
            change = row[db_schema.ref_spec].split('/')[-2]
            commiter_email = row[db_schema.author]
            user_name = commiter_email.split('@')[0]
            mail_content = """
              Hi %s,
              Your commit build failed
              %s
              see the build detail
              %s
               """% (user_name, GERRIT_URL + change, get_env('BUILD_URL') + 'console')
            mail_info_item['commiter_email'] = commiter_email
            mail_info_item['change'] = change
            mail_info_item['mail_content'] = mail_content
            mail_info_item['gerrit'] = GERRIT_URL + change
            mail_info_list.append(mail_info_item)
            run_gerrit_command(project_name, "-1", 'Build Failed ' + get_env('BUILD_URL') + 'console', ref_spec)

    reset_code(base_path, error_datas)
    save_build_result(sys.argv[7], sys.argv[6].split('/')[-1], issue_id, build_start_time, build_result)
    for mail_info in mail_info_list:
        send_mail(mail_info['commiter_email'],
             "pre_build -- %s" % mail_info['change'],
              mail_info['mail_content'])
        save_commit(sys.argv[7], issue_id, mail_info['gerrit'], build_result)
    LOG.info('post_build out')
    return build_result


def main():
    LOG.info('main in')
    dataServer = DataServer(get_env("WORKSPACE"), sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    LOG.info(sys.argv)
    ret = post_build(dataServer, os.environ.get("ISSUE_ID"), get_env("WORKSPACE"))
    dataServer.delete_db()
    LOG.info('main out')
    sys.exit(0 if ret else -1)

if __name__ == '__main__':
    main()
