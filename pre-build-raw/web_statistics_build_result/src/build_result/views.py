from django.shortcuts import render,render_to_response
from django.template import loader, Context
from django.http import HttpResponse
from build_result.models import BuildResultTable, CommitTable
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import permissions  
from build_result.serializers import BuildResultSerializer, CommitSerializer
import datetime  
import calendar
import json
from web_statistics_build_result.JuncheePaginator import JuncheePaginator
from django.core.paginator import PageNotAnInteger
from django.core.paginator import EmptyPage

#Create your views here.
def handlePage(request, posts_list):
    page_size=20
    try:
        page = int(request.GET.get('page','1'))
        page_size = int(request.GET.get('page_size','20'))
    except ValueError:
        page = 1
        page_size = 20
    
    paginator = JuncheePaginator(posts_list, page_size)
    try:
        posts = paginator.page(page)
    except PageNotAnInteger: 
        posts = paginator.page(1)
    except EmptyPage: 
        posts = paginator.page(paginator.num_pages)    

    end_page = page_size*page
    if len(posts_list) < page_size*page:
        end_page = len(posts_list)
    page_range = "("+str(1+page_size*(page-1)) +"-"+str(end_page)+"/"+str(len(posts_list))+")"
    
    return posts,page_range    

def queryRepo(repo_list, **queryFilter):
    posts_list = []
    for repo_item in list(set(repo_list)):
        projects_list = []
        repo_cursor = BuildResultTable.objects.filter(repo_name=repo_item)
        for build_item in repo_cursor:
            build_time = datetime.datetime.strptime(build_item.build_time, "%Y-%m-%d %H:%M:%S").date()
            while build_time.weekday() != calendar.MONDAY:  
                build_time -= datetime.timedelta(days=1)  
            is_exist = False
            project_map = {}
            for project_item in projects_list:
                if str(build_time) in str(project_item["build_time"]):
                    is_exist = True
                    project_map = project_item
                    projects_list.remove(project_item)
            if is_exist:
                project_map['issue_ids'] = project_map['issue_ids'] + "_" + build_item.issue_id
                if build_item.build_result:
                    project_map['success'] +=1
                    project_map['success_ids'] = project_map['success_ids'] + "_" + build_item.issue_id
                else:
                    project_map['fail'] +=1
                    project_map['fail_ids'] = project_map['fail_ids'] + "_" + build_item.issue_id
            else:
                project_map['issue_ids'] = build_item.issue_id
                if build_item.build_result:
                    project_map['success'] =1
                    project_map['fail'] =0
                    project_map['success_ids'] = build_item.issue_id
                    project_map['fail_ids'] = ''
                else:
                    project_map['success'] =0
                    project_map['fail'] =1
                    project_map['success_ids'] = ''
                    project_map['fail_ids'] = build_item.issue_id
            
            project_map['repo_name'] = build_item.repo_name
            project_map['build_time'] = "%s/%s" %(str(build_time),str(build_time+datetime.timedelta(6))) 
            project_map['total'] = project_map['success'] + project_map['fail']
            projects_list.append(project_map)       
        posts_list.extend(projects_list)
    return posts_list    

def buildResult(request):
    build_result_cursor = BuildResultTable.objects.all()
    repo_list = []
    for build_result_item in build_result_cursor:
        repo_list.append(build_result_item.repo_name)
        
    posts_list = queryRepo(repo_list)
    
    posts,page_range = handlePage(request, posts_list)
    
    post_list = {}
    project_list = []
    for post in posts:
        if post_list.has_key(post['repo_name']):
            project_list.append(post)
            post_list[post['repo_name']] = project_list
        else:
            project_list = []
            project_list.append(post)
            post_list[post['repo_name']] = project_list
    
    t = loader.get_template('build_result_archive.html')
    c = Context({'repo_list':list(set(repo_list)),'post_list': post_list,'posts': posts,'page_range':page_range})
    
    return HttpResponse(t.render(c))
 
def Commit(request, ids):
    id_list = ids.split('_')
    posts_list = []
    for id in id_list:
        commit = CommitTable.objects.filter(issue_id=id)
        posts_list.extend(commit)
    
    posts,page_range = handlePage(request, posts_list)

    post_list = {}
    project_list = []
    for post in posts:
        if post_list.has_key(post.issue_id):
            project_list.append(post)
            post_list[post.issue_id] = project_list
        else:
            project_list = []
            project_list.append(post)
            post_list[post.issue_id] = project_list
        
    t = loader.get_template('commit_archive.html')
    c = Context({'post_list': post_list,'posts': posts,'page_range':page_range})
    return HttpResponse(t.render(c))

def getSearchResult(request):
    if 'repo' in request.GET and 'starttime' in request.GET and 'endtime' in request.GET:
        repo,starttime,endtime = request.GET['repo'],request.GET['starttime'],request.GET['endtime']
        starttime = datetime.datetime.strptime(starttime, "%Y-%m-%d").date()
        while starttime.weekday() != calendar.MONDAY:  
            starttime -= datetime.timedelta(days=1)  
        endtime = datetime.datetime.strptime(endtime, "%Y-%m-%d").date()
        while endtime.weekday() != calendar.SUNDAY:  
            endtime += datetime.timedelta(days=1)      
            
        build_result_cursor = BuildResultTable.objects.all()
        repo_list = []
        if repo == 'ALL':
            for build_result_item in build_result_cursor:
                repo_list.append(build_result_item.repo_name)
        else:
            repo_list.append(repo)   
            
        post_list = {}
        for repo_item in list(set(repo_list)):
            project_list = []
            repo_cursor = BuildResultTable.objects.filter(repo_name=repo_item).filter(build_time__gte=starttime).filter(build_time__lte=endtime)
            for build_item in repo_cursor:
                build_time = datetime.datetime.strptime(build_item.build_time, "%Y-%m-%d %H:%M:%S").date()
                while build_time.weekday() != calendar.MONDAY:  
                    build_time -= datetime.timedelta(days=1)  
                is_exist = False
                project_map = {}
                for project_item in project_list:
                    if str(build_time) in str(project_item["build_time"]):
                        is_exist = True
                        project_map = project_item
                        project_list.remove(project_item)
                if is_exist:
                    project_map['issue_ids'] = project_map['issue_ids'] + "_" + build_item.issue_id
                    if build_item.build_result:
                        project_map['success'] +=1
                        project_map['success_ids'] = project_map['success_ids'] + "_" + build_item.issue_id
                    else:
                        project_map['fail'] +=1
                        project_map['fail_ids'] = project_map['fail_ids'] + "_" + build_item.issue_id
                else:
                    project_map['issue_ids'] = build_item.issue_id
                    if build_item.build_result:
                        project_map['success'] =1
                        project_map['fail'] =0
                        project_map['success_ids'] = build_item.issue_id
                        project_map['fail_ids'] = ''
                    else:
                        project_map['success'] =0
                        project_map['fail'] =1
                        project_map['success_ids'] = ''
                        project_map['fail_ids'] = build_item.issue_id
                
                project_map['repo_name'] = build_item.repo_name
                project_map['build_time'] = "%s/%s" %(str(build_time),str(build_time+datetime.timedelta(6))) 
                project_map['total'] = project_map['success'] + project_map['fail']
                project_list.append(project_map)       
            post_list[repo_item] = project_list
    #     return HttpResponse(json.dumps(post_list))
        t = loader.get_template('search_build_result_archive.html')
        c = Context({'repo_list':list(set(repo_list)),'post_list': post_list})
        return HttpResponse(t.render(c))
    else:
        return render_to_response('search_build_result_archive.html',{'error':True})
        
@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))  
def buildResultNote(request):
    if request.method == 'GET':
        buildresult = BuildResultTable.objects.all()
        serializer = BuildResultSerializer(buildresult, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = BuildResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))  
def commitNote(request):
    if request.method == 'GET':
        commit = CommitTable.objects.all()
        serializer = CommitSerializer(commit, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CommitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        