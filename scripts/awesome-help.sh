#!/bin/bash

# Awesome PHM Papers - Help and Tool Overview
#
# This script shows available tools and their usage

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🚀 Awesome PHM Papers - Management Tools${NC}"
echo "=================================================================="
echo
echo -e "${CYAN}📋 Available Tools:${NC}"
echo

echo -e "${GREEN}1. awesome-add-paper.sh${NC}"
echo "   📝 Interactively add a new paper to the collection"
echo "   ✅ Built-in quality checks (MDPI filtering, impact factor)"
echo "   🔍 Duplicate detection"
echo "   📊 Automatic metadata generation"
echo "   Usage: ./scripts/awesome-add-paper.sh"
echo

echo -e "${GREEN}2. awesome-update-check.sh${NC}"
echo "   🔍 Search for new papers and check for updates"
echo "   🤖 Uses Claude Code academic-researcher agent when available"
echo "   👤 Requires user confirmation before applying changes"  
echo "   🛡️  Implements quality filtering (IF≥5, excludes MDPI)"
echo "   Usage: ./scripts/awesome-update-check.sh [--dry-run]"
echo

echo -e "${GREEN}3. awesome-validate.sh${NC}"
echo "   ✅ Comprehensive validation of the Awesome list"
echo "   🔧 Checks data integrity, format compliance"
echo "   📊 Quality standard verification"
echo "   🔗 Link validation"
echo "   Usage: ./scripts/awesome-validate.sh"
echo

echo -e "${GREEN}4. daily_greeting.sh${NC}"
echo "   🌅 Daily status overview and recommendations"
echo "   📊 Statistics summary"
echo "   💡 Maintenance suggestions"
echo "   Usage: ./scripts/daily_greeting.sh"
echo

echo -e "${GREEN}5. search_papers.sh${NC}"
echo "   🔍 Search existing papers by various criteria"
echo "   📅 Filter by year, author, topic, keywords"
echo "   📋 Browse complete collection"
echo "   Usage: ./scripts/search_papers.sh --help"
echo

echo -e "${CYAN}🎯 Quick Start Guide:${NC}"
echo "─────────────────────────────────────────────────────────────"
echo -e "1. ${YELLOW}Validate your collection:${NC}"
echo "   ./scripts/awesome-validate.sh"
echo

echo -e "2. ${YELLOW}Check for updates:${NC}"
echo "   ./scripts/awesome-update-check.sh"
echo

echo -e "3. ${YELLOW}Add a new paper:${NC}"
echo "   ./scripts/awesome-add-paper.sh"
echo

echo -e "4. ${YELLOW}Search existing papers:${NC}"
echo "   ./scripts/search_papers.sh --all"
echo

echo -e "5. ${YELLOW}Daily status check:${NC}"
echo "   ./scripts/daily_greeting.sh"
echo

echo -e "${CYAN}🔧 Quality Standards:${NC}"
echo "─────────────────────────────────────────────────────────────"
echo "• 📊 Impact Factor ≥ 5.0 required"
echo "• 🚫 MDPI publishers automatically excluded"  
echo "• ⭐ Q1/Q2 journals preferred"
echo "• 🔍 PHM relevance score ≥ 0.7"
echo "• 📅 Publication year ≥ 2015"
echo "• 👥 Peer review required"
echo

echo -e "${CYAN}📁 Data Structure:${NC}"
echo "─────────────────────────────────────────────────────────────"
echo "data/"
echo "├── papers/           # Complete paper metadata (JSON)"
echo "├── bibtex/           # Citation files (.bib)"
echo "├── abstracts/        # Full abstracts (.txt)"
echo "└── statistics/       # Analytics and trends"
echo

echo -e "${CYAN}🤖 Claude Code Integration:${NC}"
echo "─────────────────────────────────────────────────────────────"
echo "• Use natural language commands with Claude Code"
echo "• Example: \"Search for latest bearing fault diagnosis papers\""
echo "• All updates require user confirmation"
echo "• Academic-researcher agent for paper discovery"
echo "• Quality curation with automated filtering"
echo

echo -e "${CYAN}💡 Tips:${NC}"
echo "─────────────────────────────────────────────────────────────"
echo "• Run validation before and after major changes"
echo "• Use --dry-run flag to preview updates"
echo "• Check daily_greeting.sh for maintenance reminders"
echo "• Configure API keys in config.yaml for full functionality"
echo "• All scripts support --help for detailed usage"
echo

echo -e "${YELLOW}📞 Need Help?${NC}"
echo "─────────────────────────────────────────────────────────────"
echo "• Check individual script help: script-name.sh --help"
echo "• Review README.md for project overview"
echo "• See CLAUDE.md for Claude Code specific instructions"
echo

echo -e "${BLUE}🎉 Happy researching!${NC}"