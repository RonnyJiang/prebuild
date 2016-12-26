# -*- coding: utf-8 -*-
"""
 @Desc:
 @Author: ronny
 @Contact: set@aliyun.com
 @Site: www.lemon.pub
 @File: 
 @Software: PyCharm  @since:python 3.5.2(32bit) on 16-12-26.上午11:22
"""
import urllib2
import json
import requests
from requests.auth import HTTPDigestAuth


class HttpServer(object):
    def __init__(self):
        pass

    name = 'http server'

    __reqauth=HTTPDigestAuth('ronnyjiang','dbwhhp4E3tjC')
    #header
    __reqHeader = {'content-type': 'application/json'}
    #url
    __reqUrl = ''
    #time
    __reqTimeOut = 0

    #Construction get request
    # def __buildGetRequests(self):
    #     if len(self.__reqHeader) == 0:
    #         request = urllib2.Request(self.__reqUrl)
    #     else:
    #         request = urllib2.Request(self.__reqUrl,headers=self.__reqHeader)
    #     return  request
    def __buildGetRequests(self):
        if len(self.__reqHeader) == 0:
            request = requests.get(self.__reqUrl,auth=self.__reqauth)
        else:
            request = requests.get(self.__reqUrl,headers=self.__reqHeader,auth=self.__reqauth)
        return request
    #Construction post put delete request
    def __buildPostPutDeleteRequest(self,postData):
        if len(self.__reqHeader) == 0:
            request = urllib2.Request(self.__reqUrl,data=postData)
        else:
            request = urllib2.Request(self.__reqUrl,headers=self.__reqHeader,data=postData)
        return request

    #add header
    def headers(self,headers):
        self.__reqHeader = headers
        return self


    #add url
    def url(self,url):
        print (url)
        self.__reqUrl = url
        return self

    #add timeout
    def timeOut(self,time):
        self.__reqTimeOut = time
        return self

    #debug model
    def debug(self):
        httpHandler = urllib2.HTTPHandler(debuglevel=1)
        httpsHandler = urllib2.HTTPSHandler(debuglevel=1)
        opener = urllib2.build_opener(httpHandler,httpsHandler)
        urllib2.install_opener(opener)
        return self

    #handle response
    def __handleResponse(self,request,func):
        try:
            if self.__reqTimeOut == 0:
                res = urllib2.urlopen(request)
            else:
                res = urllib2.urlopen(request,self.__reqTimeOut)
            func(res.read())
        except urllib2.HTTPError, e:
            print e.code

    #get request
    def get(self,func):
        request = self.__buildGetRequests()
        self.__handleResponse(request,func)

    #post request
    def post(self,postData,func):
        request = self.__buildPostPutDeleteRequest(postData)
        self.__handleResponse(request,func)


class JsonServer(object):
    name = 'json server'

    #obj convert json
    def getJson(self,obj):
        data = json.dumps(obj)

    #json str convert dict
    def parse(self,jsonStr):
        jsonDict = json.loads(jsonStr)
        return jsonDict


def getData(data):
    print (data)

def main():
    httpserver = HttpServer()
    url_baidu = 'http://www.baidu.com'
    httpserver.url(url=url_baidu).get(func=getData)



if __name__ == '__main__':
    main()