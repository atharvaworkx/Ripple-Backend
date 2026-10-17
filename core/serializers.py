from rest_framework import serializers
from .models import AnalysisReport

class AnalysisReportSummarySerializer(serializers.ModelSerializer):
    findings_count = serializers.SerializerMethodField()
    test_failures_count = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisReport
        fields = [
            'id',
            'mode',
            'repository',
            'pr_title',
            'pr_number',
            'base_ref',
            'head_ref',
            'status',
            'created_at',
            'findings_count',
            'test_failures_count',
            'error_message'
        ]

    def get_findings_count(self, obj):
        return obj.metrics.get('findings_count', len(obj.findings) if obj.findings else 0)

    def get_test_failures_count(self, obj):
        return obj.metrics.get('test_failures_count', 0)

class AnalysisReportDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisReport
        fields = '__all__'

class GitHubAnalysisInputSerializer(serializers.Serializer):
    pr_url = serializers.URLField(required=True)
    github_token = serializers.CharField(required=False, allow_blank=True, default='')
