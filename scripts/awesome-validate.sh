#!/bin/bash

# Awesome PHM Papers - Validation Tool
#
# This script validates the Awesome list format, data integrity,
# and ensures all papers meet quality standards.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}✅ Awesome PHM Papers - Validation Tool${NC}"
echo "=================================================================="

# Validation counters
TOTAL_ERRORS=0
TOTAL_WARNINGS=0
TOTAL_PAPERS=0

# Function to log error
log_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((TOTAL_ERRORS++))
}

# Function to log warning
log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((TOTAL_WARNINGS++))
}

# Function to log success
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to log info
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Validate project structure
validate_structure() {
    log_info "Validating project structure..."
    
    local required_dirs=(
        "data"
        "data/papers"
        "data/bibtex"  
        "data/abstracts"
        "data/statistics"
        "scripts"
    )
    
    local required_files=(
        "README.md"
        "data/statistics/overview.json"
    )
    
    # Check directories
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_success "Directory exists: $dir"
        else
            log_error "Missing directory: $dir"
        fi
    done
    
    # Check files
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "File exists: $file"
        else
            log_error "Missing file: $file"
        fi
    done
}

# Validate README format
validate_readme() {
    log_info "Validating README.md format..."
    
    if [ ! -f "README.md" ]; then
        log_error "README.md not found"
        return
    fi
    
    # Check for required sections
    local required_sections=(
        "# Awesome PHM Papers"
        "## Contents"
        "## Quality Standards"  
        "## Contributing"
        "## Statistics"
    )
    
    for section in "${required_sections[@]}"; do
        if grep -q "$section" README.md; then
            log_success "README section found: $section"
        else
            log_warning "README section missing or malformed: $section"
        fi
    done
    
    # Check for Awesome badge
    if grep -q "awesome.re/badge.svg" README.md; then
        log_success "Awesome badge found in README"
    else
        log_warning "Awesome badge missing from README"
    fi
    
    # Check for quality indicators
    if grep -q "Papers" README.md && grep -q "Quality" README.md; then
        log_success "Quality indicators found in README badges"
    else
        log_warning "Quality indicator badges missing from README"
    fi
}

# Validate data consistency
validate_data_consistency() {
    log_info "Validating data consistency..."
    
    if [ ! -d "data/papers" ]; then
        log_error "data/papers directory not found"
        return
    fi
    
    # Count papers in different locations
    paper_json_count=$(find data/papers -name "*.json" | wc -l)
    bibtex_count=$(find data/bibtex -name "*.bib" 2>/dev/null | wc -l)
    abstract_count=$(find data/abstracts -name "*.txt" 2>/dev/null | wc -l)
    
    log_info "Paper JSON files: $paper_json_count"
    log_info "BibTeX files: $bibtex_count"  
    log_info "Abstract files: $abstract_count"
    
    TOTAL_PAPERS=$paper_json_count
    
    # Check consistency
    if [ "$paper_json_count" -eq "$bibtex_count" ]; then
        log_success "Paper and BibTeX counts match"
    else
        log_warning "Mismatch between paper JSONs ($paper_json_count) and BibTeX files ($bibtex_count)"
    fi
    
    if [ "$paper_json_count" -eq "$abstract_count" ]; then
        log_success "Paper and abstract counts match"
    else
        log_warning "Mismatch between paper JSONs ($paper_json_count) and abstract files ($abstract_count)"
    fi
}

# Validate individual papers
validate_papers() {
    log_info "Validating individual papers..."
    
    if [ ! -d "data/papers" ]; then
        return
    fi
    
    local paper_count=0
    local valid_papers=0
    
    # Python script for paper validation
    python3 << 'EOF'
import json
import os
from pathlib import Path

def validate_paper_json(paper_file):
    """Validate individual paper JSON file"""
    errors = []
    warnings = []
    
    try:
        with open(paper_file) as f:
            paper = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"], []
    
    # Required fields
    required_fields = ['title', 'authors', 'year', 'venue']
    for field in required_fields:
        if field not in paper or not paper[field]:
            errors.append(f"Missing or empty required field: {field}")
    
    # Validate data types
    if 'year' in paper and not isinstance(paper['year'], int):
        errors.append("Year must be an integer")
    
    if 'authors' in paper and not isinstance(paper['authors'], list):
        errors.append("Authors must be a list")
    
    # Check for reasonable year range
    if 'year' in paper and isinstance(paper['year'], int):
        current_year = 2025  # Update as needed
        if paper['year'] < 2000 or paper['year'] > current_year:
            warnings.append(f"Unusual year: {paper['year']}")
    
    # Check for empty title or too short
    if 'title' in paper and len(paper.get('title', '')) < 10:
        errors.append("Title too short (< 10 characters)")
    
    # Check for abstract presence
    if not paper.get('abstract'):
        warnings.append("Missing abstract")
    
    # Check for DOI format if present
    if paper.get('doi') and not (paper['doi'].startswith('10.') or 'doi.org' in paper['doi']):
        warnings.append("DOI format might be incorrect")
    
    return errors, warnings

# Process all paper files
total_papers = 0
valid_papers = 0
total_errors = 0
total_warnings = 0

for paper_file in Path('data/papers').rglob('*.json'):
    total_papers += 1
    errors, warnings = validate_paper_json(paper_file)
    
    if errors:
        print(f"❌ {paper_file}: {len(errors)} error(s)")
        for error in errors:
            print(f"   • {error}")
        total_errors += len(errors)
    else:
        valid_papers += 1
        print(f"✅ {paper_file}: Valid")
    
    if warnings:
        print(f"⚠️  {paper_file}: {len(warnings)} warning(s)")
        for warning in warnings:
            print(f"   • {warning}")
        total_warnings += len(warnings)

print(f"\n📊 Paper Validation Summary:")
print(f"   Total papers: {total_papers}")
print(f"   Valid papers: {valid_papers}")  
print(f"   Papers with errors: {total_papers - valid_papers}")
print(f"   Total errors: {total_errors}")
print(f"   Total warnings: {total_warnings}")
EOF
}

# Validate quality standards
validate_quality() {
    log_info "Validating quality standards..."
    
    if [ ! -f "data/statistics/overview.json" ]; then
        log_warning "Statistics file not found, skipping quality validation"
        return
    fi
    
    python3 << 'EOF'
import json

try:
    with open('data/statistics/overview.json') as f:
        stats = json.load(f)
    
    total_papers = stats.get('total_papers', 0)
    quality_tiers = stats.get('by_quality_tier', {})
    
    print(f"📊 Quality Distribution:")
    for tier, count in quality_tiers.items():
        percentage = (count / total_papers * 100) if total_papers > 0 else 0
        print(f"   {tier}: {count} papers ({percentage:.1f}%)")
    
    # Check for reasonable quality distribution
    high_quality = quality_tiers.get('top_tier', 0) + quality_tiers.get('excellent', 0)
    if total_papers > 0:
        high_quality_ratio = high_quality / total_papers
        if high_quality_ratio < 0.3:
            print("⚠️  WARNING: Low ratio of high-quality papers")
        else:
            print("✅ Good ratio of high-quality papers")
    
    # Check average impact factor
    avg_if = stats.get('quality_metrics', {}).get('average_impact_factor', 0)
    if avg_if >= 5.0:
        print(f"✅ Average impact factor meets standards: {avg_if}")
    else:
        print(f"⚠️  WARNING: Average impact factor below standards: {avg_if}")

except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"❌ Error reading statistics: {e}")
EOF
}

# Validate links and references
validate_links() {
    log_info "Validating links and references..."
    
    if [ ! -f "README.md" ]; then
        return
    fi
    
    # Check for broken internal links
    local broken_links=0
    
    # Extract markdown links from README
    grep -o '\[.*\]([^)]*\.md)' README.md | while IFS= read -r link; do
        # Extract the path from the link
        path=$(echo "$link" | sed 's/.*(\([^)]*\)).*/\1/')
        
        # Resolve relative paths
        if [[ "$path" == ../data/* ]]; then
            full_path="${path#../}"
        else
            full_path="$path"
        fi
        
        if [ ! -f "$full_path" ]; then
            log_warning "Broken internal link: $path"
            ((broken_links++))
        fi
    done
    
    if [ "$broken_links" -eq 0 ]; then
        log_success "All internal links are valid"
    fi
}

# Generate validation report
generate_report() {
    echo
    echo -e "${BLUE}📋 Validation Report${NC}"
    echo "=============================="
    echo "Total papers validated: $TOTAL_PAPERS"
    echo "Total errors found: $TOTAL_ERRORS"  
    echo "Total warnings: $TOTAL_WARNINGS"
    echo
    
    if [ "$TOTAL_ERRORS" -eq 0 ] && [ "$TOTAL_WARNINGS" -eq 0 ]; then
        echo -e "${GREEN}🎉 All validations passed! Your Awesome list is in excellent shape.${NC}"
        exit 0
    elif [ "$TOTAL_ERRORS" -eq 0 ]; then
        echo -e "${YELLOW}✅ No errors found, but there are $TOTAL_WARNINGS warning(s) to review.${NC}"
        exit 0
    else
        echo -e "${RED}❌ Found $TOTAL_ERRORS error(s) that need to be fixed.${NC}"
        exit 1
    fi
}

# Main validation flow
main() {
    validate_structure
    validate_readme
    validate_data_consistency  
    validate_papers
    validate_quality
    validate_links
    generate_report
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help] [--fix-minor]"
        echo "  --help        Show this help message"
        echo "  --fix-minor   Automatically fix minor issues (not implemented yet)"
        exit 0
        ;;
    --fix-minor)
        echo -e "${BLUE}🔧 Minor fixes enabled (coming soon)${NC}"
        ;;
esac

# Run main validation
main