# 🔗 Integration Guide for collegeadvisor-api Repository

**Model:** collegeadvisor:latest  
**Status:** ✅ Ready for Integration  
**Date:** October 26, 2025

---

## 📦 **ARTIFACTS TO EXPORT**

### **1. Model Files (Required)**

Copy these files to your collegeadvisor-api repository:

```bash
# From CollegeAdvisor-data to collegeadvisor-api
scp gguf_models/gguf/fine_tuned_model-f16.gguf user@server:/path/to/collegeadvisor-api/models/
scp Modelfile user@server:/path/to/collegeadvisor-api/models/
```

**Files to transfer:**
- ✅ `gguf_models/gguf/fine_tuned_model-f16.gguf` (2.2GB) - The model
- ✅ `Modelfile` - Ollama configuration

### **2. API Client (Optional but Recommended)**

```bash
# Copy the Python client
scp college_advisor_api.py user@server:/path/to/collegeadvisor-api/
```

**File:**
- ✅ `college_advisor_api.py` - Production-ready Python client with helper methods

### **3. Documentation (Reference)**

```bash
# Copy documentation for reference
scp DEPLOYMENT_GUIDE.md user@server:/path/to/collegeadvisor-api/docs/
scp PRODUCTION_READY_REPORT.md user@server:/path/to/collegeadvisor-api/docs/
scp SHIP_IT_SUMMARY.md user@server:/path/to/collegeadvisor-api/docs/
```

---

## 🚀 **INTEGRATION CHECKLIST FOR collegeadvisor-api REPOSITORY**

### **Phase 1: Environment Setup** ⏳

#### **1.1 Install Ollama on Production Server**
```bash
# On your production server
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

#### **1.2 Transfer Model Files**
```bash
# Create models directory
mkdir -p /path/to/collegeadvisor-api/models

# Transfer files (from your local machine)
scp gguf_models/gguf/fine_tuned_model-f16.gguf server:/path/to/collegeadvisor-api/models/
scp Modelfile server:/path/to/collegeadvisor-api/models/
```

#### **1.3 Create Ollama Model**
```bash
# On production server
cd /path/to/collegeadvisor-api/models
ollama create collegeadvisor:latest -f Modelfile

# Verify model creation
ollama list | grep collegeadvisor
# Should show: collegeadvisor:latest    787ac59f3d77    2.2 GB
```

#### **1.4 Start Ollama Service**
```bash
# Option 1: Run as foreground process (testing)
ollama serve

# Option 2: Run as systemd service (production)
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```

---

### **Phase 2: API Integration** ⏳

#### **2.1 Install Dependencies**
```bash
# In your collegeadvisor-api repository
pip install requests  # For Ollama API calls
pip install flask flask-cors  # If using the Flask wrapper
```

#### **2.2 Add Model Client to Your API**

**Option A: Use the provided Python client**
```python
# Copy college_advisor_api.py to your repo
# Then in your API code:

from college_advisor_api import CollegeAdvisorClient

# Initialize client
client = CollegeAdvisorClient(
    base_url="http://localhost:11434",  # Or your Ollama server URL
    model="collegeadvisor:latest"
)

# Use in your endpoints
@app.route('/api/ask', methods=['POST'])
def ask_question():
    question = request.json.get('question')
    answer = client.ask(question)
    return jsonify({'answer': answer})
```

**Option B: Direct Ollama API integration**
```python
import requests

def ask_model(question):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "collegeadvisor:latest",
        "prompt": question,
        "stream": False
    }
    response = requests.post(url, json=payload, timeout=120)
    return response.json()["response"]
```

#### **2.3 Add API Endpoints**

Create these endpoints in your collegeadvisor-api:

```python
# 1. Simple Q&A endpoint
@app.route('/api/v1/ask', methods=['POST'])
def ask():
    """
    Ask the AI model a question
    
    Request:
    {
        "question": "What is the admission rate for Harvard?"
    }
    
    Response:
    {
        "answer": "The admissions rate for Harvard is approximately 3%.",
        "response_time": 0.25
    }
    """
    question = request.json.get('question')
    start_time = time.time()
    answer = client.ask(question)
    response_time = time.time() - start_time
    
    return jsonify({
        'answer': answer,
        'response_time': response_time
    })

# 2. School comparison endpoint
@app.route('/api/v1/compare', methods=['POST'])
def compare_schools():
    """
    Compare multiple schools
    
    Request:
    {
        "schools": ["MIT", "Stanford", "Caltech"],
        "criteria": ["admission rate", "engineering programs"]
    }
    
    Response:
    {
        "comparison": "...",
        "schools": ["MIT", "Stanford", "Caltech"]
    }
    """
    schools = request.json.get('schools', [])
    criteria = request.json.get('criteria')
    
    comparison = client.compare_schools(schools, criteria)
    
    return jsonify({
        'comparison': comparison,
        'schools': schools
    })

# 3. Personalized counseling endpoint
@app.route('/api/v1/counseling', methods=['POST'])
def personalized_counseling():
    """
    Get personalized college counseling advice
    
    Request:
    {
        "student_profile": {
            "gpa": 3.9,
            "sat": 1520,
            "background": "first-generation, low-income",
            "interests": "mechanical engineering",
            "activities": ["robotics club leadership", "community volunteer"]
        },
        "schools": ["MIT", "Stanford", "Caltech"],
        "question": "What are my chances and what should I emphasize?"
    }
    
    Response:
    {
        "advice": "...",
        "recommendations": [...]
    }
    """
    profile = request.json.get('student_profile', {})
    schools = request.json.get('schools', [])
    question = request.json.get('question', '')
    
    # Build personalized prompt
    prompt = f"""
    Student Profile:
    - GPA: {profile.get('gpa')}
    - SAT: {profile.get('sat')}
    - Background: {profile.get('background')}
    - Interests: {profile.get('interests')}
    - Activities: {', '.join(profile.get('activities', []))}
    
    Schools of Interest: {', '.join(schools)}
    
    Question: {question}
    """
    
    advice = client.ask(prompt)
    
    return jsonify({
        'advice': advice,
        'student_profile': profile,
        'schools': schools
    })

# 4. Admission info endpoint
@app.route('/api/v1/admission/<school>', methods=['GET'])
def get_admission_info(school):
    """
    Get admission information for a specific school
    
    Response:
    {
        "school": "Harvard",
        "info": "..."
    }
    """
    info = client.get_admission_info(school)
    
    return jsonify({
        'school': school,
        'info': info
    })

# 5. Health check endpoint
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """
    Check if the AI model is available
    
    Response:
    {
        "status": "healthy",
        "model": "collegeadvisor:latest",
        "ollama_url": "http://localhost:11434"
    }
    """
    try:
        # Test connection to Ollama
        response = requests.get(f"{client.base_url}/api/tags", timeout=5)
        response.raise_for_status()
        
        return jsonify({
            'status': 'healthy',
            'model': client.model,
            'ollama_url': client.base_url
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503
```

---

### **Phase 3: Configuration** ⏳

#### **3.1 Environment Variables**

Create `.env` file in your collegeadvisor-api repository:

```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=collegeadvisor:latest
OLLAMA_TIMEOUT=120
API_PORT=5000
API_HOST=0.0.0.0
```

#### **3.2 Configuration File**

Create `config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Ollama settings
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'collegeadvisor:latest')
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '120'))
    
    # API settings
    API_PORT = int(os.getenv('API_PORT', '5000'))
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    
    # Performance settings
    ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
    CACHE_SIZE = int(os.getenv('CACHE_SIZE', '1000'))
    
    # Rate limiting
    RATE_LIMIT = os.getenv('RATE_LIMIT', '100 per hour')
```

---

### **Phase 4: Testing** ⏳

#### **4.1 Create Test Suite**

Create `tests/test_model_integration.py`:

```python
import pytest
import requests

BASE_URL = "http://localhost:5000/api/v1"

def test_health_check():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

def test_simple_question():
    """Test simple question endpoint"""
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"question": "What is the admission rate for MIT?"}
    )
    assert response.status_code == 200
    assert 'answer' in response.json()
    assert len(response.json()['answer']) > 0

def test_school_comparison():
    """Test school comparison endpoint"""
    response = requests.post(
        f"{BASE_URL}/compare",
        json={
            "schools": ["MIT", "Stanford"],
            "criteria": ["admission rate"]
        }
    )
    assert response.status_code == 200
    assert 'comparison' in response.json()

def test_personalized_counseling():
    """Test personalized counseling endpoint"""
    response = requests.post(
        f"{BASE_URL}/counseling",
        json={
            "student_profile": {
                "gpa": 3.9,
                "sat": 1520,
                "background": "first-generation",
                "interests": "engineering"
            },
            "schools": ["MIT", "Stanford"],
            "question": "What are my chances?"
        }
    )
    assert response.status_code == 200
    assert 'advice' in response.json()

def test_admission_info():
    """Test admission info endpoint"""
    response = requests.get(f"{BASE_URL}/admission/Harvard")
    assert response.status_code == 200
    assert 'info' in response.json()
```

#### **4.2 Run Tests**

```bash
# Install pytest
pip install pytest

# Run tests
pytest tests/test_model_integration.py -v
```

---

### **Phase 5: Deployment** ⏳

#### **5.1 Docker Deployment (Recommended)**

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Copy model files
COPY models/fine_tuned_model-f16.gguf /models/
COPY models/Modelfile /models/

# Create Ollama model
RUN ollama create collegeadvisor:latest -f /models/Modelfile

# Expose ports
EXPOSE 5000 11434

# Start script
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
```

Create `start.sh`:

```bash
#!/bin/bash

# Start Ollama in background
ollama serve &

# Wait for Ollama to be ready
sleep 5

# Start API
python app.py
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  collegeadvisor-api:
    build: .
    ports:
      - "5000:5000"
      - "11434:11434"
    environment:
      - OLLAMA_BASE_URL=http://localhost:11434
      - OLLAMA_MODEL=collegeadvisor:latest
    volumes:
      - ./models:/models
    restart: unless-stopped
```

#### **5.2 Deploy**

```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f

# Test
curl http://localhost:5000/api/v1/health
```

---

### **Phase 6: Monitoring & Optimization** ⏳

#### **6.1 Add Logging**

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log all requests
@app.before_request
def log_request():
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")

# Log all responses
@app.after_request
def log_response(response):
    logger.info(f"Response: {response.status_code}")
    return response
```

#### **6.2 Add Metrics**

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'Request duration')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

#### **6.3 Add Rate Limiting**

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/v1/ask', methods=['POST'])
@limiter.limit("10 per minute")
def ask():
    # ... endpoint code
    pass
```

---

## 📋 **COMPLETE INTEGRATION CHECKLIST**

### **Setup Phase**
- [ ] Install Ollama on production server
- [ ] Transfer model files (fine_tuned_model-f16.gguf, Modelfile)
- [ ] Create Ollama model: `ollama create collegeadvisor:latest`
- [ ] Verify model: `ollama list | grep collegeadvisor`
- [ ] Start Ollama service

### **Integration Phase**
- [ ] Copy `college_advisor_api.py` to your repo
- [ ] Install dependencies: `pip install requests flask flask-cors`
- [ ] Add API endpoints (ask, compare, counseling, admission, health)
- [ ] Configure environment variables (.env file)
- [ ] Create configuration file (config.py)

### **Testing Phase**
- [ ] Create test suite (test_model_integration.py)
- [ ] Run health check test
- [ ] Run simple question test
- [ ] Run comparison test
- [ ] Run personalized counseling test
- [ ] Verify all tests pass

### **Deployment Phase**
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Build Docker image
- [ ] Deploy container
- [ ] Verify deployment with health check

### **Monitoring Phase**
- [ ] Add logging
- [ ] Add metrics (Prometheus)
- [ ] Add rate limiting
- [ ] Set up alerts
- [ ] Monitor performance

---

## 🎯 **EXPECTED RESULTS**

After completing integration, you should have:

✅ **Working API Endpoints:**
- `POST /api/v1/ask` - Simple Q&A
- `POST /api/v1/compare` - School comparisons
- `POST /api/v1/counseling` - Personalized advice
- `GET /api/v1/admission/<school>` - Admission info
- `GET /api/v1/health` - Health check

✅ **Performance:**
- Response time: 0.2-5 seconds
- Throughput: 10-20 requests/minute
- Uptime: 99.9%

✅ **Features:**
- Personalized counseling advice
- Complex analytical questions
- School comparisons
- Admission statistics
- Financial aid information

---

## 📞 **SUPPORT**

If you encounter issues during integration:

1. **Check Ollama status:** `ollama list`
2. **Check logs:** `docker-compose logs -f`
3. **Test model directly:** `ollama run collegeadvisor:latest "test"`
4. **Verify API:** `curl http://localhost:5000/api/v1/health`

**Reference Documentation:**
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `PRODUCTION_READY_REPORT.md` - Production readiness details
- `college_advisor_api.py` - API client documentation

---

**The model is ready for integration! Follow this checklist and you'll have a production-ready AI-powered college advisor API.** 🚀


