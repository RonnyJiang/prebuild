from django.contrib import admin
from build_result.models import BuildResultTable, CommitTable

# Register your models here.
class BuildResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'repo_name', 'issue_id', 'build_time', 'build_result')
    search_fields = ('repo_name',)
    
class CommitAdmin(admin.ModelAdmin):
    list_display = ('id', 'issue_id', 'gerrit', 'build_result')
    search_fields = ('issue_id',)
    
admin.site.register(BuildResultTable, BuildResultAdmin)
admin.site.register(CommitTable, CommitAdmin)