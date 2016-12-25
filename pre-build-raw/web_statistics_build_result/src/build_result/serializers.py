from build_result.models import BuildResultTable,CommitTable
from rest_framework import serializers

class BuildResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BuildResultTable
        fields = ('id', 'repo_name', 'issue_id', 'build_time', 'build_result')
        
class CommitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CommitTable
        fields = ('id', 'issue_id', 'gerrit', 'build_result')