# API Reference

**CollegeAdvisor RAG System - REST API Documentation**

---

## Base URL

**Local Development**: `http://localhost:8000`  
**Production (Cloud Run)**: `https://collegeadvisor-api-[hash]-uc.a.run.app`

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check system health and component status.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "chromadb": "ok",
    "ollama": "ok",
    "rag_system": "ok"
  },
  "version": "1.0.0",
  "timestamp": "2025-10-27T14:30:00Z"
}
```

---

### 2. Get Recommendations

**POST** `/api/mobile/recommendations`

Get personalized college recommendations with RAG-powered answers.

**Request:**
```json
{
  "query": "What are the CS transfer requirements for UC Berkeley?",
  "user_preferences": {
    "academic_interests": ["Computer Science"],
    "preferred_locations": ["California"],
    "college_preferences": {
      "size": "medium",
      "setting": "urban"
    }
  },
  "limit": 10
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "type": "answer",
      "content": "## UC Berkeley CS Transfer Requirements\n\nTo transfer to UC Berkeley's Computer Science program...",
      "citations": [
        {
          "url": "https://eecs.berkeley.edu/admissions",
          "title": "UC Berkeley EECS Admissions",
          "snippet": "The EECS major requires...",
          "authority_level": "high"
        }
      ],
      "confidence": 0.95
    }
  ],
  "personalization_score": 0.88,
  "query_type": "transfer_requirements",
  "timestamp": "2025-10-27T14:30:00Z"
}
```

---

### 3. Search

**POST** `/api/mobile/search`

Mobile-optimized search with natural language queries.

**Request:**
```json
{
  "query": "What financial aid is available for foster youth?",
  "limit": 10,
  "include_reasoning": true
}
```

**Response:**
```json
{
  "results": [
    {
      "answer": "Foster youth are eligible for several special financial aid programs...",
      "citations": [
        {
          "url": "https://studentaid.gov/understand-aid/types/grants/fseog",
          "title": "Federal Supplemental Educational Opportunity Grant",
          "snippet": "Foster youth qualify for...",
          "authority_level": "high"
        }
      ],
      "confidence": 0.92,
      "reasoning": "Query matched Foster Care handler (priority 150). Retrieved 8 documents from aid_policies collection..."
    }
  ],
  "total_results": 1,
  "query_classification": "financial_aid_special_circumstances"
}
```

---

## Request Parameters

### Common Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Natural language query |
| `limit` | integer | No | Max results (default: 10) |
| `include_reasoning` | boolean | No | Include RAG reasoning (default: false) |

### User Preferences (Optional)

| Field | Type | Description |
|-------|------|-------------|
| `academic_interests` | array[string] | Majors/fields of interest |
| `preferred_locations` | array[string] | States/regions |
| `college_preferences.size` | string | "small", "medium", "large" |
| `college_preferences.setting` | string | "urban", "suburban", "rural" |

---

## Response Fields

### Answer Object

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Markdown-formatted answer |
| `citations` | array[Citation] | Authoritative sources |
| `confidence` | float | Confidence score (0-1) |
| `reasoning` | string | RAG reasoning (if requested) |

### Citation Object

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | Source URL |
| `title` | string | Source title |
| `snippet` | string | Relevant excerpt |
| `authority_level` | string | "high", "medium", "low" |

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid query: query must be non-empty string"
}
```

### 404 Not Found
```json
{
  "detail": "Endpoint not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "RAG system error: ChromaDB connection failed"
}
```

---

## Rate Limits

- **Free Tier**: 10 requests/minute
- **Premium Tier**: 100 requests/minute
- **Institutional Tier**: 1000 requests/minute

---

## Example Usage

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/mobile/recommendations",
    json={
        "query": "What are UC Berkeley CS transfer requirements?",
        "limit": 10
    }
)

data = response.json()
print(data["recommendations"][0]["content"])
```

### cURL
```bash
curl -X POST http://localhost:8000/api/mobile/recommendations \
  -H "Content-Type: application/json" \
  -d '{"query": "What are UC Berkeley CS transfer requirements?"}'
```

### Swift (iOS)
```swift
let url = URL(string: "https://collegeadvisor-api.run.app/api/mobile/recommendations")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let body: [String: Any] = [
    "query": "What are UC Berkeley CS transfer requirements?",
    "limit": 10
]
request.httpBody = try? JSONSerialization.data(withJSONObject: body)

URLSession.shared.dataTask(with: request) { data, response, error in
    // Handle response
}.resume()
```

---

**Version**: 1.0.0  
**Base URL**: `http://localhost:8000` (local) or Cloud Run URL (production)  
**Authentication**: None (public endpoints)

