# -*- coding: utf-8 -*-
"""
 @Desc:
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: 
 @Software: PyCharm  @since:python 3.5.2(32bit) on 16-12-26.上午11:13
"""

import urllib2
from httptst.Singleton import singleton

__metaclass = type


@singleton
class HttpHelper:
    def __init__(self):
        pass

    name = 'http helper'
    # header
    __reqHeader = {}
    # url
    __reqUrl = ''
    # time
    __reqTimeOut = 0

    # 构建Get请求
    def __buildGetRequest(self):
        if len(self.__reqHeader) == 0:
            request = urllib2.Request(self.__reqUrl)
        else:
            request = urllib2.Request(self.__reqUrl, headers=self.__reqHeader)
        return request

    # 构建post,put,delete请求
    def __buildPostPutDeleteRequest(self, postData):
        if len(self.__reqHeader) == 0:
            request = urllib2.Request(self.__reqUrl, data=postData)
        else:
            request = urllib2.Request(self.__reqUrl, headers=self.__reqHeader, data=postData)
        return request

    # 添加header
    def headers(self, headers):
        self.__reqHeader = headers
        return self

    # 添加url
    def url(self, url):
        print url
        self.__reqUrl = url
        return self

    # 添加超时
    def timeOut(self, time):
        self.__reqTimeOut = time
        return self

    # 是否debug
    def debug(self):
        httpHandler = urllib2.HTTPHandler(debuglevel=1)
        httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
        opener = urllib2.build_opener(httpHandler, httpsHandler)
        urllib2.install_opener(opener)
        return self

    # 处理response
    def __handleResponse(self, request, func):
        try:
            if self.__reqTimeOut == 0:
                res = urllib2.urlopen(request)
            else:
                res = urllib2.urlopen(request, self.__reqTimeOut)
            func(res.read())
        except urllib2.HTTPError, e:
            print e.code

    # get请求
    def get(self, func):
        request = self.__buildGetRequest()
        self.__handleResponse(request, func)

    # post请求
    def post(self, postData, func):
        request = self.__buildPostPutDeleteRequest(postData=postData)
        self.__handleResponse(request, func)

    # put请求
    def put(self, putData, func):
        request = self.__buildPostPutDeleteRequest(postData=putData)
        request.get_method = lambda: 'PUT'
        self.__handleResponse(request, func)

    # delete请求
    def delete(self, putData, func):
        request = self.__buildPostPutDeleteRequest(postData=putData)
        request.get_method = lambda: 'DELETE'
        self.__handleResponse(request, func)


def getData(data):
    print data

httpHelper = HttpHelper()
url_baidu = 'http://www.baidu.com'
#简单的get请求
httpHelper.url(url=url_baidu).get(func=getData)
# post请求
httpHelper.debug() \
     .url(url=url_post_pics) \
     .headers(headers=getHeader()) \
     .post(postData=post_data_pics, func=getData)
# post请求
httpHelper.debug().url(url_post_invite_one).headers(getHeader()).post(post_data_invite_one,getData)
