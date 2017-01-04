# -*- coding: utf-8 -*-
"""
 @Desc:
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: 
 @Software: PyCharm  @since:python 3.5.2(32bit) on 16-12-27.下午12:43
"""

from mychange import Change
from restclient import RestClient

class Gerrit(object):
    conn = None
    def __init__(self,user,password,url):
        self.conn = RestClient(user,password,url)

    def getChange(self,changeId):
        return Change(self.conn,changeId)

    def getGroupUUID(self,groupname):
        try:
            # addr = "a/groups/"
            addr = "a/groups/?owned&q=%s" % groupname
            allgroups = self.conn.GET(address=addr)
            if groupname in allgroups.keys():
                return allgroups[groupname]["owner_id"]
            else:
                return None
        except StandardError,e:
            print 'except:', e


def main():
    gerrit =Gerrit("pre_build","Tr9WvxfyYuAk","http://10.27.254.101:2089")
    uuid = gerrit.getGroupUUID("tools")
    print (uuid)

    print (gerrit.getChange("58efe6627c0265af6eaa8bd076c41e7436ebf002"))

if __name__ == "__main__":
    main()

