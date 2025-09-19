#!/usr/bin/env python3
"""
Detailed usage analysis for specific services and components.
Focuses on voice, image analysis, Instagram code, and unused dependencies.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Any

class DetailedUsageAnalyzer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.analysis_results = {}

    def analyze_voice_services_usage(self) -> Dict[str, Any]:
        """Analyze voice services for actual usage patterns."""
        print("Analyzing voice services usage...")

        voice_dir = self.root_path / "services" / "voice"
        voice_files = []
        if voice_dir.exists():
            voice_files = list(voice_dir.rglob("*.py"))

        # Track imports and references to voice services
        voice_imports = defaultdict(list)
        voice_references = defaultdict(list)

        # Search all Python files for voice-related imports and calls
        for py_file in self.root_path.rglob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')

                    # Check for voice imports
                    for i, line in enumerate(lines, 1):
                        if re.search(r'from.*voice|import.*voice', line, re.IGNORECASE):
                            voice_imports[str(py_file.relative_to(self.root_path))].append({
                                'line': i,
                                'content': line.strip()
                            })

                        # Check for voice function calls or references
                        if re.search(r'voice_|livekit|Voice|LiveKit', line, re.IGNORECASE):
                            voice_references[str(py_file.relative_to(self.root_path))].append({
                                'line': i,
                                'content': line.strip()
                            })

                except Exception as e:
                    continue

        return {
            "voice_files": [str(f.relative_to(self.root_path)) for f in voice_files],
            "voice_imports": dict(voice_imports),
            "voice_references": dict(voice_references),
            "total_voice_files": len(voice_files),
            "files_importing_voice": len(voice_imports),
            "files_referencing_voice": len(voice_references)
        }

    def analyze_image_analysis_usage(self) -> Dict[str, Any]:
        """Analyze image analysis services for actual usage patterns."""
        print("Analyzing image analysis services usage...")

        img_dir = self.root_path / "services" / "image_analysis"
        img_files = []
        if img_dir.exists():
            img_files = list(img_dir.rglob("*.py"))

        # Track imports and references to image analysis services
        img_imports = defaultdict(list)
        img_references = defaultdict(list)

        # Search all Python files for image analysis related imports and calls
        for py_file in self.root_path.rglob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')

                    # Check for image analysis imports
                    for i, line in enumerate(lines, 1):
                        if re.search(r'from.*image_analysis|import.*image_analysis', line, re.IGNORECASE):
                            img_imports[str(py_file.relative_to(self.root_path))].append({
                                'line': i,
                                'content': line.strip()
                            })

                        # Check for image analysis function calls or references
                        if re.search(r'image_analysis|property_document_parser|analyze_property_document', line, re.IGNORECASE):
                            img_references[str(py_file.relative_to(self.root_path))].append({
                                'line': i,
                                'content': line.strip()
                            })

                except Exception as e:
                    continue

        return {
            "image_analysis_files": [str(f.relative_to(self.root_path)) for f in img_files],
            "image_analysis_imports": dict(img_imports),
            "image_analysis_references": dict(img_references),
            "total_image_files": len(img_files),
            "files_importing_image_analysis": len(img_imports),
            "files_referencing_image_analysis": len(img_references)
        }

    def analyze_instagram_code(self) -> Dict[str, Any]:
        """Analyze Instagram-related code and usage patterns."""
        print("Analyzing Instagram-related code...")

        instagram_references = defaultdict(list)
        instagram_files = set()

        # Search all Python files for Instagram-related code
        for py_file in self.root_path.rglob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')

                    has_instagram = False
                    for i, line in enumerate(lines, 1):
                        if re.search(r'instagram|meta.*api|ig_|fb_|facebook', line, re.IGNORECASE):
                            instagram_references[str(py_file.relative_to(self.root_path))].append({
                                'line': i,
                                'content': line.strip()
                            })
                            has_instagram = True

                    if has_instagram:
                        instagram_files.add(str(py_file.relative_to(self.root_path)))

                except Exception as e:
                    continue

        return {
            "instagram_files": list(instagram_files),
            "instagram_references": dict(instagram_references),
            "total_files_with_instagram": len(instagram_files),
            "total_instagram_references": sum(len(refs) for refs in instagram_references.values())
        }

    def analyze_medical_remnants(self) -> Dict[str, Any]:
        """Analyze medical/Krishna legacy remnants."""
        print("Analyzing medical/Krishna legacy remnants...")

        medical_references = defaultdict(list)
        medical_files = set()

        medical_keywords = [
            'medical', 'doctor', 'patient', 'diagnosis', 'krishna', 'diagnostic',
            'health', 'clinic', 'hospital', 'prescription', 'medicine'
        ]

        # Search all Python files for medical-related code
        for py_file in self.root_path.rglob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')

                    has_medical = False
                    for i, line in enumerate(lines, 1):
                        for keyword in medical_keywords:
                            if re.search(rf'\b{keyword}\b', line, re.IGNORECASE):
                                medical_references[str(py_file.relative_to(self.root_path))].append({
                                    'line': i,
                                    'content': line.strip(),
                                    'keyword': keyword
                                })
                                has_medical = True

                    if has_medical:
                        medical_files.add(str(py_file.relative_to(self.root_path)))

                except Exception as e:
                    continue

        return {
            "medical_files": list(medical_files),
            "medical_references": dict(medical_references),
            "total_files_with_medical": len(medical_files),
            "total_medical_references": sum(len(refs) for refs in medical_references.values())
        }

    def analyze_package_usage(self) -> Dict[str, Any]:
        """Analyze package usage against requirements.txt."""
        print("Analyzing package usage...")

        # Read requirements.txt
        req_file = self.root_path / "requirements.txt"
        required_packages = []
        if req_file.exists():
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        package = line.split('>=')[0].split('==')[0].split('[')[0]
                        required_packages.append(package)

        # Track actual package imports
        actual_imports = Counter()
        import_locations = defaultdict(list)

        for py_file in self.root_path.rglob("*.py"):
            if py_file.is_file():
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')

                    for i, line in enumerate(lines, 1):
                        # Match import statements
                        import_match = re.match(r'^\s*(?:from\s+(\w+)|import\s+(\w+))', line)
                        if import_match:
                            package = import_match.group(1) or import_match.group(2)
                            if package:
                                actual_imports[package] += 1
                                import_locations[package].append({
                                    'file': str(py_file.relative_to(self.root_path)),
                                    'line': i
                                })

                except Exception as e:
                    continue

        # Find unused packages
        unused_packages = []
        for req_pkg in required_packages:
            # Check if package or its common variants are used
            used = False
            for imported_pkg in actual_imports:
                if (req_pkg.lower() == imported_pkg.lower() or
                    req_pkg.lower().replace('-', '_') == imported_pkg.lower() or
                    imported_pkg.lower().startswith(req_pkg.lower().split('-')[0])):
                    used = True
                    break

            if not used:
                unused_packages.append(req_pkg)

        return {
            "required_packages": required_packages,
            "unused_packages": unused_packages,
            "actual_imports": dict(actual_imports),
            "import_locations": dict(import_locations),
            "total_required": len(required_packages),
            "total_unused": len(unused_packages)
        }

    def generate_removal_safety_report(self) -> Dict[str, Any]:
        """Generate comprehensive removal safety report."""
        print("Generating removal safety report...")

        # Combine all analyses
        voice_analysis = self.analyze_voice_services_usage()
        image_analysis = self.analyze_image_analysis_usage()
        instagram_analysis = self.analyze_instagram_code()
        medical_analysis = self.analyze_medical_remnants()
        package_analysis = self.analyze_package_usage()

        # Determine removal safety
        removal_recommendations = {
            "safe_to_remove": {
                "voice_services": {
                    "safe": voice_analysis['files_importing_voice'] == 0,
                    "reason": f"Voice services imported by {voice_analysis['files_importing_voice']} files",
                    "files": voice_analysis['voice_files']
                },
                "image_analysis": {
                    "safe": image_analysis['files_importing_image_analysis'] <= 1,  # Only the broken import
                    "reason": f"Image analysis imported by {image_analysis['files_importing_image_analysis']} files",
                    "files": image_analysis['image_analysis_files']
                }
            },
            "requires_caution": {
                "instagram_code": {
                    "files_count": len(instagram_analysis['instagram_files']),
                    "references": instagram_analysis['total_instagram_references'],
                    "files": instagram_analysis['instagram_files'][:10]  # First 10 files
                },
                "medical_remnants": {
                    "files_count": len(medical_analysis['medical_files']),
                    "references": medical_analysis['total_medical_references'],
                    "files": medical_analysis['medical_files'][:10]  # First 10 files
                }
            },
            "package_cleanup": {
                "unused_packages": package_analysis['unused_packages'],
                "total_unused": package_analysis['total_unused']
            }
        }

        return {
            "voice_analysis": voice_analysis,
            "image_analysis": image_analysis,
            "instagram_analysis": instagram_analysis,
            "medical_analysis": medical_analysis,
            "package_analysis": package_analysis,
            "removal_recommendations": removal_recommendations
        }

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete detailed analysis."""
        print("Starting detailed usage analysis...")

        results = self.generate_removal_safety_report()

        # Save detailed results
        output_file = self.root_path / "detailed_usage_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nDetailed analysis complete! Results saved to: {output_file}")

        # Print summary
        print("\n=== ANALYSIS SUMMARY ===")
        print(f"Voice Services:")
        print(f"  - Files: {results['voice_analysis']['total_voice_files']}")
        print(f"  - Importing files: {results['voice_analysis']['files_importing_voice']}")
        print(f"  - Safe to remove: {results['removal_recommendations']['safe_to_remove']['voice_services']['safe']}")

        print(f"\nImage Analysis:")
        print(f"  - Files: {results['image_analysis']['total_image_files']}")
        print(f"  - Importing files: {results['image_analysis']['files_importing_image_analysis']}")
        print(f"  - Safe to remove: {results['removal_recommendations']['safe_to_remove']['image_analysis']['safe']}")

        print(f"\nInstagram References:")
        print(f"  - Files with Instagram code: {results['instagram_analysis']['total_files_with_instagram']}")
        print(f"  - Total references: {results['instagram_analysis']['total_instagram_references']}")

        print(f"\nMedical Remnants:")
        print(f"  - Files with medical code: {results['medical_analysis']['total_files_with_medical']}")
        print(f"  - Total references: {results['medical_analysis']['total_medical_references']}")

        print(f"\nPackage Analysis:")
        print(f"  - Required packages: {results['package_analysis']['total_required']}")
        print(f"  - Unused packages: {results['package_analysis']['total_unused']}")
        print(f"  - Unused: {', '.join(results['package_analysis']['unused_packages'][:5])}")

        return results


def main():
    """Main execution function."""
    root_path = "/home/glitch/Projects/Active/centuryproptax"
    analyzer = DetailedUsageAnalyzer(root_path)
    results = analyzer.run_full_analysis()
    return results


if __name__ == "__main__":
    main()