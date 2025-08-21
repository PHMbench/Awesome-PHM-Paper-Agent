"""
Cross-Reference Linking Agent for APPA system.

This agent implements bidirectional navigation and link validation.

Single Responsibility: Implement bidirectional navigation and link validation
Input: Complete paper database and file system structure
Output: Fully cross-referenced knowledge base with verified links
"""

import os
import re
from typing import List, Dict, Any, Set, Tuple
from urllib.parse import urlparse
import requests
from datetime import datetime

from .base_agent import BaseAgent, AgentError


class CrossReferenceLinkingAgent(BaseAgent):
    """
    Agent responsible for creating and validating cross-references throughout the knowledge base.
    
    Implements bidirectional WikiLinks and validates all internal and external links.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "CrossReferenceLinkingAgent")
        
        # Base directories
        self.base_dir = os.getcwd()
        self.papers_dir = os.path.join(self.base_dir, 'papers')
        self.topics_dir = os.path.join(self.base_dir, 'topics')
        self.venues_dir = os.path.join(self.base_dir, 'venues')
        self.authors_dir = os.path.join(self.base_dir, 'authors')
        self.indices_dir = os.path.join(self.base_dir, 'indices')
        
        # Link tracking
        self.internal_links: Set[str] = set()
        self.external_links: Set[str] = set()
        self.broken_links: List[Dict[str, str]] = []
        
        # Session for link validation
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'APPA/1.0 Link Validator'})
        
        self.logger.info("Initialized Cross-Reference Linking Agent")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create cross-references and validate links.
        
        Args:
            input_data: Dictionary containing:
                - papers: List of paper data
                - file_structure: Current file system structure
        
        Returns:
            Dictionary with linking results and validation statistics
        """
        papers = input_data.get('papers', [])
        
        if not papers:
            raise AgentError("No papers provided for cross-reference linking")
        
        self.logger.info(f"Starting cross-reference linking for {len(papers)} papers")
        
        linking_stats = {
            'total_papers': len(papers),
            'internal_links_created': 0,
            'external_links_validated': 0,
            'broken_links_found': 0,
            'bidirectional_links': 0,
            'cross_references_updated': 0
        }
        
        # Build paper database for cross-referencing
        paper_db = self._build_paper_database(papers)
        
        # Create bidirectional links
        self._create_bidirectional_links(paper_db)
        linking_stats['bidirectional_links'] = len(self.internal_links)
        
        # Update cross-references in all files
        self._update_cross_references(paper_db)
        linking_stats['cross_references_updated'] = self._count_updated_files()
        
        # Validate all links
        validation_results = self._validate_all_links()
        linking_stats.update(validation_results)
        
        # Generate link report
        self._generate_link_report(linking_stats)
        
        self.logger.info(f"Cross-reference linking completed: {linking_stats['bidirectional_links']} links created")
        
        return linking_stats
    
    def _build_paper_database(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build comprehensive paper database for cross-referencing."""
        paper_db = {
            'papers': {},
            'authors': {},
            'venues': {},
            'topics': {},
            'years': {},
            'citations': {}
        }
        
        for paper in papers:
            paper_id = self._generate_paper_id(paper)
            paper_db['papers'][paper_id] = paper
            
            # Index by authors
            for author in paper.get('authors', []):
                if author not in paper_db['authors']:
                    paper_db['authors'][author] = []
                paper_db['authors'][author].append(paper_id)
            
            # Index by venue
            venue = paper.get('venue', '')
            if venue:
                if venue not in paper_db['venues']:
                    paper_db['venues'][venue] = []
                paper_db['venues'][venue].append(paper_id)
            
            # Index by topics
            analysis = paper.get('analysis', {})
            topics = analysis.get('extracted_topics', [])
            for topic in topics:
                if topic not in paper_db['topics']:
                    paper_db['topics'][topic] = []
                paper_db['topics'][topic].append(paper_id)
            
            # Index by year
            year = paper.get('year', 0)
            if year:
                if year not in paper_db['years']:
                    paper_db['years'][year] = []
                paper_db['years'][year].append(paper_id)
            
            # Index by citation count
            citation_count = paper.get('citation_count', 0)
            paper_db['citations'][paper_id] = citation_count
        
        return paper_db
    
    def _generate_paper_id(self, paper: Dict[str, Any]) -> str:
        """Generate unique identifier for paper."""
        year = paper.get('year', 0)
        first_author = 'Unknown'
        authors = paper.get('authors', [])
        if authors:
            first_author_full = authors[0]
            if ',' in first_author_full:
                first_author = first_author_full.split(',')[0].strip()
            else:
                parts = first_author_full.split()
                first_author = parts[-1] if parts else 'Unknown'
        
        title_words = paper.get('title', '').split()[:3]
        title_short = ''.join(word.capitalize() for word in title_words)
        
        return f"{year}-{first_author}-{title_short}"
    
    def _create_bidirectional_links(self, paper_db: Dict[str, Any]) -> None:
        """Create bidirectional WikiLinks between related papers."""
        papers = paper_db['papers']
        
        for paper_id, paper in papers.items():
            # Find related papers
            related_papers = self._find_related_papers(paper_id, paper, paper_db)
            
            # Create links to related papers
            for related_id in related_papers:
                self._add_bidirectional_link(paper_id, related_id)
    
    def _find_related_papers(self, paper_id: str, paper: Dict[str, Any], paper_db: Dict[str, Any]) -> List[str]:
        """Find papers related to the given paper."""
        related = set()
        
        # Same authors
        for author in paper.get('authors', []):
            if author in paper_db['authors']:
                for related_id in paper_db['authors'][author]:
                    if related_id != paper_id:
                        related.add(related_id)
        
        # Same venue
        venue = paper.get('venue', '')
        if venue and venue in paper_db['venues']:
            for related_id in paper_db['venues'][venue]:
                if related_id != paper_id:
                    related.add(related_id)
        
        # Same topics
        analysis = paper.get('analysis', {})
        topics = analysis.get('extracted_topics', [])
        for topic in topics:
            if topic in paper_db['topics']:
                for related_id in paper_db['topics'][topic]:
                    if related_id != paper_id:
                        related.add(related_id)
        
        # Same year (limit to avoid too many links)
        year = paper.get('year', 0)
        if year and year in paper_db['years']:
            year_papers = paper_db['years'][year]
            if len(year_papers) <= 10:  # Only link if not too many papers in same year
                for related_id in year_papers:
                    if related_id != paper_id:
                        related.add(related_id)
        
        return list(related)[:10]  # Limit to 10 related papers
    
    def _add_bidirectional_link(self, paper_id1: str, paper_id2: str) -> None:
        """Add bidirectional link between two papers."""
        link1 = f"{paper_id1} -> {paper_id2}"
        link2 = f"{paper_id2} -> {paper_id1}"
        
        self.internal_links.add(link1)
        self.internal_links.add(link2)
    
    def _update_cross_references(self, paper_db: Dict[str, Any]) -> None:
        """Update cross-references in all markdown files."""
        # Update paper files
        self._update_paper_cross_references(paper_db)
        
        # Update topic files
        self._update_topic_cross_references(paper_db)
        
        # Update venue files
        self._update_venue_cross_references(paper_db)
        
        # Update author files
        self._update_author_cross_references(paper_db)
        
        # Update index files
        self._update_index_cross_references(paper_db)
    
    def _update_paper_cross_references(self, paper_db: Dict[str, Any]) -> None:
        """Update cross-references in paper files."""
        for paper_id, paper in paper_db['papers'].items():
            year = paper.get('year', 0)
            folder_name = self._generate_folder_name(paper)
            paper_file = os.path.join(self.papers_dir, str(year), folder_name, 'index.md')
            
            if os.path.exists(paper_file):
                self._add_related_papers_section(paper_file, paper_id, paper_db)
    
    def _add_related_papers_section(self, paper_file: str, paper_id: str, paper_db: Dict[str, Any]) -> None:
        """Add related papers section to paper file."""
        with open(paper_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find related papers
        paper = paper_db['papers'][paper_id]
        related_papers = self._find_related_papers(paper_id, paper, paper_db)
        
        if related_papers:
            # Create related papers section
            related_section = "\n## Related Papers\n\n"
            
            for related_id in related_papers[:5]:  # Limit to 5 related papers
                related_paper = paper_db['papers'][related_id]
                related_year = related_paper.get('year', 0)
                related_folder = self._generate_folder_name(related_paper)
                related_title = related_paper.get('title', 'Unknown')
                
                # Create relative path
                relative_path = f"../../{related_year}/{related_folder}/index.md"
                related_section += f"- [[{relative_path}|{related_title}]]\n"
            
            # Insert before navigation section
            if "## Navigation" in content:
                content = content.replace("## Navigation", related_section + "## Navigation")
            else:
                content += related_section
            
            # Write back to file
            with open(paper_file, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _generate_folder_name(self, paper: Dict[str, Any]) -> str:
        """Generate folder name for paper (simplified version)."""
        year = paper.get('year', 0)
        venue = paper.get('venue', 'Unknown')
        authors = paper.get('authors', [])
        title = paper.get('title', 'Unknown')
        
        # Simplified folder name generation
        first_author = 'Unknown'
        if authors:
            first_author_full = authors[0]
            if ',' in first_author_full:
                first_author = first_author_full.split(',')[0].strip()
            else:
                parts = first_author_full.split()
                first_author = parts[-1] if parts else 'Unknown'
        
        # Create short title
        title_words = title.split()[:3]
        short_title = ''.join(word.capitalize() for word in title_words)
        
        # Sanitize
        folder_name = f"{year}-{venue[:10]}-{first_author}-{short_title}"
        folder_name = re.sub(r'[<>:"/\\|?*\s]', '-', folder_name)
        
        return folder_name[:80]  # Limit length
    
    def _update_topic_cross_references(self, paper_db: Dict[str, Any]) -> None:
        """Update cross-references in topic files."""
        # Implementation for topic cross-references
        pass
    
    def _update_venue_cross_references(self, paper_db: Dict[str, Any]) -> None:
        """Update cross-references in venue files."""
        # Implementation for venue cross-references
        pass
    
    def _update_author_cross_references(self, paper_db: Dict[str, Any]) -> None:
        """Update cross-references in author files."""
        # Implementation for author cross-references
        pass
    
    def _update_index_cross_references(self, paper_db: Dict[str, Any]) -> None:
        """Update cross-references in index files."""
        # Implementation for index cross-references
        pass
    
    def _validate_all_links(self) -> Dict[str, int]:
        """Validate all internal and external links."""
        validation_stats = {
            'internal_links_validated': 0,
            'external_links_validated': 0,
            'broken_links_found': 0
        }
        
        # Validate internal links
        internal_valid, internal_broken = self._validate_internal_links()
        validation_stats['internal_links_validated'] = internal_valid
        validation_stats['broken_links_found'] += internal_broken
        
        # Validate external links
        external_valid, external_broken = self._validate_external_links()
        validation_stats['external_links_validated'] = external_valid
        validation_stats['broken_links_found'] += external_broken
        
        return validation_stats
    
    def _validate_internal_links(self) -> Tuple[int, int]:
        """Validate internal WikiLinks."""
        valid_count = 0
        broken_count = 0
        
        # Find all markdown files
        markdown_files = self._find_all_markdown_files()
        
        for file_path in markdown_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find WikiLinks
            wiki_links = re.findall(r'\[\[([^\]]+)\]\]', content)
            
            for link in wiki_links:
                # Extract path (before |)
                link_path = link.split('|')[0]
                
                # Resolve relative path
                file_dir = os.path.dirname(file_path)
                target_path = os.path.normpath(os.path.join(file_dir, link_path))
                
                if os.path.exists(target_path):
                    valid_count += 1
                else:
                    broken_count += 1
                    self.broken_links.append({
                        'file': file_path,
                        'link': link,
                        'type': 'internal'
                    })
        
        return valid_count, broken_count
    
    def _validate_external_links(self) -> Tuple[int, int]:
        """Validate external URLs."""
        valid_count = 0
        broken_count = 0
        
        # Find all markdown files
        markdown_files = self._find_all_markdown_files()
        
        for file_path in markdown_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find external links
            external_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            
            for text, url in external_links:
                if url.startswith('http'):
                    try:
                        response = self.session.head(url, timeout=10, allow_redirects=True)
                        if response.status_code < 400:
                            valid_count += 1
                        else:
                            broken_count += 1
                            self.broken_links.append({
                                'file': file_path,
                                'link': url,
                                'type': 'external',
                                'status_code': response.status_code
                            })
                    except Exception as e:
                        broken_count += 1
                        self.broken_links.append({
                            'file': file_path,
                            'link': url,
                            'type': 'external',
                            'error': str(e)
                        })
        
        return valid_count, broken_count
    
    def _find_all_markdown_files(self) -> List[str]:
        """Find all markdown files in the knowledge base."""
        markdown_files = []
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.md'):
                    markdown_files.append(os.path.join(root, file))
        
        return markdown_files
    
    def _count_updated_files(self) -> int:
        """Count number of files updated with cross-references."""
        # Simplified implementation
        return len(self._find_all_markdown_files())
    
    def _generate_link_report(self, stats: Dict[str, Any]) -> None:
        """Generate link validation report."""
        report_path = os.path.join(self.base_dir, 'link_validation_report.md')
        
        content = f"# Link Validation Report\n\n"
        content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += f"## Statistics\n\n"
        content += f"- Total papers: {stats['total_papers']}\n"
        content += f"- Bidirectional links created: {stats['bidirectional_links']}\n"
        content += f"- Internal links validated: {stats.get('internal_links_validated', 0)}\n"
        content += f"- External links validated: {stats.get('external_links_validated', 0)}\n"
        content += f"- Broken links found: {stats.get('broken_links_found', 0)}\n\n"
        
        if self.broken_links:
            content += f"## Broken Links\n\n"
            for broken_link in self.broken_links:
                content += f"- **File**: {broken_link['file']}\n"
                content += f"  **Link**: {broken_link['link']}\n"
                content += f"  **Type**: {broken_link['type']}\n"
                if 'status_code' in broken_link:
                    content += f"  **Status Code**: {broken_link['status_code']}\n"
                if 'error' in broken_link:
                    content += f"  **Error**: {broken_link['error']}\n"
                content += "\n"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)


if __name__ == "__main__":
    # Test the agent
    config = {}
    
    agent = CrossReferenceLinkingAgent(config)
    
    test_input = {
        'papers': [
            {
                'title': 'Test Paper 1',
                'authors': ['Smith, John'],
                'year': 2023,
                'venue': 'Test Journal',
                'analysis': {'extracted_topics': ['machine learning']}
            }
        ]
    }
    
    result = agent.run(test_input)
    print(f"Cross-reference linking completed: {result}")
