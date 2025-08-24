# 🔑 API Setup Guide for APPA System

*Complete guide to configure academic API integrations*

## 📖 Overview

APPA (Awesome PHM Paper Agent) integrates with multiple academic databases to provide comprehensive paper discovery. This guide covers setup for all supported APIs, including both free and premium services.

## 🆓 Free APIs (No Registration Required)

### 1. OpenAlex API
**Status**: ✅ Always enabled, no setup required  
**Coverage**: 250M+ academic papers across all disciplines  
**Documentation**: https://docs.openalex.org/

```bash
# No API key required, but email recommended for better performance
export OPENALEX_EMAIL="your.email@example.com"
```

**Benefits:**
- Free unlimited access
- Comprehensive metadata
- Abstract reconstruction capability
- Cross-disciplinary coverage

### 2. Crossref API
**Status**: ✅ Always enabled, no setup required  
**Coverage**: 130M+ scholarly records with DOI focus  
**Documentation**: https://api.crossref.org/

```bash
# Optional: email for better rate limits
export CROSSREF_EMAIL="your.email@example.com" 
```

**Benefits:**
- Authoritative DOI data
- Publisher information
- Citation linking
- Venue quality metrics

### 3. PubMed/Europe PMC API
**Status**: ✅ Always enabled, no setup required  
**Coverage**: 35M+ biomedical and life science papers  
**Documentation**: https://www.ncbi.nlm.nih.gov/books/NBK25501/

```bash
# No configuration required
# Automatically uses both PubMed and Europe PMC
```

**Benefits:**
- Biomedical focus
- MeSH term categorization
- Government-maintained
- High-quality metadata

## 🔑 Premium APIs (Registration Required)

### 4. Semantic Scholar API
**Status**: 🔓 Requires API key  
**Coverage**: 200M+ papers with AI-powered insights  
**Registration**: https://www.semanticscholar.org/product/api

#### Setup Instructions:

1. **Register for API Key:**
   - Visit https://www.semanticscholar.org/product/api
   - Create account and request API access
   - Free tier: 1,000 requests/5 minutes

2. **Configure Environment:**
   ```bash
   # Add to .env file
   export SEMANTIC_SCHOLAR_API_KEY="your_api_key_here"
   ```

3. **Enable in Config:**
   ```yaml
   # config.yaml
   data_sources:
     semantic_scholar:
       enabled: true
       api_key: ""  # Will read from environment
   ```

**Benefits:**
- AI-powered semantic search
- Influential citations tracking
- Author disambiguation
- Paper recommendations

### 5. Lens.org API
**Status**: 🔓 Requires API key  
**Coverage**: 250M+ scholarly works plus patent data  
**Registration**: https://www.lens.org/lens/user/subscriptions

#### Setup Instructions:

1. **Register for API Key:**
   - Visit https://www.lens.org/lens/user/subscriptions
   - Create account (free tier available)
   - Free tier: 1,000 requests/month

2. **Configure Environment:**
   ```bash
   # Add to .env file
   export LENS_API_KEY="your_lens_api_key_here"
   ```

3. **Enable in Config:**
   ```yaml
   # config.yaml
   data_sources:
     lens:
       enabled: true
       api_key: ""  # Will read from environment
   ```

**Benefits:**
- Patent integration
- Multi-identifier search
- Excellent metadata coverage
- Legal and regulatory insights

## 🛠️ Complete Setup Process

### Step 1: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### Step 2: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

### Step 3: Verify Configuration

```bash
# Test API connections
python -c "
from src.utils.api_manager import APIManager
manager = APIManager()
status = manager.get_api_status()
print('API Status:', status)
"
```

### Step 4: Test Search Functionality

```bash
# Test with sample query
python -c "
from src.utils.api_manager import APIManager
manager = APIManager()
papers = manager.search_papers('bearing fault diagnosis', max_results=5)
print(f'Found {len(papers)} papers')
"
```

## ⚡ Rate Limits & Performance

| API | Rate Limit | Max Results | Response Time |
|-----|------------|-------------|---------------|
| **OpenAlex** | 10 req/sec | 200/request | ~200ms |
| **Crossref** | 5 req/sec | 1000/request | ~150ms |
| **Semantic Scholar** | 1 req/sec | 1000/request | ~300ms |
| **PubMed** | 3 req/sec | 10000/request | ~400ms |
| **Lens.org** | 2 req/sec | 100/request | ~500ms |

## 🔧 Configuration Options

### API Priorities

The system automatically selects APIs based on configured priorities:

```yaml
# config.yaml - API priority order (5=highest, 1=lowest)
api_configuration:
  priorities:
    openalex: 5          # Free, comprehensive
    crossref: 4          # Free, DOI authority
    semantic_scholar: 3  # Requires key, AI features
    pubmed: 2            # Biomedical focus
    lens: 1              # Requires key, comprehensive
```

### Quality Filters

Configure automatic quality filtering:

```yaml
# config.yaml
quality_filters:
  min_citations: 5
  venue_quartile: ["Q1", "Q2"]
  min_publication_year: 2015
  venue_whitelist:
    - "Mechanical Systems and Signal Processing"
    - "IEEE Transactions on Reliability"
    # ... more venues
```

### PHM-Specific Settings

Customize PHM relevance detection:

```python
# Each API client includes PHM keyword matching
phm_keywords = [
    'prognostics', 'health management', 'predictive maintenance',
    'condition monitoring', 'fault diagnosis', 'remaining useful life',
    'reliability', 'degradation', 'anomaly detection'
]
```

## 🔍 Testing Your Setup

### Quick API Test

```bash
# Test individual API clients
python src/utils/openalex_client.py
python src/utils/crossref_client.py
python src/utils/semantic_scholar_client.py  # If API key configured
python src/utils/pubmed_client.py
python src/utils/lens_client.py  # If API key configured
```

### Integration Test

```bash
# Test the complete API manager
python src/utils/api_manager.py
```

### Search Test

```bash
# Test search functionality
python -c "
from src.utils.api_manager import APIManager
manager = APIManager()

# Test basic search
papers = manager.search_papers('prognostics health management', max_results=10)
print(f'Search Results: {len(papers)} papers found')

# Test API statistics  
stats = manager.get_aggregated_stats()
print(f'API Stats: {stats}')

# Test API status
status = manager.get_api_status()
for api in status['apis_available']:
    print(f'{api}: Available')
"
```

## 🚨 Troubleshooting

### Common Issues

#### 1. API Key Not Working
```bash
# Verify environment variables
echo $SEMANTIC_SCHOLAR_API_KEY
echo $LENS_API_KEY

# Check .env file is being loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Keys loaded:', bool(os.getenv('SEMANTIC_SCHOLAR_API_KEY')))"
```

#### 2. Rate Limit Errors
```python
# Adjust rate limits in config.yaml
api_configuration:
  rate_limits:
    semantic_scholar: 0.5  # Slower rate
    lens: 1  # Slower rate
```

#### 3. No Results Found
```python
# Check PHM relevance thresholds
data_sources:
  openalex:
    settings:
      min_phm_relevance: 0.1  # Lower threshold
```

#### 4. Connection Timeouts
```python
# Increase timeout settings
api_configuration:
  timeout_seconds: 60  # Longer timeout
  max_retries: 5
```

### Debug Mode

Enable detailed logging:

```python
# config.yaml
logging:
  level: "DEBUG"
  file: "logs/appa.log"
```

### API Status Check

```bash
# Check current API status
python -c "
from src.utils.api_manager import APIManager
import json
manager = APIManager()
status = manager.get_api_status()
print(json.dumps(status, indent=2))
"
```

## 📊 Performance Optimization

### Parallel Processing

```yaml
# config.yaml - Enable parallel API calls
advanced:
  enable_parallel: true
  worker_threads: 4
```

### Caching

```yaml
# Enable response caching
advanced:
  enable_caching: true
  cache_expiration_hours: 24
```

### Result Limits

```python
# Balance comprehensiveness vs speed
manager.search_papers(
    query="your query",
    max_results=50,  # Reasonable limit
    api_preference=['openalex', 'crossref']  # Use fastest APIs first
)
```

## 📈 Monitoring & Analytics

### API Performance Tracking

```python
# Get detailed performance statistics
from src.utils.api_manager import APIManager
manager = APIManager()

# After running searches...
stats = manager.get_aggregated_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Papers per request: {stats['avg_papers_per_request']:.1f}")
```

### Usage Patterns

Monitor your API usage to optimize performance:

```bash
# Check logs for usage patterns
tail -f logs/appa.log | grep "API"

# Analyze daily statistics
cat logs/stats.json | jq '.api_usage'
```

## 🔐 Security Best Practices

### Environment Variables
- ✅ Use `.env` files for API keys
- ✅ Never commit API keys to git
- ✅ Use different keys for dev/prod
- ✅ Rotate keys regularly

### Access Control
```bash
# Restrict .env file permissions
chmod 600 .env

# Verify gitignore is working
git status --ignored
```

### Rate Limiting
- ✅ Respect API rate limits
- ✅ Implement exponential backoff
- ✅ Monitor quota usage
- ✅ Use free APIs when possible

## 🎯 Production Deployment

### Docker Configuration

```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Environment variables will be provided at runtime
CMD ["python", "main.py"]
```

### Environment Management

```bash
# Production environment setup
export NODE_ENV=production
export SEMANTIC_SCHOLAR_API_KEY="prod_key_here"
export LENS_API_KEY="prod_key_here"
export OPENALEX_EMAIL="production@yourcompany.com"
```

## 📞 Support & Resources

### Official Documentation
- **OpenAlex**: https://docs.openalex.org/
- **Crossref**: https://api.crossref.org/
- **Semantic Scholar**: https://api.semanticscholar.org/
- **PubMed**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **Lens.org**: https://docs.api.lens.org/

### Getting Help
- **APPA Issues**: https://github.com/your-repo/issues
- **API-specific support**: Check respective API documentation
- **Community**: Join relevant academic API communities

---

*📅 Last updated: 2025-08-24 | 🤖 APPA v2.0 with Multi-API Integration*

## 🎉 Quick Start Summary

For impatient researchers who want to get started immediately:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Use free APIs immediately (no setup needed)
python -c "from src.utils.api_manager import APIManager; papers = APIManager().search_papers('your research topic', max_results=10); print(f'Found {len(papers)} papers')"

# 3. Optional: Add premium API keys to .env for enhanced features
cp .env.example .env
# Edit .env with your API keys

# 4. Start discovering papers!
python main.py --search "prognostics health management"
```

**You're ready to discover PHM papers across 5 academic databases! 🚀**