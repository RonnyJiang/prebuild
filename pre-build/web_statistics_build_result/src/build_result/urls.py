"""web_statistics_build_result URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from build_result.views import buildResult, Commit, buildResultNote, commitNote
 
urlpatterns = [
    url(r'^build_result.html/$', buildResult, name='buildResult'),
    url(r'^commit/(?P<ids>\w*\s*)/$', Commit, name='Commit'),
    url(r'^note_build_result.do', buildResultNote, name='buildResultNote'),
    url(r'^note_commit.do', commitNote, name='commitNote'),
]