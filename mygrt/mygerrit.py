# -*- coding: utf-8 -*-
"""
 @Desc:
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: 
 @Software: PyCharm  @since:python 3.5.2(32bit) on 16-12-27.下午12:43
"""
from change import Change, CommentsList
from connectionhelper import ConnectionHelper
class Gerrit(object):
    conn = None
    def __init__(self, user, password, url):
        self.conn = ConnectionHelper(user, password, url)
    def getReviewedChanges(self):
return self.conn.GET("a/changes/?q=reviewer:"+ self.conn.user+"+AND+status:open")
def getChange(self, changeId):
return Change(self.conn, changeId)
def main():
gerrit = Gerrit("", "", "")
changeId = ""
# changes = gerrit.getReviewedChanges()
# print changes
# for c in changes:
# print c.owner.name
# change = gerrit.getChange(changeId)
# print change.changeInfo.id
# # print change.createDraft("db/rules-db.sql", 584, "TEST DRAFT COMMENT")
# cl = CommentsList ()
# cl.addComment(path = "db/rules-db.sql", line = 581, message ="TEST COMMENT")
# print change.setReview(message = "TEST MESS", codeReview = -1, verified = -1, comments =cl)
# # r = change.rebase()
# print r
if __name__ == "__main__":
main()