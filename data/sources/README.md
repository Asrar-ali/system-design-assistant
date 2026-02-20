# System Design Source Curation

**Purpose:** This directory contains manually curated, high-quality system design resources for the RAG pipeline. Quality curation here determines 60% of the final answer quality — garbage in, garbage out.

**Current Status:** 26 sources curated across 3 types (GitHub repos, engineering blogs, YouTube videos) with manual validation for content quality and extractability.

---

## Source Inventory

| Source Type | Count | Estimated Chunks | Examples |
|-------------|-------|------------------|----------|
| **GitHub Repos** | 10 | 1,830 | system-design-primer, karanpratapsingh/system-design, ByteByteGo/system-design-101 |
| **Engineering Blogs** | 8 | 545 | Netflix TechBlog, Meta Engineering, Uber Engineering, AWS Architecture Blog |
| **YouTube Videos** | 8 | 172 | ByteByteGo (CAP theorem, message queues), Gaurav Sen (URL shortener, rate limiter) |
| **TOTAL** | **26** | **2,547** | Covers all major system design topics for interview preparation |

**Chunk Estimation Method:**
- GitHub: Manual review of README + markdown file count (avg 400-500 tokens per chunk)
- Blogs: Sample article word count / 400 (estimated avg chunk size)
- YouTube: Transcript word count / 400

---

## Quality Criteria

### Authority Level Thresholds

| Level | Definition | Examples | Validation |
|-------|------------|----------|------------|
| **HIGH** | FAANG engineering blogs, 10K+ GitHub stars, well-known industry experts | Netflix TechBlog, system-design-primer (275K stars), ByteByteGo | Manual verification of author credentials, star count check via PyGithub |
| **MEDIUM** | Professional engineering blogs, 5K-10K stars, verified engineers | Yelp Engineering, Tech Dummies Narendra L | Blog domain authority check, sample content review |
| **COMMUNITY** | Curated lists, awesome repos, well-maintained collections | awesome-system-design (12K stars), awesome-scalability | Verify curation quality by sampling 3-5 linked resources |

### Content Quality Requirements

**Minimum Standards:**
- **GitHub Repos:**
  - 200+ words in README or sample markdown files
  - Technical depth appropriate for 3rd year CS student
  - Substantive explanations (not just code or links)
  - Active maintenance (updated within 2 years)

- **Blog Posts:**
  - 200+ words per article (technical blog posts)
  - Technical depth with code examples or architecture diagrams
  - Link density < 30% (avoid link-heavy marketing content)
  - No paywalls blocking content extraction

- **YouTube Videos:**
  - 500+ words in transcript
  - System design terminology verified (e.g., "scalability", "CAP theorem", "sharding")
  - Transcript available via youtube-transcript-api
  - Educational content (not marketing or product demos)

### Deduplication Strategy

- **GitHub:** SHA-256 hash of repo URL (repos don't change URLs)
- **Blogs:** URL + publication date (same blog may republish content)
- **YouTube:** Video ID from URL (YouTube IDs are permanent)

**Deduplication is handled at ingestion time (Phase 3)**, not during curation. Curation focuses on quality validation.

---

## Topic Coverage

Topic taxonomy defined in `topic_taxonomy.json` maps content to 8 TopicCategory enum values:

| TopicCategory | Description | Example Sources |
|---------------|-------------|-----------------|
| **DATABASES** | Database selection, scaling, consistency models | system-design-primer, Meta Engineering, Gaurav Sen (URL shortener) |
| **CACHING** | Redis, Memcached, CDN, invalidation strategies | Netflix TechBlog, awesome-scalability |
| **LOAD_BALANCING** | L4/L7 balancing, algorithms, health checks | ByteByteGo/system-design-101, AWS Architecture Blog |
| **SCALABILITY** | Horizontal scaling, partitioning, microservices | karanpratapsingh/system-design, Uber Engineering, Tech Dummies (Twitter design) |
| **RELIABILITY** | Fault tolerance, disaster recovery, circuit breakers | Stripe Engineering, AWS Architecture Blog |
| **DISTRIBUTED_SYSTEMS** | CAP theorem, consensus, eventual consistency | ByteByteGo (CAP theorem), awesome-system-design |
| **API_DESIGN** | REST, GraphQL, gRPC, versioning, rate limiting | ByteByteGo (API gateway), Gaurav Sen (rate limiter) |
| **GENERAL** | Multi-topic content, interview fundamentals | system-design-primer, checkcheckzz/system-design-interview |

**Current Distribution** (sources can have multiple categories):
- Most coverage: SCALABILITY, DISTRIBUTED_SYSTEMS, DATABASES (10+ sources each)
- Good coverage: GENERAL, CACHING, API_DESIGN (5-8 sources)
- Adequate coverage: RELIABILITY, LOAD_BALANCING (3-5 sources)

**Gap Analysis:** All categories have minimum viable coverage. Future curation can focus on:
- More real-world reliability case studies (incident reports)
- Advanced load balancing scenarios (global traffic management)

---

## Adding New Sources

Follow this validation workflow before adding sources to JSON files:

### Step 1: Content Extraction Validation

**GitHub Repos:**
```python
from github import Github
import os

# Requires GITHUB_TOKEN environment variable
g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo("donnemartin/system-design-primer")

print(f"Stars: {repo.stargazers_count}")
print(f"Last updated: {repo.updated_at}")

# Sample markdown content
readme = repo.get_readme()
content = readme.decoded_content.decode('utf-8')
word_count = len(content.split())
print(f"README word count: {word_count}")

# Check for substantive content (not just links)
if word_count < 200:
    print("❌ FAIL: Insufficient content")
else:
    print("✅ PASS: Sufficient content")
```

**Blog Posts:**
```python
from bs4 import BeautifulSoup
import requests

url = "https://stripe.com/blog/engineering"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract main content (adjust selector per site)
content = soup.find('article') or soup.find('main')
text = content.get_text() if content else ""
word_count = len(text.split())

# Calculate link density
links = len(content.find_all('a')) if content else 0
link_density = (links / word_count * 100) if word_count > 0 else 100

print(f"Word count: {word_count}")
print(f"Link density: {link_density:.2f}%")

if word_count < 200:
    print("❌ FAIL: Insufficient content")
elif link_density > 30:
    print("❌ FAIL: Too link-heavy (marketing content)")
else:
    print("✅ PASS: Quality content extractable")
```

**YouTube Videos:**
```python
from youtube_transcript_api import YouTubeTranscriptApi

video_id = "lX4CrbXMsNQ"  # From URL: youtube.com/watch?v=lX4CrbXMsNQ
transcript = YouTubeTranscriptApi.get_transcript(video_id)

# Concatenate all text
full_text = " ".join([entry['text'] for entry in transcript])
word_count = len(full_text.split())

print(f"Transcript word count: {word_count}")

# Check for system design terminology
keywords = ['system design', 'scalability', 'database', 'architecture', 'distributed']
found_keywords = [kw for kw in keywords if kw.lower() in full_text.lower()]

if word_count < 500:
    print("❌ FAIL: Transcript too short")
elif not found_keywords:
    print("❌ FAIL: No system design terminology")
else:
    print(f"✅ PASS: Quality transcript with keywords: {found_keywords}")
```

### Step 2: Quality Criteria Check

Run validation from Step 1, then manually verify:

- **Technical depth:** Read sample content — does it explain WHY (trade-offs) not just WHAT (definitions)?
- **Target audience:** Is it appropriate for 3rd year CS student? (Not too basic, not research-level)
- **Substantive explanations:** Are there code examples, diagrams, or multi-step patterns?

### Step 3: Add to JSON File

Follow the `Source` schema from `src/models/source.py`:

**Required fields:**
- `url`: Full URL to resource
- `source_type`: "github_repo" | "blog_post" | "youtube_video"
- `topic_categories`: Array of TopicCategory enum values (can be multiple)
- `authority_level`: "high" | "medium" | "community"
- `title`: Descriptive title
- `author`: Author name or organization
- `validated`: true (after Step 1-2 checks)
- `validation_notes`: String documenting validation results (word count, link density, etc.)
- `curated_date`: ISO 8601 timestamp (e.g., "2026-02-07T20:05:00Z")
- `estimated_chunks`: Integer estimate (word_count / 400)

**Type-specific optional fields:**
- GitHub: `github_repo_stars` (integer)
- YouTube: `youtube_views` (integer, optional)
- Blogs: `blog_publication_date` (ISO 8601 timestamp, optional)

**Example GitHub entry:**
```json
{
  "url": "https://github.com/donnemartin/system-design-primer",
  "source_type": "github_repo",
  "topic_categories": ["general", "scalability", "databases"],
  "authority_level": "high",
  "title": "The System Design Primer",
  "author": "donnemartin",
  "validated": true,
  "validation_notes": "README word count: 15000, verified substantive explanations",
  "curated_date": "2026-02-07T20:05:00Z",
  "estimated_chunks": 400,
  "github_repo_stars": 275000
}
```

### Step 4: Update Source Count

After adding to JSON file:
1. Recalculate total source count
2. Update the **Source Inventory** table in this README
3. Run validation commands (see below) to ensure schema compliance

---

## Metadata Schema Reference

Full schema defined in `src/models/source.py`:

**Core Schema:**
```python
@dataclass
class Source:
    url: str
    source_type: SourceType  # Enum: GITHUB_REPO, BLOG_POST, YOUTUBE_VIDEO
    topic_categories: list[TopicCategory]  # Array of enums (see topic_taxonomy.json)
    authority_level: AuthorityLevel  # Enum: HIGH, MEDIUM, COMMUNITY
    title: str
    author: str
    validated: bool = False
    validation_notes: str = ""
    curated_date: datetime | None = None
    estimated_chunks: int = 0

    # Type-specific optional fields
    github_repo_stars: int | None = None
    youtube_views: int | None = None
    blog_publication_date: datetime | None = None
```

**Enum Definitions:**
- `SourceType`: `GITHUB_REPO`, `BLOG_POST`, `YOUTUBE_VIDEO`
- `TopicCategory`: `DATABASES`, `CACHING`, `LOAD_BALANCING`, `SCALABILITY`, `RELIABILITY`, `DISTRIBUTED_SYSTEMS`, `API_DESIGN`, `GENERAL`
- `AuthorityLevel`: `HIGH`, `MEDIUM`, `COMMUNITY`

**Serialization:** Use `Source.to_dict()` for JSON export, `Source.from_dict()` for import.

---

## Validation Commands

### Verify JSON Schema Compliance

```bash
# Check all sources load without errors
python3.11 -c "
from src.models.source import Source
import json

for source_file in ['data/sources/github_sources.json', 'data/sources/blog_sources.json', 'data/sources/youtube_sources.json']:
    sources = json.load(open(source_file))
    for s in sources:
        Source.from_dict(s)  # Will raise if schema invalid
    print(f'✅ {source_file}: {len(sources)} sources valid')
"
```

### Count Sources by Type

```bash
python3.11 -c "
import json

github = len(json.load(open('data/sources/github_sources.json')))
blogs = len(json.load(open('data/sources/blog_sources.json')))
youtube = len(json.load(open('data/sources/youtube_sources.json')))

print(f'GitHub: {github}')
print(f'Blogs: {blogs}')
print(f'YouTube: {youtube}')
print(f'Total: {github + blogs + youtube}')
"
```

### Check All Sources Validated

```bash
python3.11 -c "
import json

all_validated = True
for source_file in ['data/sources/github_sources.json', 'data/sources/blog_sources.json', 'data/sources/youtube_sources.json']:
    sources = json.load(open(source_file))
    unvalidated = [s['title'] for s in sources if not s.get('validated', False)]
    if unvalidated:
        print(f'❌ {source_file}: Unvalidated sources: {unvalidated}')
        all_validated = False

if all_validated:
    print('✅ All sources validated')
"
```

### Calculate Topic Coverage

```bash
python3.11 -c "
import json
from collections import Counter

topic_counts = Counter()
for source_file in ['data/sources/github_sources.json', 'data/sources/blog_sources.json', 'data/sources/youtube_sources.json']:
    sources = json.load(open(source_file))
    for s in sources:
        for topic in s['topic_categories']:
            topic_counts[topic] += 1

print('Topic coverage:')
for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
    print(f'  {topic}: {count} sources')
"
```

---

## Contributors

When adding sources:
1. **Quality over quantity** — 5 excellent sources beat 20 mediocre ones
2. **Validate before adding** — Run extraction tests first
3. **Document validation** — Record word counts, link density, technical depth check in `validation_notes`
4. **Update this README** — Keep source counts current
5. **Test ingestion** — After Phase 3 is built, verify new sources extract cleanly

For questions or proposed sources, open an issue with validation results from Step 1.
