from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import AnalysisReport
from engine.diff_parser import parse_unified_diff
from engine.ast_parser import PythonFileAnalyzer
from engine.github_client import parse_github_pr_url

class RippleEngineTestCase(TestCase):
    def test_diff_parser_unified_format(self):
        diff_text = """diff --git a/billing/pricing.py b/billing/pricing.py
index a41bc90..78df21b 100644
--- a/billing/pricing.py
+++ b/billing/pricing.py
@@ -20,3 +20,3 @@ def calculate_discounted_price():
-    return round(base_price * (1.0 - discount_rate), 2)
+    discounted = base_price * (1.0 - discount_rate)
+    return math.floor(discounted * 100) / 100.0
"""
        files = parse_unified_diff(diff_text)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["new_path"], "billing/pricing.py")
        self.assertTrue(len(files[0]["changed_lines_new"]) > 0)

    def test_ast_parser_function_and_calls(self):
        sample_code = """
def helper(x):
    return x * 2

def compute():
    val = helper(10)
    return val
"""
        analyzer = PythonFileAnalyzer("test_module.py", sample_code)
        success = analyzer.analyze()
        self.assertTrue(success)
        self.assertEqual(len(analyzer.definitions), 2)
        names = [d.name for d in analyzer.definitions]
        self.assertIn("helper", names)
        self.assertIn("compute", names)
        compute_def = next(d for d in analyzer.definitions if d.name == "compute")
        self.assertEqual(len(compute_def.calls), 1)
        self.assertEqual(compute_def.calls[0]["target_name"], "helper")

    def test_github_url_validator(self):
        valid_url = "https://github.com/psf/requests/pull/1234"
        parsed = parse_github_pr_url(valid_url)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed, ("psf", "requests", 1234))

        invalid_url = "https://evil-site.com/exploit"
        self.assertIsNone(parse_github_pr_url(invalid_url))

class RippleAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")

    def test_run_demo_analysis(self):
        response = self.client.post('/api/analyses/demo/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("findings", response.data)
        self.assertIn("test_results", response.data)
        self.assertIn("metrics", response.data)
        
        # Verify genuine seeded test failure was detected
        self.assertGreater(len(response.data["findings"]), 0)
        self.assertEqual(response.data["metrics"]["test_failures_count"], 1)

        # Verify dashboard updates
        dash_resp = self.client.get('/api/dashboard/')
        self.assertEqual(dash_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(dash_resp.data["metrics"]["total_analyses"], 1)
        self.assertEqual(dash_resp.data["metrics"]["test_failures_detected"], 1)

    def test_github_invalid_url_handling(self):
        response = self.client.post('/api/analyses/github/', {"pr_url": "https://not-github.com/invalid"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("error", response.data)
