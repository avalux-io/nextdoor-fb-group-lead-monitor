# Nextdoor & Facebook Group Lead Monitor

> **Open source local lead monitoring for service businesses.** Built by [Avalux](https://avalux.io), a full-stack AI automation agency. This repository provides the core scaffolding for monitoring local social platforms and identifying buying-intent posts.

## Why this exists

Local service businesses miss thousands of potential customers every day. While homeowners post "Need a plumber ASAP" or "Looking for landscaping recommendations" in Nextdoor neighborhoods and Facebook community groups, most contractors never see these posts until it's too late.

Traditional lead generation focuses on outbound marketing or expensive advertising. But the highest-intent prospects are already asking for help in local online communities. The challenge is systematic monitoring, intelligent scoring, and timely notification across multiple platforms and geographic areas.

This repository solves the technical foundation: authenticated API access, geographic filtering, keyword pattern matching, and lead scoring algorithms. It's designed for agencies and developers who need to build robust local lead monitoring systems.

## Who this is for

**Service business owners** who want to catch local opportunities as they happen. HVAC contractors, landscapers, handymen, cleaning services, and other local businesses that rely on geographic proximity.

**Marketing agencies** building lead generation systems for local service clients. This codebase handles the complex API authentication, rate limiting, and geographic filtering that makes local social monitoring challenging.

**Developers** who need a starting point for social platform monitoring. The authentication flows, webhook handlers, and scoring algorithms provide a foundation for custom implementations.

## What's in the box

```
nextdoor-fb-group-lead-monitor/
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── monitor.py              # Main monitoring logic
│   ├── platforms/
│   │   ├── __init__.py
│   │   ├── nextdoor.py         # Nextdoor API integration
│   │   └── facebook.py         # Facebook Groups API
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── intent_scorer.py    # Buying intent algorithms
│   │   └── urgency_detector.py # Time-sensitive keyword detection
│   ├── geo/
│   │   ├── __init__.py
│   │   └── radius_filter.py    # Geographic boundary logic
│   └── notifications/
│       ├── __init__.py
│       ├── webhook.py          # Outbound lead notifications
│       └── formatters.py       # Lead data formatting
├── config/
│   ├── keywords.json           # Service-specific search terms
│   ├── scoring_weights.json    # Intent scoring parameters
│   └── geo_boundaries.json     # Service area definitions
├── tests/
│   ├── __init__.py
│   ├── test_monitor.py
│   └── test_scoring.py
└── docs/
    ├── API_SETUP.md            # Platform authentication guides
    ├── SCORING_LOGIC.md        # Intent detection algorithms
    └── DEPLOYMENT.md           # Production deployment notes
```

## Quick start

**1. Clone and install dependencies**
```bash
git clone https://github.com/elikem2021/nextdoor-fb-group-lead-monitor.git
cd nextdoor-fb-group-lead-monitor
pip install -r requirements.txt
```

**2. Configure platform access**
```bash
cp .env.example .env
# Edit .env with your API credentials
```

**3. Set up service areas**
```bash
# Edit config/geo_boundaries.json with your target locations
# Example: 5-mile radius around business address
```

**4. Run initial test**
```bash
python -m src.monitor --test-mode --platform=nextdoor
```

**5. Configure keywords for your vertical**
```bash
# Edit config/keywords.json
# Add service-specific terms like "plumber", "emergency repair", etc.
```

## Platform authentication

### Nextdoor Business API

Nextdoor's Business API requires verification as a legitimate local business. The authentication flow involves:

1. **Business verification**: Submit business license and address verification
2. **API application**: Request developer access with specific use case
3. **OAuth 2.0 flow**: Standard three-legged OAuth for user consent
4. **Webhook registration**: Real-time post notifications within service area

```python
# Example authentication check
from src.platforms.nextdoor import NextdoorClient

client = NextdoorClient(
    client_id=os.getenv('NEXTDOOR_CLIENT_ID'),
    client_secret=os.getenv('NEXTDOOR_CLIENT_SECRET')
)

# Verify API access and rate limits
status = client.verify_access()
print(f"Rate limit: {status['rate_limit_remaining']}/hour")
```

### Facebook Groups API

Facebook's Groups API has strict approval requirements and limited public group access. The integration focuses on:

1. **App review process**: Facebook requires detailed use case documentation
2. **Group permissions**: Admin approval required for monitoring
3. **Content Policy compliance**: Automated systems must respect community guidelines
4. **Rate limiting**: Conservative request patterns to avoid API suspension

```python
# Example group monitoring setup
from src.platforms.facebook import FacebookGroupsClient

client = FacebookGroupsClient(access_token=os.getenv('FB_ACCESS_TOKEN'))

# Monitor specific groups with geographic relevance
groups = [
    {'id': '123456789', 'name': 'Denver Home Improvement', 'radius_miles': 25},
    {'id': '987654321', 'name': 'Boulder Area Services', 'radius_miles': 15}
]

for group in groups:
    client.setup_webhook(group['id'], callback_url='/webhook/facebook')
```

## Geographic filtering

Local service businesses operate within specific service areas. The geographic filtering system handles:

**Radius-based boundaries**: Simple distance calculations from business location
```python
from src.geo.radius_filter import RadiusFilter

filter = RadiusFilter(
    center_lat=39.7392,  # Denver coordinates
    center_lng=-104.9903,
    radius_miles=15
)

# Check if a post location falls within service area
if filter.contains(post_lat, post_lng):
    # Process this lead
    pass
```

**ZIP code boundaries**: More precise service area definitions
```python
# config/geo_boundaries.json example
{
    "service_areas": [
        {
            "name": "Denver Metro",
            "zip_codes": ["80202", "80203", "80204", "80205"],
            "include_adjacent": true
        }
    ]
}
```

**Custom polygon boundaries**: Complex service areas with geographic constraints
```python
# Handle mountain areas, water boundaries, etc.
from shapely.geometry import Point, Polygon

service_polygon = Polygon([(lat1, lng1), (lat2, lng2), ...])
post_location = Point(post_lat, post_lng)

if service_polygon.contains(post_location):
    # Within complex service boundary
    pass
```

## Intent scoring algorithms

Not all posts represent genuine buying intent. The scoring system evaluates multiple factors:

### Urgency indicators
```python
# High-urgency keywords boost lead scores
URGENT_KEYWORDS = [
    "emergency", "ASAP", "urgent", "broken", "not working",
    "flooding", "no heat", "won't start", "help!"
]

# Time-based urgency
def calculate_urgency_score(post_text, post_time):
    score = 0
    
    # Keyword matching
    for keyword in URGENT_KEYWORDS:
        if keyword.lower() in post_text.lower():
            score += 25
    
    # Weekend/evening posts often indicate urgency
    if post_time.weekday() >= 5:  # Weekend
        score += 15
    if post_time.hour >= 18 or post_time.hour <= 6:  # Evening/night
        score += 10
    
    return min(score, 100)
```

### Service-specific matching
```python
# Match posts to specific service categories
SERVICE_PATTERNS = {
    "plumbing": {
        "keywords": ["plumber", "leak", "pipe", "drain", "toilet", "faucet"],
        "negative_keywords": ["DIY", "myself", "tutorial"]
    },
    "hvac": {
        "keywords": ["heating", "cooling", "AC", "furnace", "thermostat"],
        "negative_keywords": ["filter change", "maintenance"]
    }
}

def match_service_category(post_text):
    scores = {}
    
    for service, patterns in SERVICE_PATTERNS.items():
        score = 0
        
        # Positive keyword matching
        for keyword in patterns["keywords"]:
            if keyword.lower() in post_text.lower():
                score += 20
        
        # Negative keyword penalties
        for neg_keyword in patterns["negative_keywords"]:
            if neg_keyword.lower() in post_text.lower():
                score -= 30
        
        scores[service] = max(score, 0)
    
    return scores
```

### Budget and timeline signals
```python
# Detect posts with clear budget or timeline indicators
def extract_budget_timeline(post_text):
    import re
    
    # Budget pattern matching
    budget_patterns = [
        r'\$([0-9,]+)',  # $500, $1,200
        r'budget.*?([0-9,]+)',  # "budget is 800"
        r'willing to pay.*?([0-9,]+)'  # "willing to pay up to 1500"
    ]
    
    # Timeline pattern matching
    timeline_patterns = [
        r'need.*?(today|tomorrow|this week)',
        r'by.*?(monday|tuesday|wednesday|thursday|friday)',
        r'within.*?([0-9]+).*?(day|week)'
    ]
    
    budget_score = 0
    timeline_score = 0
    
    for pattern in budget_patterns:
        if re.search(pattern, post_text.lower()):
            budget_score = 30
            break
    
    for pattern in timeline_patterns:
        if re.search(pattern, post_text.lower()):
            timeline_score = 25
            break
    
    return budget_score + timeline_score
```

## Webhook notifications

When high-scoring leads are detected, the system sends structured notifications:

```python
# Example webhook payload
webhook_payload = {
    "lead_id": "fb_123456789_post_987654321",
    "platform": "facebook",
    "score": 85,
    "post_data": {
        "text": "Emergency plumber needed! Pipe burst in basement, water everywhere. Need help ASAP!",
        "author": "Sarah M.",
        "location": "Denver, CO",
        "post_url": "https://facebook.com/groups/denver-home/posts/123456",
        "timestamp": "2024-01-15T14:30:00Z"
    },
    "scoring_breakdown": {
        "urgency": 40,
        "service_match": 30,
        "geographic_relevance": 15
    },
    "recommended_action": "immediate_response"
}
```

## Production considerations

This open source version provides core functionality, but production deployments require additional hardening:

**Rate limit management**: Both platforms have strict API limits. Production systems need sophisticated queuing and backoff strategies.

**Content policy compliance**: Automated monitoring must respect platform terms of service and community guidelines.

**Data privacy**: Local posts often contain personal information. Production systems need careful PII handling and retention policies.

**Scale considerations**: Monitoring hundreds of groups across multiple cities requires distributed processing and efficient data storage.

**Integration complexity**: Real business value comes from connecting lead detection to CRM systems, notification workflows, and response tracking.

## Why we built this

At [Avalux](https://avalux.io), we work with local service businesses who struggle with inconsistent lead flow. Traditional marketing channels are expensive and competitive, but social platforms contain thousands of high-intent prospects asking for help.

The technical challenge is systematic monitoring at scale while respecting platform policies and delivering actionable intelligence. This open source project provides the foundation, but production implementations require custom integration work.

If you're building lead generation systems for local businesses, we'd love to collaborate. Contact us at [avalux.io](https://avalux.io).

## Avalux's other open source projects

- [Freight ETA Toolkit](https://github.com/elikem2021/freight-eta-toolkit) - Supply chain visibility and shipment tracking
- [Multi-Channel Attribution Engine](https://github.com/elikem2021/attribution-engine) - Marketing attribution across touchpoints
- [Customer Health Score Calculator](https://github.com/elikem2021/customer-health-score) - Churn prediction and account monitoring

## License

MIT License - see LICENSE file for details.

---

**Keywords**: Nextdoor lead generation, Facebook group monitoring, local service lead capture, buying intent detection, social media lead scraping, neighborhood lead monitoring, local business automation, service area lead tracking, community group monitoring, geographic lead filtering