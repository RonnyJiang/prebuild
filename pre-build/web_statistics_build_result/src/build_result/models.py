from __future__ import unicode_literals

from django.db import models

# Create your models here.
class BuildResultTable(models.Model):
    repo_name = models.CharField(max_length=200)
    issue_id = models.CharField(max_length=20)
    build_time = models.CharField(max_length=200)
    build_result = models.BooleanField()
    
    class Meta:
        ordering = ('-build_time',)
    
class CommitTable(models.Model):
    issue_id = models.CharField(max_length=20)
    gerrit = models.CharField(max_length=200)
    build_result = models.BooleanField()