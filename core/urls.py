from django.urls import path
from .views import (
    HealthView,
    DashboardView,
    AnalysisDemoView,
    AnalysisGitHubView,
    AnalysisListView,
    AnalysisDetailView,
    AnalysisFindingsView,
    AnalysisTestsView
)

urlpatterns = [
    path('health/', HealthView.as_view(), name='api-health'),
    path('dashboard/', DashboardView.as_view(), name='api-dashboard'),
    path('analyses/demo/', AnalysisDemoView.as_view(), name='analysis-demo'),
    path('analyses/github/', AnalysisGitHubView.as_view(), name='analysis-github'),
    path('analyses/', AnalysisListView.as_view(), name='analysis-list'),
    path('analyses/<uuid:pk>/', AnalysisDetailView.as_view(), name='analysis-detail'),
    path('analyses/<uuid:pk>/findings/', AnalysisFindingsView.as_view(), name='analysis-findings'),
    path('analyses/<uuid:pk>/tests/', AnalysisTestsView.as_view(), name='analysis-tests'),
]
