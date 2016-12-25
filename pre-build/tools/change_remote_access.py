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
import urllib2
import re
import sys
import logging
import commands

global RESET_REMOTE_CONFIG
RESET_REMOTE_CONFIG = False
PREBUILD_KEY = "xxx"
PREBUILD_GROUP = "tools"

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
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'change_access.log'))
    file.setFormatter(formatter)
    logger.addHandler(file)
    logger.setLevel(logging.INFO)
    return logger

LOG = GetLog()

def run_shell_command(cmd):
    sys = os.name
    if sys == 'posix':
        LOG.info(cmd)
        return commands.getstatusoutput(cmd)
    else:
        return 'System of The PC is not a posix'

def change_project_access(remote_project_list, root_path):
    os.system('''(repo forall -c 'CHANGE_ID=`git log --before="1 days" -1 --pretty=format:"%H"`;git reset --hard $CHANGE_ID')''')
    os.system("repo sync")
    os.system("repo checkout master")
    os.system("repo forall -c git fetch origin refs/meta/config:config")
    os.system("repo checkout config")
    analyzeArgs(sys.argv)
    global RESET_REMOTE_CONFIG
    status, projects = run_shell_command("find * -name .git")
    project_paths = projects.split('\n')
    if status == 0:
        for project_path in project_paths:
            os.chdir(root_path + "/" + project_path + "/..")
            _,local_path = run_shell_command("pwd")
            _,project_name = run_shell_command("git config --get remote.origin.projectname")
            if handle_config_file(remote_project_list, local_path, project_name):
                if RESET_REMOTE_CONFIG:
                    os.system("git add -")
                else:
                    os.system("git add groups project.config")
                os.system("git status")
                os.system("git commit -m 'Modify access rules'")
                #os.system("git push origin config:refs/for/refs/meta/config")
                os.system("git push origin config:refs/meta/config")
    os.system("repo checkout master")

def analyzeArgs(args):
    for arg in args:
        if arg == '--reset_remote_config':
            global RESET_REMOTE_CONFIG
            RESET_REMOTE_CONFIG = True

def handle_config_file(remote_project_list, local_path, project_name):
    if not project_name:
        return False

    if remote_project_list.has_key(project_name):
        remote_project_name = project_name
        remote_project_branch = remote_project_list[project_name]
        LOG.info("name=%s;branch=%s"%(remote_project_name, remote_project_branch))
        if not remote_project_branch:
            return False

        old_config_content = ''
        old_groups_content = ''
        analyzeArgs(sys.argv)
        global RESET_REMOTE_CONFIG

        if os.path.exists("project.config"):
            config_file_r = open("project.config","r")
            old_config_content = config_file_r.read()
            config_file_r.close()

            if old_config_content.find("refs/heads/%s"%(remote_project_branch)) >= 0 :
                if RESET_REMOTE_CONFIG:
                    if old_config_content.count("[access") == 1:
                        os.remove('project.config')
                        os.remove('groups')
                        return True
                    elif old_config_content.count("[access") > 1:
                        config_file_w = open("project.config","w")
                        config_file_w.write(old_config_content.replace('%s[access "refs/heads/%s"]\n\texclusiveGroupPermissions = label-Verified\n\tlabel-Verified = -1..+1 group %s\n'%(old_config_content, remote_project_branch, PREBUILD_GROUP),""))
                        config_file_w.close()
                        return True
                else:
                    return False
            elif RESET_REMOTE_CONFIG:
                return False
        elif RESET_REMOTE_CONFIG:
                return False

        if os.path.exists("groups") and os.path.getsize("groups") > 0:
            groups_file_r = open("groups","r")
            old_groups_content = groups_file_r.read()
            groups_file_r.close()

        config_file_w = open("project.config","w")
        config_file_w.write('%s[access "refs/heads/%s"]\n\texclusiveGroupPermissions = label-Verified\n\tlabel-Verified = -1..+1 group %s\n'%(old_config_content, remote_project_branch, PREBUILD_GROUP))
        config_file_w.close()

        groups_w = open("groups","w")
        if not old_groups_content:
            groups_w.write('# UUID                                  \tGroup Name\n#\n%s\t%s\n'%(PREBUILD_KEY, PREBUILD_GROUP))
        elif old_groups_content.find("tools") == -1:
	    groups_w.write("%s%s\t%s\n"%(old_groups_content, PREBUILD_KEY, PREBUILD_GROUP))
        else:
            groups_w.write(old_groups_content)
        groups_w.close()

        return True
    else:
        return False

def get_project_list():
    git_list = {}
    rex_noGroup = "p=.+\s+b=.*\s+"
    rex_namedGroup = "p=(?P<project>.+)\s+b=(?P<branch>.*)\s+"
    repo_config_file = urllib2.urlopen(sys.argv[1], timeout=10)
    try:
        content = repo_config_file.read()
        total_project = re.findall(rex_noGroup, content)
        for index,one_project in enumerate(total_project):
            LOG.info("index=%s(%s)" % (index,one_project))
            result = re.search(rex_namedGroup, one_project)
            git_list[result.group('project')] = result.group('branch')
    except Exception, exp:
        LOG.error('get_project_list Exception:%s', exp)
    finally:
        repo_config_file.close()

    return git_list

def main():
    remote_project_list = get_project_list()
    if len(remote_project_list) == 0:
        LOG.error('remote_project_list is NULL')
        return

    change_project_access(remote_project_list, os.getcwd())

if __name__ == '__main__':
    main()
