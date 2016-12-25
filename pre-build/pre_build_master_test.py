#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 @desc:
 @author: ronny
 @contact: set@aliyun.com
 @site: www.lemon.pub
 @software: PyCharm  @since:python 3.5.2(32bit) on 2016/11/28.14:00
"""
import os,subprocess,re,logging
import smtplib
from email.mime.text import MIMEText

PRE_BUILD_EMAIL = 'xxx@xxx.com'
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
    print(cc)
    if receiver in cc:
        cc.remove(receiver)
    print(cc)
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
        return subprocess.getstatusoutput(cmd)
    else:
        return 'System of The PC is not a posix'

def get_issue_id_test():
    change_id = 'Id12b8382a95aa8ce48e612e696b87b9e60bbdce7'
    commit_message = get_change_content(change_id).upper()
    print(commit_message)
    m = re.search(r'(ID:\s*#?)(\d+)', commit_message)
    print(m)
    print('grup1:', m.group(1), 'group2:', m.group(2))
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
    LOG.info(command)
    status,content = run_shell_command(command)
    if status == 0:
        return content
    else:
        LOG.error("git change content error")
        return None


def delete_db():
    if os.path.exists('C:/python_project/prebuild/pre-build/upload_pre-build-error.db'):
        LOG.info('delete %s' % 'C:/python_project/prebuild/pre-build/upload_pre-build-error.db')
        os.remove('C:/python_project/prebuild/pre-build/upload_pre-build-error.db')

if __name__ == '__main__':
    # get_issue_id_test()
    # send_mail('email',
    #           "pre_build -- ",
    #           """
    #           Hi %s,
    #           please add "Issue ID:" in Commit Message, and git commit --amend
    #           %s
    #           """ % ('email'.split('@')[0], GERRIT_URL + '4/46/1'))
    # print(os.path.exists('C:/python_project/prebuild/pre-build/upload_pre-build-error.db'))
    # if not os.path.exists('C:/python_project/prebuild/pre-build/upload_pre-build-error.db'):
    #     return False
    refsstr = 'refs/changes/02/118502/1'
    print(refsstr.split('/'))
    print(refsstr.split('/')[-2])