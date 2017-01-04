# -*- coding: utf-8 -*-
"""
 @Desc: 动态回收prebuild repo项目的verify　-1..+1权限.
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: change_access_config.py
 @Software: PyCharm  @since:python 2.7.3(32bit) on 16-12-20.下午1:39
"""
import logging
import os
import re
import sys
import restclient

global RESET_REMOTE_CONFIG
RESET_REMOTE_CONFIG = False
global INIT_REMOTE_CONFIG
INIT_REMOTE_CONFIG = False


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
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'change_access_config.log'))
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


def analyzeArgs(args):
    LOG.info(args)
    if len(args) != 3:
        LOG.info("Error, invalid parameters")
        sys.exit(-1)
    for arg in args:
        if arg == '--reset_remote_config':
            global RESET_REMOTE_CONFIG
            RESET_REMOTE_CONFIG = True
        if arg == '--init_remote_config':
            global INIT_REMOTE_CONFIG
            INIT_REMOTE_CONFIG = True

def init_prebuild_project(project_name,project_branch):
    LOG.info("Init project:%s ,branch:%s" % (project_name, project_branch))

def add_refs_verified_context(resAccessinfo,refslabel,project_name):
    if refslabel in resAccessinfo[project_name]["local"].keys():
        print ("***%s is verfied for %s----%s" % (project_name, refslabel,resAccessinfo[project_name]["local"].keys()))
    else:
        print ("--- %s is not verfied for %s ---%s" % (project_name, refslabel,resAccessinfo[project_name]["local"].keys()))

def add_refs_review_context():
    pass





def reset_prebuild_project(project_name,project_branch):
    LOG.info("Reset project:%s ,branch:%s" % (project_name, project_branch))


def get_project_list(trigger_file):
    LOG.info("get project list IN")
    git_list = {}
    rex_noGroup = "p=.+\s+b=.*\s*"
    rex_namedGroup = "p=(?P<project>.+)\s+b=(?P<branch>.*)\s*"
    repo_config_file = open(trigger_file,'r')
    try:
        content = repo_config_file.read()
        total_project = re.findall(rex_noGroup, content)
        for index,one_project in enumerate(total_project):
            result = re.search(rex_namedGroup, one_project)
            git_list[result.group('project')] = result.group('branch')
    except Exception, exp:
        LOG.error('get_project_list Exception:%s', exp)
    finally:
        repo_config_file.close()
    LOG.info("get project list OUT")
    return git_list

def check_file_and_get_project_list(trigger_file):
    LOG.info("check_trigger_config_file: %s" % trigger_file)
    if os.path.exists(trigger_file):
        reset_project_list = get_project_list(trigger_file)
        if not reset_project_list:
            LOG.info("The %s cannot find project and branch,file content is empty or format error!" % trigger_file)
            return None
        LOG.info("Obtain project list from %s successfully" % trigger_file)
        return reset_project_list
    else:
        LOG.info("The %s cannot be found!" % trigger_file)
        return None

def init_verify_rights():
    LOG.info("init_verify_rights IN")
    init_project_list = check_file_and_get_project_list(sys.argv[1])
    if init_project_list is not None:
        for initProjKey in init_project_list.keys():
            init_prebuild_project(initProjKey,init_project_list[initProjKey])
    else:
        LOG.info("Init failed! Please check the file: %s" % sys.argv[1])
    LOG.info("init_verify_rights OUT")

def test_check_verify_rights():
    LOG.info("init_verify_rights IN")
    init_project_list = check_file_and_get_project_list(sys.argv[1])
    if init_project_list is not None:
        for initProjKey in init_project_list.keys():
            init_prebuild_project(initProjKey,init_project_list[initProjKey])
    else:
        LOG.info("Init failed! Please check the file: %s" % sys.argv[1])
    LOG.info("init_verify_rights OUT")

def update_verify_rights():
    LOG.info("update_verify_rights IN")
    new_project_list = check_file_and_get_project_list(sys.argv[1])
    bak_project_list = check_file_and_get_project_list(sys.argv[2])
    if new_project_list is None or bak_project_list is None:
        LOG.info("Error,Please check %s and %s" % (sys.argv[1],sys.argv[2]))
        sys.exit(-1)
    for bakProjKey in bak_project_list.keys():
        if new_project_list.has_key(bakProjKey) and new_project_list[bakProjKey]==bak_project_list[bakProjKey]:
            new_project_list.pop(bakProjKey)
        else:
            reset_prebuild_project(bakProjKey,bak_project_list[bakProjKey])

    if new_project_list:
        for newProjKey in new_project_list.keys():
            init_prebuild_project(newProjKey,new_project_list[newProjKey])
    LOG.info("update_verify_rights OUT")

def reset_verify_rights():
    LOG.info("reset verify rights IN")
    reset_project_list = check_file_and_get_project_list(sys.argv[1])
    if reset_project_list is not None:
        for resetProjKey in reset_project_list.keys():
            reset_prebuild_project(resetProjKey,reset_project_list[resetProjKey])
    else:
        LOG.info("Reset failed! Please check the file: %s" % sys.argv[1])
    LOG.info("reset verify rights OUT")

def change_remote_verify_rights():
    LOG.info("change remote verify rights IN")
    global RESET_REMOTE_CONFIG
    if INIT_REMOTE_CONFIG:
        init_verify_rights()
    elif RESET_REMOTE_CONFIG:
        reset_verify_rights()
    else:
        update_verify_rights()
    LOG.info("change remote verify rights OUT")

def main():
    LOG.info("------------------------------------------------------")
    LOG.info("main IN")
    analyzeArgs(sys.argv)
    mygerritclient = restclient.RestClient(username="pre_build",
                                             passwd="Tr9WvxfyYuAk",
                                             url="http://10.27.254.101:2089")
    print (mygerritclient)
    print (mygerritclient.getGroupUUID("tools"))
    test_project_list = check_file_and_get_project_list(sys.argv[1])
    print (test_project_list)
    if test_project_list is not None:

        for testProjKey in test_project_list.keys():
            resAccessinfo = mygerritclient.getAccessInfo(projectname=testProjKey)
            refslabel = "refs/heads/%s" % test_project_list[testProjKey]

            add_refs_verified_context(resAccessinfo=resAccessinfo,refslabel=refslabel,project_name=testProjKey)
    else:
        LOG.info("Init failed! Please check the file: %s" % sys.argv[1])
    # change_remote_verify_rights()
    LOG.info("main OUT")
    LOG.info("------------------------------------------------------")


    # usage:
    #   init verify rights:
    #                 python change_access_config.py aurora_plus_trigger_config --init_remote_config
    #　　update verify rights:
    #                 python change_access_config.py aurora_plus_trigger_config aurora_plus_trigger_config.bak
    #   reset verify rights:
    #                 python change_access_config.py aurora_plus_trigger_config.bak --reset_remote_config

if __name__ == '__main__':
    main()
