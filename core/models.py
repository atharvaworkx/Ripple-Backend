import uuid
from django.db import models

class AnalysisReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mode = models.CharField(max_length=20, default='demo')  # 'demo' or 'github'
    repository = models.CharField(max_length=255, default='sample-repo')
    pr_title = models.CharField(max_length=500, blank=True, default='')
    pr_number = models.IntegerField(null=True, blank=True)
    base_ref = models.CharField(max_length=100, default='main')
    head_ref = models.CharField(max_length=100, default='')
    status = models.CharField(max_length=30, default='completed')  # queued, analyzing, completed, failed
    created_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, default='')
    
    # Detailed payloads
    changed_files = models.JSONField(default=list)
    changed_functions = models.JSONField(default=list)
    diff_snippet = models.TextField(blank=True, default='')
    findings = models.JSONField(default=list)
    affected_nodes = models.JSONField(default=dict)
    existing_tests = models.JSONField(default=list)
    suggested_tests = models.JSONField(default=list)
    test_results = models.JSONField(default=list)
    graph = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Analysis {self.id} ({self.mode} - {self.repository} #{self.pr_number})"
