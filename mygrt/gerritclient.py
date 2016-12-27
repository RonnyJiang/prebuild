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
from requests.auth import HTTPDigestAuth


class GerritClient(object):
    __url = None
    __user = None
    __passwd = None
    __guuid = None

    def __str__(self):
        return 'GerritClient object(USER: %s)' % self.__user

    def __init__(self,username,passwd,url):
        self.__user = username
        self.__passwd = passwd
        self.__url = url

    def getGroupUUID(self,groupname):
        pass


    def getAccessInfo(self,projectname):
        data = urllib.urlencode({'project': projectname})
        addr = "a/access/?%s" % data
        return self.GET(address=addr)

    def GET(self,address):
        return self.send(address,method="GET")


    def POST(self,address,data):
        return self.send(address,method="POST")

    def PUT(self,address,data):
        return self.send(address,method="PUT")

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
            print ("runing1 send  %s request...." % method)
            response = requests.post(url=address,
                                     headers=headers,
                                     auth=HTTPDigestAuth(self.__user,self.__passwd),
                                     data=json.dumps(data))
        elif method == "PUT":
            print ("runing2 send  %s request...." % method)
            response = requests.put(url=address,
                                    headers=headers,
                                    auth=HTTPDigestAuth(self.__user,self.__passwd),
                                    data=json.dumps(data))

        responseJson = response.content.replace(')]}\'','',1)
        return json.loads(responseJson)


def main():
    mygerrit = GerritClient(username="ronnyjiang",passwd="dbwhhp4E3tjC",url="http://10.27.254.101:2089")
    print (mygerrit)
    # res = mygerrit.GET("groups/")
    # project_name = 'android/Billing'
    project_name="android/Live"
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


    res = mygerrit.getAccessInfo(project_name)
    print (res,type(res))

if __name__ == '__main__':
    main()

