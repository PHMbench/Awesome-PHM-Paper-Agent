#!/usr/bin/env python3
"""
BibTeX Quality Validation Script
用于验证APPA系统中BibTeX文件的质量标准

Quality Standards:
- Impact Factor ≥ 5.0 (for journal papers)
- Exclude MDPI and other blacklisted publishers
- Verify DOI format (basic check)
- Check for required fields

Usage:
    python scripts/quality_check.py
    python scripts/quality_check.py --strict  # Stricter validation
    python scripts/quality_check.py --report  # Generate detailed report
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Quality standards
MIN_IMPACT_FACTOR = 5.0
BLACKLISTED_PUBLISHERS = [
    'MDPI', 'Hindawi', 'Scientific Research Publishing',
    'OMICS Publishing Group', 'Bentham Science', 'WASET'
]

# High-quality publishers
WHITELIST_PUBLISHERS = [
    'IEEE', 'Elsevier', 'Springer Nature', 'Springer',
    'Wiley', 'Oxford University Press', 'Cambridge University Press',
    'Nature Publishing Group', 'American Chemical Society'
]

# High-quality PHM journals
TOP_TIER_JOURNALS = [
    'Mechanical Systems and Signal Processing',
    'IEEE Transactions on Industrial Electronics',
    'Reliability Engineering & System Safety',
    'Expert Systems with Applications',
    'IEEE Transactions on Industrial Informatics',
    'IEEE Internet of Things Journal'
]

class BibTeXValidator:
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.stats = {
            'total_files': 0,
            'passed_quality': 0,
            'failed_quality': 0,
            'warnings': 0,
            'errors': []
        }
    
    def validate_bibtex_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single BibTeX file."""
        result = {
            'file': file_path.name,
            'status': 'unknown',
            'issues': [],
            'warnings': [],
            'quality_score': 0.0,
            'metadata': {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse basic metadata
            metadata = self._parse_bibtex(content)
            result['metadata'] = metadata
            
            # Quality checks
            quality_score = 0.0
            
            # Check impact factor
            if 'impact_factor' in metadata:
                try:
                    if_value = float(metadata['impact_factor'].replace('{', '').replace('}', ''))
                    if if_value >= MIN_IMPACT_FACTOR:
                        quality_score += 0.4
                    else:
                        result['issues'].append(f"Impact factor {if_value} < {MIN_IMPACT_FACTOR}")
                except:
                    result['warnings'].append("Invalid impact factor format")
            elif not self._is_arxiv_or_conference(metadata):
                result['issues'].append("Missing impact factor for journal paper")
            
            # Check publisher
            publisher = metadata.get('publisher', '').strip('{}')
            journal = metadata.get('journal', '').strip('{}')
            
            if any(bp.lower() in publisher.lower() for bp in BLACKLISTED_PUBLISHERS):
                result['issues'].append(f"Blacklisted publisher: {publisher}")
            elif any(wp.lower() in publisher.lower() for wp in WHITELIST_PUBLISHERS):
                quality_score += 0.3
            elif any(tj.lower() in journal.lower() for tj in TOP_TIER_JOURNALS):
                quality_score += 0.3
            
            # Check DOI format
            doi = metadata.get('doi', '').strip('{}')
            if doi and self._is_valid_doi(doi):
                quality_score += 0.2
            elif not doi and not self._is_arxiv_or_conference(metadata):
                result['warnings'].append("Missing DOI")
            
            # Check required fields
            required_fields = ['title', 'author', 'year']
            for field in required_fields:
                if field not in metadata or not metadata[field].strip('{}'):
                    result['issues'].append(f"Missing required field: {field}")
                else:
                    quality_score += 0.1 / len(required_fields)
            
            result['quality_score'] = quality_score
            
            # Determine status
            if result['issues']:
                result['status'] = 'failed'
                self.stats['failed_quality'] += 1
            elif result['warnings'] and self.strict_mode:
                result['status'] = 'warning'
                self.stats['warnings'] += 1
            else:
                result['status'] = 'passed'
                self.stats['passed_quality'] += 1
                
        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f"Failed to parse file: {e}")
            self.stats['errors'].append(f"{file_path.name}: {e}")
        
        self.stats['total_files'] += 1
        return result
    
    def _parse_bibtex(self, content: str) -> Dict[str, str]:
        """Parse BibTeX content to extract metadata."""
        metadata = {}
        
        # Extract fields using regex
        field_pattern = r'(\w+)\s*=\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        matches = re.findall(field_pattern, content, re.MULTILINE)
        
        for field, value in matches:
            metadata[field.lower()] = value.strip()
        
        return metadata
    
    def _is_valid_doi(self, doi: str) -> bool:
        """Check if DOI format is valid."""
        doi_pattern = r'^10\.\d{4,}\/[-._;()\/:a-zA-Z0-9]+$'
        return re.match(doi_pattern, doi) is not None
    
    def _is_arxiv_or_conference(self, metadata: Dict[str, str]) -> bool:
        """Check if this is an ArXiv preprint or conference paper."""
        journal = metadata.get('journal', '').lower()
        return 'arxiv' in journal or 'conference' in journal or 'proceedings' in journal
    
    def validate_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Validate all BibTeX files in a directory."""
        results = []
        
        for bib_file in directory.glob('*.bib'):
            result = self.validate_bibtex_file(bib_file)
            results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate a quality validation report."""
        report = []
        report.append("🔍 APPA BibTeX Quality Validation Report")
        report.append("=" * 50)
        report.append(f"📊 Total files: {self.stats['total_files']}")
        report.append(f"✅ Passed quality: {self.stats['passed_quality']}")
        report.append(f"⚠️ Warnings: {self.stats['warnings']}")
        report.append(f"❌ Failed quality: {self.stats['failed_quality']}")
        
        if self.stats['errors']:
            report.append(f"🚨 Errors: {len(self.stats['errors'])}")
        
        # Quality summary
        if self.stats['total_files'] > 0:
            pass_rate = (self.stats['passed_quality'] / self.stats['total_files']) * 100
            report.append(f"📈 Quality pass rate: {pass_rate:.1f}%")
        
        report.append("\n" + "=" * 50)
        report.append("📋 Detailed Results:")
        
        # Group by status
        for status in ['failed', 'warning', 'passed']:
            status_results = [r for r in results if r['status'] == status]
            if not status_results:
                continue
            
            status_emoji = {'failed': '❌', 'warning': '⚠️', 'passed': '✅'}[status]
            report.append(f"\n{status_emoji} {status.upper()} ({len(status_results)} files):")
            
            for result in status_results:
                report.append(f"  📄 {result['file']}")
                if result['issues']:
                    for issue in result['issues']:
                        report.append(f"    🔸 {issue}")
                if result['warnings']:
                    for warning in result['warnings']:
                        report.append(f"    ⚠️ {warning}")
                if result['quality_score'] > 0:
                    report.append(f"    📊 Quality score: {result['quality_score']:.2f}")
        
        # Recommendations
        report.append("\n" + "=" * 50)
        report.append("💡 Recommendations:")
        
        if self.stats['failed_quality'] > 0:
            report.append("  🔧 Fix or remove papers that don't meet quality standards")
        if any('Missing DOI' in str(r.get('warnings', [])) for r in results):
            report.append("  🔗 Add DOI information where missing")
        if any('impact factor' in str(r.get('issues', [])) for r in results):
            report.append("  📈 Verify impact factor information")
        
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='Validate BibTeX files in APPA repository')
    parser.add_argument('--directory', '-d', 
                      default='data/bibtex',
                      help='Directory containing BibTeX files')
    parser.add_argument('--strict', action='store_true',
                      help='Enable strict validation mode')
    parser.add_argument('--report', '-r', action='store_true',
                      help='Generate detailed report')
    parser.add_argument('--output', '-o',
                      help='Output file for report')
    
    args = parser.parse_args()
    
    # Find APPA root directory
    script_dir = Path(__file__).parent
    appa_root = script_dir.parent
    bibtex_dir = appa_root / args.directory
    
    if not bibtex_dir.exists():
        print(f"❌ Directory not found: {bibtex_dir}")
        sys.exit(1)
    
    print(f"🔍 Validating BibTeX files in: {bibtex_dir}")
    
    validator = BibTeXValidator(strict_mode=args.strict)
    results = validator.validate_directory(bibtex_dir)
    
    if args.report or args.output:
        report = validator.generate_report(results)
        
        if args.output:
            output_file = Path(args.output)
            output_file.write_text(report, encoding='utf-8')
            print(f"📄 Report saved to: {output_file}")
        else:
            print(report)
    else:
        # Brief summary
        print(f"✅ Quality validation completed:")
        print(f"  📊 {validator.stats['passed_quality']}/{validator.stats['total_files']} files passed")
        if validator.stats['failed_quality'] > 0:
            print(f"  ❌ {validator.stats['failed_quality']} files failed quality standards")
        if validator.stats['warnings'] > 0:
            print(f"  ⚠️ {validator.stats['warnings']} files have warnings")


if __name__ == '__main__':
    main()