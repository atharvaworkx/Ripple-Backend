"""Test selection, test generation, and safe execution engine."""

import ast
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from engine.graph import DependencyGraph

def select_relevant_tests(graph: DependencyGraph, affected_node_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Select existing test functions that target or import affected components.
    """
    selected_tests = []
    seen = set()

    # Find all test nodes
    for nid, node in graph.nodes.items():
        if not node.is_test:
            continue

        # Check if this test has any edge to any affected node
        callees = graph.get_callees(nid)
        targets_affected = []
        for edge in callees:
            if edge.target_id in affected_node_ids:
                targets_affected.append(edge.target_id)

        # Also check file/module convention matching
        if not targets_affected:
            for aff_id in affected_node_ids:
                aff_node = graph.get_node(aff_id)
                if aff_node and (aff_node.name in node.name or aff_node.name.replace("calculate_", "") in node.name):
                    targets_affected.append(aff_id)

        if targets_affected and nid not in seen:
            seen.add(nid)
            selected_tests.append({
                "test_id": nid,
                "name": node.name,
                "file_path": node.file_path,
                "lineno": node.lineno,
                "reason": f"Directly tests affected component: {targets_affected[0]}",
                "inferred": len(callees) == 0
            })

    return selected_tests

def generate_suggested_regression_tests(changed_functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate targeted pytest code suggestions for boundary conditions,
    error cases, and financial precision.
    Validates syntax with ast.parse.
    """
    suggestions = []

    for fn in changed_functions:
        fn_name = fn.get("name", "target_func")
        file_path = fn.get("file_path", "")
        module_path = file_path.replace("/", ".").replace(".py", "")

        test_code = f'''import pytest
from {module_path} import {fn_name}

def test_{fn_name}_boundary_values():
    """Verify behavior on extreme edge inputs (0.0, 1.0, minimum threshold)."""
    # Boundary: Zero discount / neutral operation
    res_zero = {fn_name}(100.0, 0.0)
    assert res_zero == 100.0, f"Expected 100.0 on zero discount, got {{res_zero}}"

def test_{fn_name}_negative_inputs_raise():
    """Ensure invalid negative values raise appropriate ValueError."""
    with pytest.raises(ValueError):
        {fn_name}(-50.0, 0.1)

def test_{fn_name}_floating_point_rounding_invariance():
    """Ensure strict two-decimal half-up rounding precision is preserved."""
    # Financial edge case: 10.05 * 0.95 = 9.5475 -> must round to 9.55
    res = {fn_name}(10.05, 0.05)
    assert res == 9.55, f"Financial rounding discrepancy detected: {{res}} != 9.55"
'''
        # Syntactic validation
        is_valid = True
        syntax_err = None
        try:
            ast.parse(test_code)
        except SyntaxError as e:
            is_valid = False
            syntax_err = str(e)

        suggestions.append({
            "target_function": fn_name,
            "target_file": file_path,
            "title": f"Targeted Regression Suite for {fn_name}()",
            "description": "Tests floating point boundary conditions, invalid inputs, and half-up rounding precision.",
            "code": test_code,
            "syntactically_valid": is_valid,
            "syntax_error": syntax_err
        })

    return suggestions

def execute_trusted_sample_tests(sample_repo_dir: Path) -> List[Dict[str, Any]]:
    """
    Safely executes sample repository tests using pytest in a subprocess.
    Never uses shell=True. Strictly bound with a 15-second timeout.
    """
    test_results = []
    tests_dir = sample_repo_dir / "tests"
    if not tests_dir.exists():
        return test_results

    cmd = [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"]
    start_time = time.time()

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(sample_repo_dir),
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )
        duration = round(time.time() - start_time, 2)
        raw_output = proc.stdout + "\n" + proc.stderr

        # Parse test results from verbose pytest output
        # Lines format: tests/test_pricing.py::test_calculate_discounted_price_standard PASSED
        for line in raw_output.splitlines():
            line_str = line.strip()
            if "::" in line_str and ("PASSED" in line_str or "FAILED" in line_str or "SKIPPED" in line_str):
                parts = line_str.split()
                test_spec = parts[0]
                status_raw = parts[1] if len(parts) > 1 else "UNKNOWN"
                status = "passed" if "PASSED" in status_raw else ("failed" if "FAILED" in status_raw else "skipped")
                
                test_results.append({
                    "test_spec": test_spec,
                    "test_name": test_spec.split("::")[-1] if "::" in test_spec else test_spec,
                    "status": status,
                    "duration": f"{duration}s",
                    "output_snippet": line_str,
                    "failure_details": raw_output if status == "failed" else None
                })

    except subprocess.TimeoutExpired:
        test_results.append({
            "test_spec": "all",
            "test_name": "pytest_timeout",
            "status": "failed",
            "duration": ">15s",
            "output_snippet": "Pytest execution timed out after 15 seconds.",
            "failure_details": "Execution timeout"
        })
    except Exception as e:
        test_results.append({
            "test_spec": "all",
            "test_name": "execution_error",
            "status": "failed",
            "duration": "0s",
            "output_snippet": str(e),
            "failure_details": str(e)
        })

    return test_results
