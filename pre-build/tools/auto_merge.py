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
import re

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
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'auto_merge.log'))
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

def get_env(ev):
    return os.environ.get(ev)

def get_whitelist():
    return get_env("whitelist")

def get_commiter_email():
    return get_env("GERRIT_CHANGE_OWNER_EMAIL")

def get_project_name():
    return get_env("GERRIT_PROJECT")

def get_refspec():
    return get_env("GERRIT_REFSPEC")

def run_gerrit_command(project, patch_set, verified="+1", manual_test="+1", code_review="+2", gerrit_ip="10.27.254.101", gerrit_port="29000"):
    command = "ssh -p %s %s gerrit review --project %s --verified %s --manual-test %s --code-review %s --submit %s" % (
        gerrit_port, gerrit_ip, project, verified, manual_test, code_review, patch_set)
    run_shell_command(command)

def cmp_with_commiter():
    whitelist = get_whitelist().split(';')
    for item in whitelist:
        if item.strip()=='':
            continue
        if item == get_commiter_email():
            LOG.info("commiter(%s) is in whitelist, allow to auto-merge"%(item))
            return True
        
    LOG.info("commiter(%s) isn't in whitelist, not allow to auto-merge"%(item))
    return False

def merge_to_server():
    LOG.info('merge_to_server in')

    if cmp_with_commiter() is True:
        project_name = get_project_name()
        ref_spec = ','.join(get_refspec().split('/')[-2:])
        run_gerrit_command(project_name, ref_spec)

    LOG.info('merge_to_server out')

def main():
    LOG.info('main in')

    merge_to_server()

    LOG.info('main out')

if __name__ == '__main__':
    main()