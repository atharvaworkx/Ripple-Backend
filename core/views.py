from pathlib import Path
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AnalysisReport
from .serializers import (
    AnalysisReportSummarySerializer,
    AnalysisReportDetailSerializer,
    GitHubAnalysisInputSerializer
)
from engine.pipeline import run_sample_demo_analysis, run_github_pr_analysis

class HealthView(APIView):
    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "Ripple Impact Analysis Platform",
            "version": "1.0.0",
            "engine": "Python AST & Adjacency Graph",
            "database": "SQLite / Django ORM"
        }, status=status.HTTP_200_OK)

class DashboardView(APIView):
    def get(self, request):
        total_analyses = AnalysisReport.objects.count()
        recent = AnalysisReport.objects.all()[:5]

        # Calculate metrics from stored real data
        total_failures = 0
        total_findings = 0
        for r in AnalysisReport.objects.all():
            total_failures += r.metrics.get('test_failures_count', 0)
            total_findings += r.metrics.get('findings_count', len(r.findings) if r.findings else 0)

        return Response({
            "metrics": {
                "total_analyses": total_analyses,
                "test_failures_detected": total_failures,
                "unresolved_impact_findings": total_findings,
            },
            "recent_analyses": AnalysisReportSummarySerializer(recent, many=True).data
        }, status=status.HTTP_200_OK)

class AnalysisDemoView(APIView):
    def post(self, request):
        base_dir = Path(settings.BASE_DIR)
        report_data = run_sample_demo_analysis(base_dir)

        # Persist to database
        report = AnalysisReport.objects.create(
            mode=report_data.get("mode", "demo"),
            repository=report_data.get("repository", "sample-repo"),
            pr_title=report_data.get("pr_title", ""),
            pr_number=report_data.get("pr_number"),
            base_ref=report_data.get("base_ref", "main"),
            head_ref=report_data.get("head_ref", ""),
            status=report_data.get("status", "completed"),
            changed_files=report_data.get("changed_files", []),
            changed_functions=report_data.get("changed_functions", []),
            diff_snippet=report_data.get("diff_snippet", ""),
            findings=report_data.get("findings", []),
            affected_nodes=report_data.get("affected_nodes", {}),
            existing_tests=report_data.get("existing_tests", []),
            suggested_tests=report_data.get("suggested_tests", []),
            test_results=report_data.get("test_results", []),
            graph=report_data.get("graph", {}),
            metrics=report_data.get("metrics", {})
        )

        serializer = AnalysisReportDetailSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AnalysisGitHubView(APIView):
    def post(self, request):
        input_serializer = GitHubAnalysisInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pr_url = input_serializer.validated_data["pr_url"]
        token = input_serializer.validated_data.get("github_token")

        report_data = run_github_pr_analysis(pr_url, token=token)

        if report_data.get("status") == "failed":
            # Record failed analysis attempt
            report = AnalysisReport.objects.create(
                mode="github",
                repository=pr_url,
                status="failed",
                error_message=report_data.get("error", "Analysis failed"),
                metrics={"findings_count": 0, "test_failures_count": 0}
            )
            return Response({
                "id": str(report.id),
                "status": "failed",
                "error": report_data.get("error", "Analysis failed")
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        report = AnalysisReport.objects.create(
            mode="github",
            repository=report_data.get("repository", ""),
            pr_title=report_data.get("pr_title", ""),
            pr_number=report_data.get("pr_number"),
            base_ref=report_data.get("base_ref", "main"),
            head_ref=report_data.get("head_ref", ""),
            status="completed",
            changed_files=report_data.get("changed_files", []),
            changed_functions=report_data.get("changed_functions", []),
            diff_snippet=report_data.get("diff_snippet", ""),
            findings=report_data.get("findings", []),
            affected_nodes=report_data.get("affected_nodes", {}),
            existing_tests=report_data.get("existing_tests", []),
            suggested_tests=report_data.get("suggested_tests", []),
            test_results=report_data.get("test_results", []),
            graph=report_data.get("graph", {}),
            metrics=report_data.get("metrics", {})
        )

        serializer = AnalysisReportDetailSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AnalysisListView(APIView):
    def get(self, request):
        reports = AnalysisReport.objects.all()
        serializer = AnalysisReportSummarySerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AnalysisDetailView(APIView):
    def get(self, request, pk):
        try:
            report = AnalysisReport.objects.get(pk=pk)
            return Response(AnalysisReportDetailSerializer(report).data, status=status.HTTP_200_OK)
        except AnalysisReport.DoesNotExist:
            return Response({"error": "Analysis report not found"}, status=status.HTTP_404_NOT_FOUND)

class AnalysisFindingsView(APIView):
    def get(self, request, pk):
        try:
            report = AnalysisReport.objects.get(pk=pk)
            findings = report.findings or []
            
            # Optional query filters
            severity = request.query_params.get("severity")
            category = request.query_params.get("category")
            if severity:
                findings = [f for f in findings if f.get("severity", "").upper() == severity.upper()]
            if category:
                findings = [f for f in findings if f.get("category", "").lower() == category.lower()]

            return Response(findings, status=status.HTTP_200_OK)
        except AnalysisReport.DoesNotExist:
            return Response({"error": "Analysis report not found"}, status=status.HTTP_404_NOT_FOUND)

class AnalysisTestsView(APIView):
    def get(self, request, pk):
        try:
            report = AnalysisReport.objects.get(pk=pk)
            return Response({
                "existing_tests": report.existing_tests,
                "suggested_tests": report.suggested_tests,
                "test_results": report.test_results
            }, status=status.HTTP_200_OK)
        except AnalysisReport.DoesNotExist:
            return Response({"error": "Analysis report not found"}, status=status.HTTP_404_NOT_FOUND)
