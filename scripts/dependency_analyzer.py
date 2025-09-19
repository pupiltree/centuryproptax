#!/usr/bin/env python3
"""
Comprehensive dependency analysis script for property tax codebase.
Analyzes imports, usage patterns, and generates removal safety reports.
"""

import ast
import os
import json
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import sys

class DependencyAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.import_graph = defaultdict(set)
        self.usage_map = defaultdict(set)
        self.file_imports = defaultdict(set)
        self.function_definitions = defaultdict(set)
        self.class_definitions = defaultdict(set)
        self.function_calls = defaultdict(set)
        self.package_usage = defaultdict(set)
        self.errors = []

    def analyze_codebase(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of the codebase."""
        print("Starting comprehensive dependency analysis...")

        # Find all Python files
        python_files = list(self.root_path.rglob("*.py"))
        print(f"Found {len(python_files)} Python files")

        # Analyze each file
        for py_file in python_files:
            try:
                self._analyze_file(py_file)
            except Exception as e:
                self.errors.append(f"Error analyzing {py_file}: {str(e)}")

        # Generate analysis results
        results = {
            "import_analysis": self._generate_import_analysis(),
            "usage_analysis": self._generate_usage_analysis(),
            "zero_usage_components": self._identify_zero_usage(),
            "package_analysis": self._analyze_package_usage(),
            "risk_assessment": self._generate_risk_assessment(),
            "errors": self.errors,
            "statistics": self._generate_statistics()
        }

        return results

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file using AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            relative_path = str(file_path.relative_to(self.root_path))

            visitor = ImportUsageVisitor(relative_path, self)
            visitor.visit(tree)

        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {str(e)}")
        except UnicodeDecodeError as e:
            self.errors.append(f"Encoding error in {file_path}: {str(e)}")

    def _generate_import_analysis(self) -> Dict[str, Any]:
        """Generate comprehensive import analysis."""
        return {
            "import_graph": {k: list(v) for k, v in self.import_graph.items()},
            "file_imports": {k: list(v) for k, v in self.file_imports.items()},
            "circular_dependencies": self._detect_circular_dependencies(),
            "import_statistics": self._calculate_import_statistics()
        }

    def _generate_usage_analysis(self) -> Dict[str, Any]:
        """Analyze usage patterns across the codebase."""
        return {
            "function_definitions": {k: list(v) for k, v in self.function_definitions.items()},
            "class_definitions": {k: list(v) for k, v in self.class_definitions.items()},
            "function_calls": {k: list(v) for k, v in self.function_calls.items()},
            "usage_frequency": self._calculate_usage_frequency()
        }

    def _identify_zero_usage(self) -> Dict[str, List[str]]:
        """Identify components with zero usage."""
        zero_usage = {
            "unused_functions": [],
            "unused_classes": [],
            "unused_files": [],
            "unused_directories": []
        }

        # Find unused functions
        all_functions = set()
        for file_path, functions in self.function_definitions.items():
            for func in functions:
                all_functions.add(f"{file_path}::{func}")

        called_functions = set()
        for file_path, calls in self.function_calls.items():
            called_functions.update(calls)

        zero_usage["unused_functions"] = list(all_functions - called_functions)

        # Find unused classes
        all_classes = set()
        for file_path, classes in self.class_definitions.items():
            for cls in classes:
                all_classes.add(f"{file_path}::{cls}")

        # Find files with no external references
        all_files = set(self.file_imports.keys())
        referenced_files = set()
        for imports in self.file_imports.values():
            referenced_files.update(imports)

        zero_usage["unused_files"] = list(all_files - referenced_files)

        return zero_usage

    def _analyze_package_usage(self) -> Dict[str, Any]:
        """Analyze external package usage."""
        return {
            "package_usage": {k: list(v) for k, v in self.package_usage.items()},
            "package_frequency": dict(Counter(
                pkg for packages in self.package_usage.values() for pkg in packages
            ))
        }

    def _generate_risk_assessment(self) -> Dict[str, List[str]]:
        """Generate risk assessment for removal."""
        risk_assessment = {
            "safe_to_remove": [],
            "caution_required": [],
            "critical_preserve": []
        }

        # Critical components to preserve
        critical_patterns = [
            "fastapi", "langchain", "langgraph", "whatsapp", "redis",
            "database", "property_tax", "assessment", "payment"
        ]

        # Voice and image analysis services (likely safe to remove)
        safe_patterns = [
            "voice", "image_analysis", "instagram", "medical", "krishna"
        ]

        for file_path in self.file_imports.keys():
            file_lower = file_path.lower()

            if any(pattern in file_lower for pattern in critical_patterns):
                risk_assessment["critical_preserve"].append(file_path)
            elif any(pattern in file_lower for pattern in safe_patterns):
                risk_assessment["safe_to_remove"].append(file_path)
            else:
                risk_assessment["caution_required"].append(file_path)

        return risk_assessment

    def _detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in import graph."""
        # Simplified cycle detection
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.import_graph.get(node, []):
                dfs(neighbor, path + [node])

            rec_stack.remove(node)

        for node in self.import_graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _calculate_import_statistics(self) -> Dict[str, int]:
        """Calculate import-related statistics."""
        return {
            "total_files": len(self.file_imports),
            "total_imports": sum(len(imports) for imports in self.file_imports.values()),
            "files_with_no_imports": len([f for f, imports in self.file_imports.items() if not imports]),
            "max_imports_per_file": max(len(imports) for imports in self.file_imports.values()) if self.file_imports else 0
        }

    def _calculate_usage_frequency(self) -> Dict[str, int]:
        """Calculate usage frequency for functions and classes."""
        frequency = Counter()

        for calls in self.function_calls.values():
            frequency.update(calls)

        return dict(frequency)

    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate overall statistics."""
        return {
            "total_python_files": len(self.file_imports),
            "total_functions": sum(len(funcs) for funcs in self.function_definitions.values()),
            "total_classes": sum(len(classes) for classes in self.class_definitions.values()),
            "total_imports": sum(len(imports) for imports in self.file_imports.values()),
            "analysis_errors": len(self.errors)
        }


class ImportUsageVisitor(ast.NodeVisitor):
    """AST visitor to collect import and usage information."""

    def __init__(self, file_path: str, analyzer: DependencyAnalyzer):
        self.file_path = file_path
        self.analyzer = analyzer
        self.current_class = None

    def visit_Import(self, node):
        """Handle 'import module' statements."""
        for alias in node.names:
            module_name = alias.name
            self.analyzer.file_imports[self.file_path].add(module_name)
            self.analyzer.import_graph[self.file_path].add(module_name)

            # Track package usage
            root_package = module_name.split('.')[0]
            self.analyzer.package_usage[self.file_path].add(root_package)

        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Handle 'from module import name' statements."""
        if node.module:
            module_name = node.module
            self.analyzer.file_imports[self.file_path].add(module_name)
            self.analyzer.import_graph[self.file_path].add(module_name)

            # Track package usage
            root_package = module_name.split('.')[0]
            self.analyzer.package_usage[self.file_path].add(root_package)

        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Handle function definitions."""
        func_name = node.name
        if self.current_class:
            full_name = f"{self.current_class}.{func_name}"
        else:
            full_name = func_name

        self.analyzer.function_definitions[self.file_path].add(full_name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Handle async function definitions."""
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        """Handle class definitions."""
        class_name = node.name
        self.analyzer.class_definitions[self.file_path].add(class_name)

        old_class = self.current_class
        self.current_class = class_name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node):
        """Handle function calls."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            self.analyzer.function_calls[self.file_path].add(func_name)
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            self.analyzer.function_calls[self.file_path].add(attr_name)

        self.generic_visit(node)


def main():
    """Main execution function."""
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = "/home/glitch/Projects/Active/centuryproptax"

    analyzer = DependencyAnalyzer(root_path)
    results = analyzer.analyze_codebase()

    # Save results to JSON file
    output_file = os.path.join(root_path, "dependency_analysis_report.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nAnalysis complete! Results saved to: {output_file}")
    print(f"Total files analyzed: {results['statistics']['total_python_files']}")
    print(f"Total functions found: {results['statistics']['total_functions']}")
    print(f"Total classes found: {results['statistics']['total_classes']}")
    print(f"Analysis errors: {results['statistics']['analysis_errors']}")

    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")

    return results


if __name__ == "__main__":
    main()