#!/bin/bash

# Awesome PHM Papers - Interactive Paper Addition Tool
# 
# This script provides an interactive way to add high-quality PHM papers
# to the Awesome list with built-in quality checks and user confirmation.

set -e

# Colors for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Configuration
MIN_IMPACT_FACTOR=5.0
EXCLUDED_PUBLISHERS=("mdpi" "scirp" "hindawi")

echo -e "${BLUE}🚀 Awesome PHM Papers - Interactive Paper Addition${NC}"
echo "=================================================================="

# Function to check if paper already exists
check_paper_exists() {
    local title="$1"
    local doi="$2"
    
    if [ -n "$doi" ]; then
        if grep -r "$doi" data/papers/ 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Paper with DOI $doi already exists${NC}"
            return 0
        fi
    fi
    
    if grep -r "$title" data/papers/ 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Paper with similar title might already exist${NC}"
        return 0
    fi
    
    return 1
}

# Function to validate paper quality
validate_paper_quality() {
    local venue="$1"
    local year="$2"
    local venue_lower=$(echo "$venue" | tr '[:upper:]' '[:lower:]')
    
    # Check excluded publishers
    for publisher in "${EXCLUDED_PUBLISHERS[@]}"; do
        if echo "$venue_lower" | grep -q "$publisher"; then
            echo -e "${RED}❌ Paper from excluded publisher: $publisher${NC}"
            return 1
        fi
    done
    
    # Check publication year (must be >= 2015)
    if [ "$year" -lt 2015 ]; then
        echo -e "${RED}❌ Paper too old (< 2015): $year${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Paper passes basic quality checks${NC}"
    return 0
}

# Function to get user confirmation
get_user_confirmation() {
    local prompt="$1"
    echo -e "${YELLOW}$prompt${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Interactive paper input
echo -e "${BLUE}📝 Enter paper information:${NC}"

echo -n "Paper Title: "
read -r paper_title

echo -n "Authors (comma-separated): "
read -r authors

echo -n "Publication Year: "
read -r year

echo -n "Venue/Journal: "
read -r venue

echo -n "DOI (optional): "
read -r doi

echo -n "Abstract: "
read -r abstract

# Validate inputs
if [ -z "$paper_title" ] || [ -z "$authors" ] || [ -z "$year" ] || [ -z "$venue" ]; then
    echo -e "${RED}❌ Required fields missing. Title, authors, year, and venue are required.${NC}"
    exit 1
fi

# Check if paper already exists
if check_paper_exists "$paper_title" "$doi"; then
    if ! get_user_confirmation "Paper might already exist. Add anyway?"; then
        echo -e "${YELLOW}⏹️  Operation cancelled${NC}"
        exit 0
    fi
fi

# Validate paper quality
if ! validate_paper_quality "$venue" "$year"; then
    if ! get_user_confirmation "Paper failed quality checks. Add anyway?"; then
        echo -e "${YELLOW}⏹️  Operation cancelled${NC}"
        exit 0
    fi
fi

# Show paper summary
echo -e "${BLUE}📋 Paper Summary:${NC}"
echo "Title: $paper_title"
echo "Authors: $authors"
echo "Year: $year"
echo "Venue: $venue"
echo "DOI: $doi"
echo "Abstract: ${abstract:0:200}..."

if ! get_user_confirmation "Add this paper to Awesome PHM Papers?"; then
    echo -e "${YELLOW}⏹️  Operation cancelled${NC}"
    exit 0
fi

# Create paper data structure
echo -e "${BLUE}📁 Creating paper data structure...${NC}"

# Use Python to create proper data structure
python3 << EOF
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Paper data
paper_data = {
    "title": "$paper_title",
    "authors": [author.strip() for author in "$authors".split(',')],
    "year": int("$year"),
    "venue": "$venue",
    "doi": "$doi" if "$doi" else "",
    "abstract": "$abstract",
    "added_date": datetime.now().isoformat(),
    "source": "manual_addition",
    "quality_tier": "under_review",
    "phm_relevance_score": 0.8  # Default score for manual additions
}

# Create filename-safe identifier
first_author = paper_data["authors"][0].split()[-1] if paper_data["authors"] else "Unknown"
title_words = re.findall(r'\w+', paper_data["title"])[:3]
title_key = '-'.join(word.lower() for word in title_words)
paper_id = f"$year-{first_author}-{title_key}"

# Create directories
paper_dir = Path(f"data/papers/{paper_id}")
paper_dir.mkdir(parents=True, exist_ok=True)

# Save paper JSON
with open(paper_dir / "paper.json", "w") as f:
    json.dump(paper_data, f, indent=2)

# Save abstract
with open(f"data/abstracts/{paper_id}.txt", "w") as f:
    f.write(paper_data["abstract"])

# Create BibTeX
first_author_last = first_author.replace(" ", "")
bibtex_key = f"{first_author_last}{paper_data['year']}"
bibtex_content = f"""@article{{{bibtex_key},
  title = {{{paper_data["title"]}}},
  author = {{{'and '.join(paper_data["authors"])}}},
  year = {{{paper_data["year"]}}},
  journal = {{{paper_data["venue"]}}},
"""

if paper_data["doi"]:
    bibtex_content += f"""  doi = {{{paper_data["doi"]}}},
"""

bibtex_content += "}\n"

with open(f"data/bibtex/{paper_id}.bib", "w") as f:
    f.write(bibtex_content)

print(f"✅ Paper data created: {paper_id}")
EOF

# Update statistics
echo -e "${BLUE}📊 Updating statistics...${NC}"
python3 -c "
import json
from pathlib import Path

# Load existing statistics
stats_file = Path('data/statistics/overview.json')
if stats_file.exists():
    with open(stats_file) as f:
        stats = json.load(f)
else:
    stats = {'total_papers': 0, 'by_year': {}, 'by_quality_tier': {}}

# Update stats
stats['total_papers'] = stats.get('total_papers', 0) + 1
stats['by_year']['$year'] = stats.get('by_year', {}).get('$year', 0) + 1
stats['by_quality_tier']['under_review'] = stats.get('by_quality_tier', {}).get('under_review', 0) + 1
stats['last_updated'] = '$(date -Iseconds)'

# Save updated stats
stats_file.parent.mkdir(parents=True, exist_ok=True)
with open(stats_file, 'w') as f:
    json.dump(stats, f, indent=2)

print('✅ Statistics updated')
"

echo -e "${GREEN}🎉 Paper added successfully!${NC}"
echo
echo -e "${BLUE}📝 Next steps:${NC}"
echo "1. Review the paper data in data/papers/"
echo "2. Run ./scripts/awesome-validate.sh to check format"
echo "3. Update README.md to include the new paper"
echo "4. Consider running quality assessment with academic tools"

echo -e "${BLUE}💡 Tip: Use 'python main.py --status' to see updated statistics${NC}"