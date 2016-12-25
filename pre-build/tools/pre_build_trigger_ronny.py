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
from xml.etree import ElementTree

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
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pre_build_trigger_ronny.log'))
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

def parse_xml(xml_file, project_list, branch='master'):
    os.chdir(get_env("WORKSPACE"))
    xml_path = os.path.join(get_env("WORKSPACE"), xml_file)
    root = ElementTree.parse(xml_path)

    default_branch = branch
    default_node = root.find('default')
    if default_node is not None:
        default_branch = default_node.get('revision')

    project_node = root.findall('project')
    for project_node_item in project_node:
        project_name = project_node_item.get('name')
        project_branch = default_branch
        if project_node_item.get('revision') is not None:
            project_branch = project_node_item.get('revision')
        project_list[project_name] = project_branch

    include_node = root.findall('include')
    for include_node_item in include_node:
        parse_xml(include_node_item.get("name"), project_list, default_branch)

    return project_list

def parse_xmls(xml_file, project_list, branch='master'):
    os.chdir('/home/pre_build/workspace/pre_build_master_trigger')
    xml_path = os.path.join('/home/pre_build/workspace/pre_build_master_trigger', xml_file)
    root = ElementTree.parse(xml_path)

    default_branch = branch
    default_node = root.find('default')
    if default_node is not None:
        default_branch = default_node.get('revision')

    project_node = root.findall('project')
    for project_node_item in project_node:
        project_name = project_node_item.get('name')
        project_branch = default_branch
        if project_node_item.get('revision') is not None:
            project_branch = project_node_item.get('revision')
        project_list[project_name] = project_branch

    include_node = root.findall('include')
    for include_node_item in include_node:
        parse_xmls(include_node_item.get("name"), project_list, default_branch)

    return project_list

def get_profile_list(content):
    profile_list = {}
    rex_noGroup = "repo_xml=.+\s+repo_config_path=.+\s*"
    rex_namedGroup = "repo_xml=(?P<xml>.+)\s+repo_config_path=(?P<trigger_config_path>.+)\s*"
    total_xml = re.findall(rex_noGroup, content)
    for index,one_xml in enumerate(total_xml):
        LOG.info("index=%s(%s)" % (index,one_xml))
        result = re.search(rex_namedGroup, one_xml)
        profile_list[result.group('xml')] = result.group('trigger_config_path')

    return profile_list

def get_change_content(gerrit_ip="10.27.254.101", gerrit_port="29000"):
    change_id = get_env("GERRIT_CHANGE_ID")
    command = "ssh -p %s %s gerrit query %s --files --current-patch-set" % (gerrit_port, gerrit_ip, change_id)
    status,content = run_shell_command(command)
    if status == 0:
        LOG.info("get_change_content = %s" % content)
        return content
    else:
        LOG.error("get change content error")
        return None

def update_trigger_config():
    LOG.info('update_trigger_config in')

    change_content = get_change_content()
    profile_list = get_profile_list(get_env("profile"))

    for (K,V) in profile_list.items():
        if change_content.find(K) >= 0:
            project_list = {}
            parse_xml(K, project_list)
            LOG.info("project_list = %s"%project_list)

            config_file_w = open(V,"w")
            for (key,value) in project_list.items():
                config_file_w.write("p="+key+"\n"+"b="+value+"\n")
            config_file_w.close()

    LOG.info('update_trigger_config out')

def create_trigger_config():
    LOG.info('create_trigger_config in')
    project_list = {}
    K='aurora.xml'
    V = '/var/ftpd/incoming/pre_build_config/aurora_puls_trigger_config'
    parse_xmls(K, project_list)
    LOG.info("project_list = %s"%project_list)

    # config_file_w = open(V,"w")
    # for (key,value) in project_list.items():
    #     config_file_w.write("p="+key+"\n"+"b="+value+"\n")
    #     config_file_w.close()

    LOG.info('create_trigger_config out')

def main():
    LOG.info('main in')

    create_trigger_config()

    LOG.info('main out')

if __name__ == '__main__':
    main()