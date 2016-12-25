#!/usr/bin/env python3
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
import re
import commands
import pexpect
import smtplib
from email.mime.text import MIMEText


class db_schema:
    project_name = 0
    ref_spec = 1
    issue_id = 2
    author = 3

ERROR_FILE_NAME = 'pre-build-error.db'
PRE_BUILD_EMAIL = 'pre_build@xxx.com'
PRE_BUILD_PSSWORD = 'xxx'
LT_SMTP_SERVER = 'smtp.xxx.com'
GERRIT_URL = "http://gerrit.xxx.com:2089/"
MAIL_CC = ["aaa@xxx.com", "bbb@xxx.com", "ccc@xxx.com"]


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
    # Pexpect 可以用来和像 ssh、ftp、passwd、telnet 等命令行程序进行自动交互。
    child = pexpect.spawn(cmdline)

    i = child.expect([pexpect.TIMEOUT, ssh_newkey, passwd_key])
    # 如果登录超时，打印出错信息，并退出.
    if i == 0:
        raise WaitForResponseTimedOutError(
            'time out, child.before=%s, child.after=%s' % (child.before, child.after))
    # 如果 ssh 没有 public key，接受它.
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
    # 输出命令结果.
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
        createTable = False    #变量改为createTable
        if not os.path.exists(dbPath):
            createTable = True
        # 如果sqlite3.connect中参数***.db若不存在，会自动在当前目录创建:
        self.connect = sqlite3.connect(dbPath)
        cursor = self.connect.cursor()
        if createTable:
            cursor.execute(
                "create table error_table (project_name text, ref_spec text, issue_id text, author text)")
            cursor.close()
            self.connect.commit()

    def close(self):
        if self.connect is not None:
            self.connect.close()

    def addRecord(self, project_name, ref_spec, issue_id, author):
        LOG.info('addRecord in')
        if self.connect is None:
            return
        cursor = self.connect.cursor()
        cmd = 'SELECT * FROM error_table'
        cursor.execute(cmd)
        output = cursor.fetchall()
        #当addRecord out(data = [(u'venus/tvos/platform/frameworks/dvb', u'refs/changes/86/118486/1', u'113717', u'email')])提交后，
        # 又提交u'refs/changes/86/118486/2', u'113717'
        # 这样的话change = ref_spec.split('/')[-2] = 118486，那么就会删掉118486/1的记录，在表中插入118486/2的记录，表中的记录和个字段就更新如下：
        # addRecord out(data = [(u'venus/tvos/platform/frameworks/dvb', u'refs/changes/86/118486/2', u'113717', u'email.com')])
        if output:
            change = ref_spec.split('/')[-2]
            for row in output:
                if(row[db_schema.ref_spec].split('/')[-2] == change):
                    cmd = "DELETE FROM error_table WHERE ref_spec = '%s'" % (row[db_schema.ref_spec])
                    cursor.execute(cmd)
        cmd = 'insert into error_table values("%s","%s","%s","%s")' % (
            project_name, ref_spec, issue_id, author)
        cursor.execute(cmd)
        cursor.close()
        self.connect.commit()
        LOG.info('addRecord out(data = %s)' % self.getRecord(issue_id))
        #addRecord out(data = [(u'venus/tvos/vendor/zhaoxin', u'refs/changes/02/118502/1', u'000000', u'email.com')])

    def getRecord(self, issue_id):
        if self.connect is None:
            return None, None, None, None
        cursor = self.connect.cursor()
        cmd = "SELECT * FROM error_table WHERE issue_id = '%s'" % (issue_id)
        cursor.execute(cmd)
        output = cursor.fetchall()
        cursor.close()
        return output

    def getRecordByRefspec(self, ref_spec):
        if self.connect is None:
            return None, None, None, None
        cursor = self.connect.cursor()
        cmd = "SELECT * FROM error_table WHERE ref_spec = '%s'" % (ref_spec)
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

    def deleteRecordByRefspec(self, ref_spec):
        if self.connect is None:
            return
        cursor = self.connect.cursor()
        cmd = 'DELETE FROM error_table WHERE ref_spec = "%s"' % (ref_spec)
        cursor.execute(cmd)
        self.connect.commit()
        cursor.close()


class DataServer():
    def __init__(self, dir, ip, user, password):
        # self.db = None
        self.dir = dir
        self.ip = ip
        self.user = user
        self.password = password
        self.downloadPath = '%s/download_%s' % (self.dir, ERROR_FILE_NAME)
        self.uploadPath = '%s/upload_%s' % (self.dir, ERROR_FILE_NAME)

    def delete_db(self):
        if os.path.exists(self.downloadPath):
            LOG.info('delete %s' % self.downloadPath)
            os.remove(self.downloadPath)

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

    def delete_build_recordByRefspec(self, ref_spec):
        try:
            LOG.info('delete_build_recordByRefspec in')
            self.delete_db()
            if self.data_server_lock() is False or self.download_data_file() is False:
                return False
            if not os.path.exists(self.downloadPath):
                return False
            db = SQLiteDatabase(self.downloadPath)
            db.deleteRecordByRefspec(ref_spec)
            db.close()
            self.upload_data_file()
            LOG.info('delete_build_recordByRefspec out')
            return True
        except Exception, exp:
            LOG.info('delete_build_recordByRefspec Exception:%s', exp)
            return False
        finally:
            self.data_server_unlock()

    def get_build_record(self, issue_id):
        try:
            self.delete_db()
            if self.data_server_lock() is False or self.download_data_file() is False:
                return False
            if not os.path.exists(self.downloadPath):
                return False
            db = SQLiteDatabase(self.downloadPath)
            output = db.getRecord(issue_id)
            db.close()
            return output
        except Exception, exp:
            LOG.info('get_build_record Exception:%s', exp)
            return False
        finally:
            self.data_server_unlock()

    def has_build_record(self, issue_id): #判断有没有已经记录了此issue id，如果有就返回True，没有返回False
        try:
            LOG.info('has_build_record in')
            self.delete_db()    #删除旧的download_pre-build-error.
            #接下来的就是调用两个函数self.data_server_lock()和self.download_data_file()
            # 判断pre-build-lock目录是否存在：不存在创建一个pre-build-lock目录，返回True .存在的话则等待30s（sleep30s）后返回个False

            if self.data_server_lock() is False or self.download_data_file() is False:
                # 其实就是拷贝最新的upload_pre-build-error.db成dbdownload_pre-build-error.db文件
                return False
            #执行到这就说明已经在self.dir目录下创建了pre-build-lock目录，并且在dir目录将upload_pre-build-error.db拷贝成download_pre-build-error.db
            #拷贝完后接下来判断拷贝后是否存在，不存在说明拷贝失败（失败原因有可能是upload...db被删除了等原因，这样就可以检查upload.db是否被删除）就返回False
            if not os.path.exists(self.downloadPath):
                return False
            db = SQLiteDatabase(self.downloadPath)
            output = db.getRecord(issue_id)
            db.close()
            return_flag = True
            if output is None or len(output) < 1:
                return_flag = False
            LOG.info('has_build_record out')
            return return_flag
        except Exception, exp:
            LOG.info('has_build_record Exception:%s', exp)
            return False
        finally:
            self.data_server_unlock()

    def has_build_recordByRefspec(self, ref_spec):
        try:
            LOG.info('has_build_recordByRefspec in')
            self.delete_db()
            if self.data_server_lock() is False or self.download_data_file() is False:
                return False
            if not os.path.exists(self.downloadPath):
                return False
            db = SQLiteDatabase(self.downloadPath)
            output = db.getRecordByRefspec(ref_spec)
            db.close()
            return_flag = True
            if output is None or len(output) < 1:
                return_flag = False
            LOG.info('has_build_recordByRefspec out')
            return return_flag
        except Exception, exp:
            LOG.info('has_build_recordByRefspec Exception:%s', exp)
            return False
        finally:
            self.data_server_unlock()

    def add_build_record(self, project_name, ref_spec, issue_id, author):
        try:
            LOG.info('add_build_record in')
            if os.path.exists(self.downloadPath):
                os.remove(self.downloadPath)
            self.data_server_lock()
            self.download_data_file()
            db = SQLiteDatabase(self.downloadPath)
            db.addRecord(project_name, ref_spec, issue_id, author)
            db.close()
            self.upload_data_file()
            LOG.info('add_build_record out')
        except Exception, exp:
            LOG.info('add_build_record Exception:%s', exp)
        finally:
            self.data_server_unlock()

    def download_data_file(self):
        #这个函数其实就是拷贝self.dir目录下最新的upload_pre-build-error.db成dbdownload_pre-build-error.db文件，然后返回True
        try:
            LOG.info('download_data_file in')
            scp_form_server(
                self.ip, self.user, self.password, self.uploadPath, self.downloadPath)
            LOG.info('download_data_file out')
        except WaitForResponseTimedOutError, error:
            LOG.info(
                'download_data_file WaitForResponseTimedOutError:%s', error.msg)
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

    def data_server_lock(self):  #目的：防止别人同时篡改db的数据
        ##判断pre-build-lock目录是否存在：
        # 不存在创建一个pre-build-lock目录，返回True
        # 存在的话则等待30s（sleep30s）后返回个False
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
            LOG.info(
                'data_server_lock WaitForResponseTimedOutError:%s', error.msg)
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


def get_env(ev):
    return os.environ.get(ev)


def get_issue_id():
    change_id = get_env("GERRIT_CHANGE_ID")
    commit_message = get_change_content(change_id).upper()
    m = re.search(r'(ID:\s*#?)(\d+)', commit_message)
    if m:
        return m.group(2)
    else:
        revert = re.search(r'(THIS REVERTS COMMIT\s*)(\w+).', commit_message)
        if revert:
            commit_message = get_change_content(revert.group(2)).upper()
            m = re.search(r'(ID:\s*#?)(\d+)', commit_message)
            if m:
                return m.group(2)
            else:
                return None
        else:
            return None



def get_change_content(change_id, gerrit_ip="10.27.254.101", gerrit_port="29000"):
    command = "ssh -p %s %s gerrit query %s" % (gerrit_port, gerrit_ip, change_id)
    status,content = run_shell_command(command)
    if status == 0:
        return content
    else:
        LOG.error("git change content error")
        return None

def get_commiter_email():
    return get_env("GERRIT_CHANGE_OWNER_EMAIL")


def get_project_name():
    return get_env("GERRIT_PROJECT")


def get_refspec():
    return get_env("GERRIT_REFSPEC")   ##The ref-spec. (refs/changes/xx/xxxx/z). eg：refs/changes/46/28146/1


def get_whitelist():
    return get_env("whitelist")


def filter_commiter():
    whitelist = get_whitelist().split(';')
    for item in whitelist:
        if item.strip()=='':
            continue
        if item == get_commiter_email():
            LOG.info("commiter(%s) is in whitelist, don't need pre-build"%(item))
            sys.exit(-1)


def check_repo(path, project):
    project_path = get_project_path(path, project)
    if project_path:
        return True
    else:
        LOG.error("error repo")
        return False


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


def pre_build(dataServer, base_path):
    LOG.info('pre_build in')
    #if check_repo(base_path, get_project_name()) is False:
    #    LOG.info('pre_build out, check_repo is False')
    #    return False
    issue_id = get_issue_id()  #获取issue id
    if not issue_id:
        LOG.info("get issue id error")
        # or build
        change = get_refspec().split('/')[-2]      #如下例子，change = 118502   GERRIT_URL + change = http://gerrit.aaa.com:2089/118502
        # addRecord out(data = [(u'venus/aa/vendor/bb', u'refs/changes/02/118502/1', u'000000', u'email')])
        send_mail(get_commiter_email(),
             "pre_build -- %s" % change,
              """
              Hi %s,
              please add "Issue ID:" in Commit Message, and git commit --amend
              %s
              """% (get_commiter_email().split('@')[0], GERRIT_URL + change))
        return False
    # (u'venus/platform/external/chromium_org', u'refs/changes/46/118546/1', u'107393', u'email'), + nextline
    # (u'venus/platform/external/chromium_org/third_party/WebKit', u'refs/changes/49/118549/1', u'107393', u'email')]
    # 这两个先提交u'refs/changes/46/118546/1', u'107393'这时issue id在db中没有，然后添加进去，返回True。然后又提交了refs/changes/49/118549/1，问题也是u'107393'，
    # 这时issue id在db中已经有了，然后添加进去，返回False，最后main函数exit (-1) jenkins项目状态failed
    if dataServer.has_build_record(issue_id) is True:
        dataServer.add_build_record(get_project_name(), get_refspec(
        ), issue_id, get_commiter_email())
        LOG.info('pre_build out, has_build_record is True')
        return False
    else:
        dataServer.add_build_record(get_project_name(), get_refspec(
        ), issue_id, get_commiter_email())
        LOG.info('pre_build out, has_build_record is Flase')
        os.chdir(base_path)
        with open("propfile", 'w') as fp:
            fp.write("ISSUE_ID=%s" % issue_id)
            fp.close()
        return True


def main():
    LOG.info('main in')

    filter_commiter()
    # python /home/pre_build/workspace/AutoTest/pre-build/pre_build_master.py  +
    #  + /home/pre_build/workspace/pre_build_aurora_master ip pre_build passwd
    # sys.argv[1]--/home/pre_build/workspace/pre_build_aurora_master
    # sys.argv[2]--ip
    # sys.argv[3]--pre_build
    # sys.argv[4]--passwd

    dataServer = DataServer(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    LOG.info(sys.argv)

    if get_env("GERRIT_EVENT_TYPE") == "change-abandoned":
        ref_spec = get_refspec()     #refs/changes/02/118502/1
        if dataServer.has_build_recordByRefspec(ref_spec):
            dataServer.delete_build_recordByRefspec(ref_spec)
            LOG.info('trigger by change-abandoned, delete the recordByRefspec:%s', ref_spec)
        else:
            LOG.info("trigger by change-abandoned, but can't find the recordByRefspec:%s(maybe the build is finished)", ref_spec)
        sys.exit(-1)

    ret = pre_build(dataServer, get_env("WORKSPACE"))
    dataServer.delete_db()
    LOG.info('main out')
    sys.exit(0 if ret else -1)

if __name__ == '__main__':
    main()
