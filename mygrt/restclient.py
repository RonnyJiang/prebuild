
# -*- coding: utf-8 -*-
"""
 @Desc: gerrit client: generate gerrit authorization object,get gerrit user group(UUID),and send request info
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: restclient.py
 @Software: PyCharm  @since:python 3.5.2(32bit) on 16-12-27.下午12:42
"""

import requests
import os
import json
import urllib

from requests.auth import HTTPDigestAuth



class RestClient(object):
    __url = None
    __user = None
    __passwd = None

    def __str__(self):
        return 'RestClient object(USER: %s)' % self.__user

    def __init__(self,username,passwd,url):
        self.__user = username
        self.__passwd = passwd
        self.__url = url

    # def getGroupUUID(self,groupname):
    #     try:
    #         addr = "a/groups/"
    #         allgroups = self.GET(address=addr)
    #         if groupname in allgroups.keys():
    #             # LOG.info(allgroups.keys())
    #             return allgroups[groupname]["owner_id"]
    #         else:
    #             return None
    #     except StandardError,e:
    #         LOG.exception(e)
    #     finally:
    #         print ('--getGroupUUID END--')


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
        # address = os.path.join(self.__url,addr)
        address = "%s/%s" % (self.__url,addr)
        headers = {'Content-Type': 'application/json;charset=UTF-8',
                   'Accept': 'application/json'
                   }
        print ("runing send  %s request: %s" % (method, address))
        if method == "GET":
            response = requests.get(url=address,
                                    headers=headers,
                                    auth=HTTPDigestAuth(self.__user,self.__passwd))

        elif method == "POST":
            response = requests.post(url=address,
                                     headers=headers,
                                     auth=HTTPDigestAuth(self.__user,self.__passwd),
                                     data=json.dumps(data))
        elif method == "PUT":
            response = requests.put(url=address,
                                    headers=headers,
                                    auth=HTTPDigestAuth(self.__user,self.__passwd),
                                    data=json.dumps(data))
        if response.ok:
            responseJson = response.content.replace(')]}\'', '', 1)
            # print ("--1--",responseJson)
            return json.loads(responseJson)
        else:
            print "================"


def main():
    # mygerrit = GerritClient(username="ronnyjiang",passwd="dbwhhp4E3tjC",url="http://10.27.254.101:2089")
    mygerrit = RestClient(username="pre_build", passwd="Tr9WvxfyYuAk", url="http://10.27.254.101:2089")
    print (mygerrit)

    # res = mygerrit.GET("a/groups/?owned&q=tools")
    # print (res["tools"]["owner_id"])
    changeId = "58efe6627c0265af6eaa8bd076c41e7436ebf002"
    response1 = mygerrit.GET(address="a/changes/?q=" + changeId + "&o=CURRENT_REVISION&o=DOWNLOAD_COMMANDS")
    print (response1[0])
#     # guuid = mygerrit.getGroupUUID("tools")
#     # print (guuid)
#
if __name__ == '__main__':
    main()

