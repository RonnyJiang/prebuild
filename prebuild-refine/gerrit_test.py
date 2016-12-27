# -*- coding: utf-8 -*-
"""
 @Desc:
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: gerrit_test.py
 @Software: PyCharm  @since:python 3.5.2(32bit) on 16-12-23.上午10:52
"""
import urllib,urllib2
import json
import requests
from requests.auth import HTTPDigestAuth




def get_project_mes(project_name):
    data = urllib.urlencode({'project':project_name})
    print (data)
    gerrit_get_url = "http://10.27.254.101:2089/a/access/?%s" % data
    # gerrit_get_url = "http://10.27.254.101:2089/groups/"
    # gerrit_get_url = "http://10.27.254.101:2089/"
    print (gerrit_get_url)
    r = requests.get(url=gerrit_get_url, auth=HTTPDigestAuth('ronnyjiang','dbwhhp4E3tjC'))

    # print (r.status_code)
    if r.status_code == 200:
        rel_content = r.content[4:]
        print (r.content)
        s = json.loads(rel_content)
        print (s.keys())

        # print ('-------------------------')
        # print (rel_content)
    else:
        print ("error request")
    # r = requests.get(url=gerrit_get_url, auth=HTTPBasicAuth('RonnyJiang', 'Cos*142527'))
    # request = urllib2.Request(gerrit_project_url)
    # print (request)
    # response = urllib2.urlopen(request)
    # print (response)
    # print type(response)
    # print (response.read())



if __name__ == '__main__':
    # get_version='config/server/version'
    # get_messages(get_version)

    get_project='android/Billing'
    get_project_mes(get_project)




#
# def doPost(data1,data2):
#     data = urllib.urlencode({'data1':data1,'data2':data2})
#     print (data)
#     request = urllib2.Request('www.baidu.com',data)
#     # response = urllib2.urlopen(request)
#     # file = response.read()
#     # print (file)
#
# doPost('allow','deny')

##post info
# def post_messages():
#     # gerrit_project_url = "www.gerrit.com:29000"
#
#     # data = urllib.urlencode({'data1':"111",'data2':"222"})
#     headers = {'Content-Type': 'application/json'}
#     request = urllib2.Request(url=gerrit_project_url,data=json.dumps(data),headers=headers)
#     response = urllib2.urlopen(request)


# def get_messages(getinfo):
#     gerrit_get_url = "http://10.27.254.101:2089/%s" % getinfo
#     print (gerrit_get_url)
#     r = requests.get(url=gerrit_get_url,auth=HTTPBasicAuth('RonnyJiang','Cos*142527'))
#     print (r.status_code)
#     print (r.headers)
#     print (r.encoding)
#     print (r.content)

