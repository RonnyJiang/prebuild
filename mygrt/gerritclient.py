# -*- coding: utf-8 -*-
"""
 @Desc: gerrit client: generate gerrit authorization object,get gerrit user group(UUID),and send request info
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: gerritclient.py
 @Software: PyCharm  @since:python 3.5.2(32bit) on 16-12-27.下午12:42
"""

import requests
import os
import json
import urllib
import logging
from requests.auth import HTTPDigestAuth

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
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'gerrit_client.log'))
    file.setFormatter(formatter)
    logger.addHandler(file)
    logger.setLevel(logging.INFO)
    return logger

LOG = GetLog()

class GerritClient(object):
    __url = None
    __user = None
    __passwd = None

    def __str__(self):
        return 'GerritClient object(USER: %s)' % self.__user

    def __init__(self,username,passwd,url):
        self.__user = username
        self.__passwd = passwd
        self.__url = url

    def getGroupUUID(self,groupname):
        try:
            addr = "a/groups/"
            allgroups = self.GET(address=addr)
            if groupname in allgroups.keys():
                # LOG.info(allgroups.keys())
                return allgroups[groupname]["owner_id"]
            else:
                return None
        except StandardError,e:
            LOG.exception(e)
        finally:
            print ('--getGroupUUID END--')


    def getAccessInfo(self,projectname):
        projecturl = urllib.urlencode({'project': projectname})
        addr = "a/access/?%s" % projecturl
        return self.GET(address=addr)

    def putAccessInfo(self,projectname,data):
        projecturl = urllib.urlencode({'project': projectname})
        addr = "a/access/?%s" % projecturl
        return self.PUT(address=addr,data=data)

    def GET(self,address):
        return self.send(address,method="GET")


    def POST(self,address,data):
        return self.send(address,method="POST",data=data)

    def PUT(self,address,data):
        return self.send(address,method="PUT",data=data)

    def send(self,addr,method,data={}):
        response = None
        address = os.path.join(self.__url,addr)
        print (address)
        headers = {'Content-Type': 'application/json;charset=UTF-8',
                   'Accept': 'application/json'
                   }
        if method == "GET":
            print ("runing send  %s request...." % method)
            response = requests.get(url=address,
                                    headers=headers,
                                    auth=HTTPDigestAuth(self.__user,self.__passwd))

        elif method == "POST":
            print ("runing send  %s request...." % method)
            response = requests.post(url=address,
                                     headers=headers,
                                     auth=HTTPDigestAuth(self.__user,self.__passwd),
                                     data=json.dumps(data))
        elif method == "PUT":
            print ("runing send  %s request...." % method)
            response = requests.put(url=address,
                                    headers=headers,
                                    auth=HTTPDigestAuth(self.__user,self.__passwd),
                                    data=json.dumps(data))

        responseJson = response.content.replace(')]}\'','',1)


        if response.ok:
            return json.loads(responseJson)
        else:
            print "================"


def main():
    # mygerrit = GerritClient(username="ronnyjiang",passwd="dbwhhp4E3tjC",url="http://10.27.254.101:2089")
    mygerrit = GerritClient(username="pre_build", passwd="Tr9WvxfyYuAk", url="http://10.27.254.101:2089")
    print (mygerrit)
    # res = mygerrit.GET("groups/")
    #project_name = 'android/Billing'
    project_branch = 'master'
    project_name="android/Settings"
    # data = urllib.urlencode({'project': project_name})
    """
    u'refs/heads/master': {
            u'permissions': {
                u'label-Verified': {
                    u'rules': {
                        u'827de1e3b53db7a2f6c1a3ee24b3f2d7a47f0fxx': {
                            u'action': u'ALLOW',
                            u'max': 1,
                            u'min': -1
                        }
                    },
                    u'exclusive': True,
                    u'label': u'Verified'
                }
            }
    },
    """
    # res = mygerrit.GET("a/groups/?owned&q=tools")
    # print (res)
    resAccessinfo = mygerrit.getAccessInfo(project_name)
    verify_branch = "refs/heads/%s" % project_branch
    print (resAccessinfo)
    print (resAccessinfo.keys())
    # print (resAccessinfo[project_name].keys())
    # print (resAccessinfo[project_name]["local"].keys())
    # print (resAccessinfo[project_name]["local"][verify_branch])
    # print (resAccessinfo[project_name]["local"][verify_branch].keys())
    # print (resAccessinfo[project_name]["local"][verify_branch]["permissions"])
    # print (resAccessinfo[project_name]["local"][verify_branch]["permissions"].keys())


    # verified_data = {project_name:
    #                      {"local":{verify_branch:
    #                                {"permissions":
    #                                     {"label-Verified":
    #                                          {"rules":
    #                                               {"827de1e3b53db7a2f6c1a3ee24b3f2d7a47f0f8a":
    #                                                    {"action": "ALLOW",
    #                                                     "max": 1,
    #                                                     "min": -1}
    #                                                },
    #                                           "exclusive": True,
    #                                           "label": "Verified"}
    #                                      }
    #                                 }
    #                            }
    #                       }
    #                  }


    verified_data = {"add":[verify_branch:{"permissions":{"label-Verified":{"rules":{"827de1e3b53db7a2f6c1a3ee24b3f2d7a47f0f8a":{"action": "ALLOW","max": 1,"min": -1}},"exclusive": True,"label": "Verified"}}}]}

    result = mygerrit.POST(address="a/projects/android%2FSettings/access",data=verified_data)

    print (result)

    # resAccessinfo[project_name]["local"][verify_branch] = verified_data
    #
    # aa_str = '{"android/Settings": {"local": {"refs/heads/master": {"permissions": {"label-Verified": {"rules": {"827de1e3b53db7a2f6c1a3ee24b3f2d7a47f0f8a": {"action": "ALLOW", "max": 1, "min": -1}}, "exclusive": true, "label": "Verified"}}}}}}'
    # newresAccessinfo = mygerrit.putAccessInfo(projectname=project_name,data=json.loads(aa_str))
    # print (verified_data.keys())
    # print (verified_data[project_name])
    # print (verified_data[project_name].keys())
    # print (verified_data[project_name]["local"])
    # print (verified_data[project_name]["local"].keys())
    # print (verified_data[project_name]["local"][verify_branch])
    # print (verified_data[project_name]["local"][verify_branch].keys())
    # print (verified_data[project_name]["local"][verify_branch]["permissions"])
    # print (verified_data[project_name]["local"][verify_branch]["permissions"].keys())
    # print (verified_data[project_name]["local"][verify_branch]["permissions"]["label-Verified"])
    # print (verified_data[project_name]["local"][verify_branch]["permissions"]["label-Verified"].keys())
    # print (verified_data[project_name]["local"][verify_branch]["permissions"]["label-Verified"]["rules"])
    # print (verified_data[project_name]["local"][verify_branch]["permissions"]["label-Verified"]["rules"].keys())

    # print (resAccessinfo[project_name]["local"]["refs/*"])
    # print (resAccessinfo[project_name]["local"]["refs/*"]["permissions"]["label-Verified"])

    # verified_data = {"permissions":
    #                      {"label-Verified":
    #                           {"rules":
    #                                {"827de1e3b53db7a2f6c1a3ee24b3f2d7a47f0f8a":
    #                                     {"action": "ALLOW",
    #                                      "max": 1,
    #                                      "min": -1}
    #                                 },
    #                            "exclusive": True,
    #                            "label": "Verified"
    #                            }
    #                       }
    #                  }
    # print (type(verified_data))
    # verified_data["permissions"] = "label-Verified"
    # verified_data["permissions"]["label-Verified"] = ["rules","exclusive","label"]
    # verified_data["permissions"]["label-Verified"]["exclusive"] = True
    # verified_data["permissions"]["label-Verified"]["label"] = "Verified"
    #
    # verified_data["permissions"]["label-Verified"]["rules"] = 0



    # print (verified_data)
    # verified_data["permissions"]["label-Verified"] =
    # resAccessinfo[project_name]["local"][verify_branch]={u'permissions': {u'label-Verified': {u'rules': {u'827de1e3b53db7a2f6c1a3ee24b3f2d7a47f0f8a': {u'action': u'ALLOW', u'max': 1, u'min': -1}}, u'exclusive': True, u'label': u'Verified'}}}
    # if verify_branch in resAccessinfo[project_name]["local"].keys():
    #     print (resAccessinfo[project_name]["local"][verify_branch])
    # res = mygerrit.getAccessInfo(project_name)[project_name]["local"]["refs/heads/master"]
    #{u'permissions': {u'label-Verified': {u'rules': {u'827de1e3b53db7a2f6c1a3ee24b3f2d7a47f0f8a': {u'action': u'ALLOW', u'max': 1, u'min': -1}}, u'exclusive': True, u'label': u'Verified'}}}
    #{u'permissions': {u'label-Verified': {u'rules': {u'827de1e3b53db7a2f6c1a3ee24b3f2d7a47f0f8a': {u'action': u'ALLOW', u'max': 1, u'min': -1}}, u'exclusive': True, u'label': u'Verified'}}}

    # guuid = mygerrit.getGroupUUID("tools")
    # print (guuid)

if __name__ == '__main__':
    main()

