#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 @desc:
 @author: ronny
 @contact: set@aliyun.com
 @site: www.lemon.pub
 @software: PyCharm  @since:python 3.5.2(32bit) on 2016/11/29.13:51
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
import zipfile
from email.mime.text import MIMEText
from xml.etree import ElementTree

PRE_BUILD_EMAIL = 'xx@xxx.com'
PRE_BUILD_PSSWORD = 'xxx'
LT_SMTP_SERVER = 'smtp.xxx.com'
CCACHE_FOLDER_NAME = ".ccache"
GERRIT_URL = "http://gerrit.xxx.com:2089/"
MAIL_CC = ["email","email"]


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
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pre-build_app_slave.log'))
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
    msg = MIMEText(content, _subtype='plain', _charset='utf-8')  # _subtype='html'
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
        return commands.getstatusoutput(cmd)
    else:
        return 'System of The PC is not a posix'

#run_gerrit_command(project_name, "0", 'Build Start ' + get_env('BUILD_URL') + 'console', ref_spec_new)
def run_gerrit_command(project, verified, comments, patch_set, gerrit_ip="10.27.254.101", gerrit_port="29000"):
    command = "ssh -p %s %s gerrit review --project %s --verified %s --message \'\"%s\"\' %s" % (
        gerrit_port, gerrit_ip, project, verified, comments, patch_set)
    LOG.info('run_gerrit_command(%s)' % command)
    #run_gerrit_command(ssh -p 29000 10.27.254.101 gerrit review --project android/LiveSettings --verified 0 --message '"Build Start http://10.27.16.83:8080/job/pre_build_app_aurora_slave/209/console"' 118560,1)
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


def get_whitelist():
    return get_env("whitelist")


def filter_commiter():
    whitelist = get_whitelist().split(';')
    for item in whitelist:
        if item.strip() == '':
            continue
        if item == get_commiter_email():
            LOG.info("commiter(%s) is in whitelist, don't need pre-build" % (item))
            sys.exit(-1)


def get_project_path(path, project):
    os.chdir(path)
    status, projects = run_shell_command("find * -name .git")
    project_paths = projects.split('\n')
    if status == 0:
        for project_path in project_paths:
            os.chdir(path + "/" + project_path + "/..")
            status, local_project = run_shell_command(
                "git config --get remote.origin.projectname")
            if status == 0 and (local_project == project or local_project == project + '.git'):
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


def init_ccache(docker_containerid, path):
    LOG.info("init_ccache in")
    ccache_path = os.path.join(path, CCACHE_FOLDER_NAME)
    LOG.info("init_cache cache_path = %s" % ccache_path)
    if os.path.exists(ccache_path) is False:
        os.mkdir(ccache_path)

    run_shell_command(
        "docker exec -u pre_build:pre_build %s sh -c 'export USE_CCACHE=1 && export CCACHE_DIR=%s && ccache -M 50G'" % (
        docker_containerid, ccache_path))
    LOG.info("init_ccache out")


def init_timeZone(docker_containerid):
    LOG.info("init_timeZone in")
    run_shell_command(
        "docker exec %s sh -c 'cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime'" % (docker_containerid))
    LOG.info("init_timeZone out")


def get_top_containerid():
    status, output = run_shell_command("docker ps -a | grep %s | head -n 1 | awk '{print $1}'" % (sys.argv[2]))
    if status == 0:
        return output
    else:
        LOG.error("get_top_containerid fail")
        return None


def get_running_containerid():
    _, output = run_shell_command("docker ps | grep %s | head -n 1 | awk '{print $1}'" % (sys.argv[2]))
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


def reset_code(path, project_name):
    LOG.info('reset_code in')
    os.chdir(get_project_path(path, project_name))
    run_shell_command("git reset --hard HEAD~1")

    os.chdir(path)
    status, projects = run_shell_command("find * -name .git")
    project_paths = projects.split('\n')
    if status == 0:
        for project_path in project_paths:
            os.chdir(path + "/" + project_path + "/..")
            status, change = run_shell_command("git status")
            # LOG.info("%s"%change)
            if change.find("Untracked files:") >= 0 or change.find('use "git push" to publish your local commits') >= 0 or change.find("nothing to commit") == -1:
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

    for (src, dest) in copy_list.items():
        try:
            if os.path.exists(os.path.join(path, dest)) and os.path.isfile(os.path.join(path, dest)):
                os.remove(os.path.join(path, dest))
            shutil.copyfile(os.path.join(path, src), os.path.join(path, dest))
            os.chmod(os.path.join(path, dest), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        except Exception, e:
            LOG.error(e)
    LOG.info('repo_copy_files out')


def save_data(httpurl, data):
    response = None
    try:
        headers = {'Content-Type': 'application/json'}
        request = urllib2.Request(url=httpurl, headers=headers, data=json.dumps(data))
        response = urllib2.urlopen(request)
        LOG.info("url = %s;params=%s;response=%s" % (httpurl, data, response.getcode()))
    except urllib2.URLError as e:
        if hasattr(e, 'code'):
            LOG.info("url = %s;params=%s;error code=%s" % (httpurl, data, e.code))
        elif hasattr(e, 'reason'):
            LOG.info("url = %s;params=%s;error reason=%s" % (httpurl, data, e.reason))
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


def clean_out(path):
    LOG.info('clean_out in')
    os.chdir(path)
    status, outs = run_shell_command("find * -name out")
    if status == 0 and outs.strip():
        out_paths = outs.split('\n')
        for out_path in out_paths:
            out = os.path.join(path, out_path)
            shutil.rmtree(out)
            LOG.info('rm %s' % out)

    LOG.info('clean_out out')


def stringToDate(mytime):
    timeArray = time.localtime(int(mytime))
    mydate = time.strftime("%a, %d %b %Y %H:%M:%S %Z", timeArray)
    return mydate


def dateToString(mytime):
    timeArray = time.strptime(mytime, "%a, %d %b %Y %H:%M:%S %Z")
    timeStamp = int(time.mktime(timeArray))
    return timeStamp


def gmtToCst(mytime):
    gmtTime = dateToString(mytime)
    gmtTime += 8 * 3600
    return gmtTime


def getRemoteFileModifiedTime(url, proxy=None):
    opener = urllib2.build_opener()
    if proxy:
        if url.lower().startswith('https://'):
            opener.add_handler(urllib2.ProxyHandler({'https': proxy}))
        else:
            opener.add_handler(urllib2.ProxyHandler({'http': proxy}))
    try:
        request = urllib2.Request(url)
        request.get_method = lambda: 'HEAD'
        response = opener.open(request)
        response.read()
    except Exception, e:
        LOG.error(e)
        return -1
    else:
        return dict(response.headers).get("last-modified", -1)


def check_sdk_update(sdk_zip_path, sdk_zip_url):
    remote_zipfile_time = gmtToCst(getRemoteFileModifiedTime(sdk_zip_url))
    try:
        local_zipfile_time = int(os.stat(sdk_zip_path).st_mtime)
        if local_zipfile_time < remote_zipfile_time:
            LOG.info("check_sdk_update success")
            return True
        else:
            LOG.info("check_sdk_update fail")
            return False
    except Exception, e:
        LOG.error(e)
        return True


def del_sdk_temp_file(sdk_unzip_path, sdk_zip_path):
    try:
        shutil.rmtree(sdk_unzip_path)
    except Exception, e:
        LOG.error(e)

    try:
        os.remove(sdk_zip_path)
        LOG.info("del_sdk_zip success")
    except Exception, e:
        LOG.error(e)


def download_sdk_zip(sdk_add_ones_path, sdk_zip_url):
    os.chdir(sdk_add_ones_path)
    cmd = 'curl -O %s' % sdk_zip_url
    LOG.info(cmd)
    run_shell_command(cmd)


def unzip_file(file_path, dir):
    if os.path.exists(file_path) is False:
        return False

    if os.path.exists(dir) is False:
        os.makedirs(dir)
    try:
        zfile = zipfile.ZipFile(file_path, 'r')
        for filename in zfile.namelist():
            full_path = os.path.join(dir, filename)
            if full_path.endswith("/"):
                split_dir = full_path[:-1]
                if not os.path.exists(split_dir):
                    os.makedirs(split_dir)
            else:
                split_dir, _ = os.path.split(full_path)
                LOG.info(split_dir)
                if not os.path.exists(split_dir):
                    os.makedirs(split_dir)

                hFile = open(full_path, 'wb')
                hFile.write(zfile.read(filename))
                hFile.close()
        zfile.close()
    except Exception, e:
        LOG.info(e)
        return False
    return True


def copy_file(src, dir):
    if os.path.exists(src) is False:
        return False

    if os.path.exists(dir) is False:
        os.makedirs(dir)

    src_list = []

    src_list = os.listdir(src)
    for stub_path in src_list:
        try:
            if os.path.isdir(os.path.join(src, stub_path)):
                copy_file(os.path.join(src, stub_path), os.path.join(dir, stub_path))
            else:
                shutil.copy(os.path.join(src, stub_path), dir)
        except Exception, e:
            LOG.info(e)
            return False

    return True


def download_and_upzip_sdk(sdk_add_ones_path, sdk_zip_url):
    sdk_zip_path = os.path.join(sdk_add_ones_path, sdk_zip_url.split("/")[-1])
    #/home/pre_build/workspace/aurora_build_sdk/add-ons/stb_library-eng.-linux-x86.zip
    sdk_unzip_path = os.path.splitext(sdk_zip_path)[0]
    #/home/pre_build/workspace/aurora_build_sdk/add-ons/stb_library-eng.-linux-x86

    #sdk_zip_url=http://sdktest.aa.com/sdk/repository/stb_library-eng.-linux-x86.zip
    if check_sdk_update(sdk_zip_path, sdk_zip_url):
        for index in range(3):
            del_sdk_temp_file(sdk_unzip_path, sdk_zip_path)
            download_sdk_zip(sdk_add_ones_path, sdk_zip_url)
            if unzip_file(sdk_zip_path, sdk_add_ones_path):
                copy_file(sdk_unzip_path, os.path.join(sdk_add_ones_path, get_env("sdk_add_ones")))
                return True
            else:
                LOG.info('unzip_file is false')
                time.sleep(10)
    else:
        LOG.info("download_and_upzip_sdk fail")


def build(path):
    os.chdir(path)

    init_timeZone(get_running_containerid())
    init_ccache(get_running_containerid(), path)
    repo_copy_files(path)

    cmd = "docker exec -u pre_build:pre_build %s sh -c 'cd %s && ./%s sdk_root_rel=%s'" % (
    get_running_containerid(), path, sys.argv[1], sys.argv[4])
    if sys.argv[4].find(get_env("aurora_sdk")) >= 0:
        download_and_upzip_sdk(sys.argv[4], get_env("aurora_build_sdk_url"))
        cmd = "docker exec -u pre_build:pre_build %s sh -c 'cd %s && ./%s'" % (
        get_running_containerid(), path, sys.argv[1])
    LOG.info(cmd)

    status = os.system(cmd)
    if status == 0:
        LOG.info("pre build success")
        return True
    else:
        # build fail
        LOG.error("pre build fail")
        return False


def get_change_content(patch_set, gerrit_ip="10.27.254.101", gerrit_port="29000"):
    command = "ssh -p %s %s gerrit query %s --files --current-patch-set" % (gerrit_port, gerrit_ip, patch_set)
    status, content = run_shell_command(command)
    if status == 0:
        return content
    else:
        LOG.error("git change content error")
        return None


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


def post_build(base_path):
    LOG.info('post_build in')

    issue_id = get_issue_id()
    if not issue_id:
        LOG.info("get issue id error")
        # or build
        change = get_refspec().split('/')[-2]
        send_mail(get_commiter_email(),
                  "pre_build -- %s" % change,
                  """
                  Hi %s,
                  please add "Issue ID:" in Commit Message, and git commit --amend
                  %s
                  """ % (get_commiter_email().split('@')[0], GERRIT_URL + change))
        return

    project_name = get_project_name()
    ref_spec = get_refspec()   #ref_spec=refs/changes/60/118560/1
    patch_set = ref_spec.split('/')[-2]       #patch_set = 118560
    change = ref_spec.split('/')[-2]     #change = 118560
    ref_spec_new = ','.join(ref_spec.split('/')[-2:])    #ref_spec_new = 118560,1
    commiter_email = get_commiter_email()
    user_name = commiter_email.split('@')[0]

    run_gerrit_command(project_name, "0", 'Build Start ' + get_env('BUILD_URL') + 'console', ref_spec_new)
    # run_gerrit_command(ssh -p 29000 10.27.254.101 gerrit review --project android/LiveSettings --verified 0 --message '"Build Start http://10.27.16.83:8080/job/pre_build_app_aurora_slave/209/console"' 118560,1)
    update_code(base_path, project_name, ref_spec)

    build_start_time = time.strftime("%Y-%m-%d %X", time.localtime())
    clean_out(base_path)
    build_result = build(base_path)
    if build_result:
        mail_content = """
          Hi %s,
          Your commit build successful
          %s
          see the build detail
          %s
           """ % (user_name, GERRIT_URL + change, get_env('BUILD_URL') + 'console')
        run_gerrit_command(project_name, "+1", 'Build Successful ' + get_env('BUILD_URL') + 'console', ref_spec_new)
        run_gerrit_submit_command(ref_spec_new)
    else:
        mail_content = """
          Hi %s,
          Your commit build failed
          %s
          see the build detail
          %s
           """ % (user_name, GERRIT_URL + change, get_env('BUILD_URL') + 'console')
        run_gerrit_command(project_name, "-1", 'Build Failed ' + get_env('BUILD_URL') + 'console', ref_spec_new)

    reset_code(base_path, project_name)
    save_build_result(sys.argv[3], sys.argv[2].split('/')[-1], issue_id, build_start_time, build_result)
    send_mail(commiter_email,
              "pre_build -- %s" % change,
              mail_content)
    save_commit(sys.argv[3], issue_id, GERRIT_URL + change, build_result)

    LOG.info('post_build out')
    return build_result


def main():
    LOG.info('main in')

    filter_commiter()

    LOG.info(sys.argv)
    ret = post_build(get_env("WORKSPACE"))

    LOG.info('main out')
    sys.exit(0 if ret else -1)


if __name__ == '__main__':
    main()

