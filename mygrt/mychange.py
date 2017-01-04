# -*- coding: utf-8 -*-
"""
 @Desc:
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: 
 @Software: PyCharm  @since:python 3.5.2(32bit) on 16-12-27.下午12:39
"""

import os
class Change(object):
    changeInfo = None
    changeUrl = None
    conn = None
    def __init__(self,conn,changeId):
        self.conn = conn
        self.changeInfo = self.conn.GET(self.conn.GET("a/changes/?q=" + changeId + "&o=CURRENT_REVISION&o=DOWNLOAD_COMMANDS")[0])
        # self.changeUrl = os.path.join("a/changes/", self.changeInfo["id"])
        # self.changeUrl = "%s/%s" % ("a/changes/",self.changeInfo["id"])

    def setReview(self):
        pass
