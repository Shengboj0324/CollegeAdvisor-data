# ✅ TODO List for collegeadvisor-api Repository

**Model:** collegeadvisor:latest (Ready for Integration)  
**Date:** October 26, 2025  
**Status:** Model trained and exported - Ready for API integration

---

## 📦 **STEP 1: TRANSFER ARTIFACTS**

### **Files to Copy from CollegeAdvisor-data to collegeadvisor-api**

```bash
# Required files (2.2GB total)
✅ gguf_models/gguf/fine_tuned_model-f16.gguf  (2.2GB) - The AI model
✅ Modelfile                                    (1KB)  - Ollama configuration

# Recommended files
✅ college_advisor_api.py                       (10KB) - Python client with helpers
✅ DEPLOYMENT_GUIDE.md                          (20KB) - Complete deployment guide
✅ INTEGRATION_GUIDE_FOR_API_REPO.md            (15KB) - This integration guide
```

**Transfer Command:**
```bash
# From CollegeAdvisor-data directory
scp gguf_models/gguf/fine_tuned_model-f16.gguf user@server:/path/to/collegeadvisor-api/models/
scp Modelfile user@server:/path/to/collegeadvisor-api/models/
scp college_advisor_api.py user@server:/path/to/collegeadvisor-api/
scp DEPLOYMENT_GUIDE.md user@server:/path/to/collegeadvisor-api/docs/
scp INTEGRATION_GUIDE_FOR_API_REPO.md user@server:/path/to/collegeadvisor-api/docs/
```

---

## 🔧 **STEP 2: ENVIRONMENT SETUP**

### **2.1 Install Ollama**
```bash
# On your production server
curl -fsSL https://ollama.com/install.sh | sh
ollama --version  # Verify installation
```

### **2.2 Create Ollama Model**
```bash
cd /path/to/collegeadvisor-api/models
ollama create collegeadvisor:latest -f Modelfile

# Verify
ollama list | grep collegeadvisor
# Expected output: collegeadvisor:latest    787ac59f3d77    2.2 GB
```

### **2.3 Start Ollama Service**
```bash
# Option 1: Foreground (testing)
ollama serve

# Option 2: Background service (production)
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```

---

## 💻 **STEP 3: CODE INTEGRATION**

### **3.1 Install Dependencies**
```bash
# In collegeadvisor-api repository
pip install requests          # For Ollama API calls
pip install flask flask-cors  # If using Flask
pip install python-dotenv     # For environment variables
```

### **3.2 Create Configuration File**

**File: `config.py`**
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
```

### **3.3 Create Environment File**

**File: `.env`**
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=collegeadvisor:latest
OLLAMA_TIMEOUT=120
API_PORT=5000
API_HOST=0.0.0.0
```

### **3.4 Add API Endpoints**

**File: `app.py` or your main API file**

Add these endpoints:

```python
from college_advisor_api import CollegeAdvisorClient
from flask import Flask, request, jsonify
import time

app = Flask(__name__)
client = CollegeAdvisorClient()

# 1. Simple Q&A
@app.route('/api/v1/ask', methods=['POST'])
def ask():
    question = request.json.get('question')
    start_time = time.time()
    answer = client.ask(question)
    response_time = time.time() - start_time
    
    return jsonify({
        'answer': answer,
        'response_time': response_time
    })

# 2. School Comparison
@app.route('/api/v1/compare', methods=['POST'])
def compare_schools():
    schools = request.json.get('schools', [])
    criteria = request.json.get('criteria')
    comparison = client.compare_schools(schools, criteria)
    
    return jsonify({
        'comparison': comparison,
        'schools': schools
    })

# 3. Personalized Counseling (NEW - handles complex questions)
@app.route('/api/v1/counseling', methods=['POST'])
def personalized_counseling():
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

# 4. Admission Info
@app.route('/api/v1/admission/<school>', methods=['GET'])
def get_admission_info(school):
    info = client.get_admission_info(school)
    return jsonify({'school': school, 'info': info})

# 5. Health Check
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    try:
        response = requests.get(f"{client.base_url}/api/tags", timeout=5)
        response.raise_for_status()
        return jsonify({
            'status': 'healthy',
            'model': client.model,
            'ollama_url': client.base_url
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## 🧪 **STEP 4: TESTING**

### **4.1 Create Test File**

**File: `tests/test_model_integration.py`**
```python
import pytest
import requests

BASE_URL = "http://localhost:5000/api/v1"

def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

def test_simple_question():
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"question": "What is the admission rate for MIT?"}
    )
    assert response.status_code == 200
    assert 'answer' in response.json()

def test_personalized_counseling():
    response = requests.post(
        f"{BASE_URL}/counseling",
        json={
            "student_profile": {
                "gpa": 3.9,
                "sat": 1520,
                "background": "first-generation, low-income",
                "interests": "mechanical engineering",
                "activities": ["robotics club", "community volunteer"]
            },
            "schools": ["MIT", "Stanford", "Caltech"],
            "question": "What are my chances and what should I emphasize?"
        }
    )
    assert response.status_code == 200
    assert 'advice' in response.json()
```

### **4.2 Run Tests**
```bash
pip install pytest
pytest tests/test_model_integration.py -v
```

---

## 🐳 **STEP 5: DOCKER DEPLOYMENT (OPTIONAL)**

### **5.1 Create Dockerfile**

**File: `Dockerfile`**
```dockerfile
FROM python:3.9-slim

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Copy model files
COPY models/fine_tuned_model-f16.gguf /models/
COPY models/Modelfile /models/

# Create Ollama model
RUN ollama create collegeadvisor:latest -f /models/Modelfile

EXPOSE 5000 11434

# Start script
COPY start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]
```

### **5.2 Create Start Script**

**File: `start.sh`**
```bash
#!/bin/bash
ollama serve &
sleep 5
python app.py
```

### **5.3 Create Docker Compose**

**File: `docker-compose.yml`**
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

### **5.4 Deploy**
```bash
docker-compose up -d
docker-compose logs -f
curl http://localhost:5000/api/v1/health
```

---

## 📊 **STEP 6: MONITORING & OPTIMIZATION**

### **6.1 Add Logging**
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
```

### **6.2 Add Rate Limiting**
```bash
pip install flask-limiter
```

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
```

### **6.3 Add Caching (Optional)**
```bash
pip install flask-caching
```

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/v1/ask', methods=['POST'])
@cache.cached(timeout=300, query_string=True)
def ask():
    # ... endpoint code
```

---

## ✅ **COMPLETE CHECKLIST**

### **Phase 1: Setup** ⏳
- [ ] Transfer model files to collegeadvisor-api repository
- [ ] Install Ollama on production server
- [ ] Create Ollama model: `ollama create collegeadvisor:latest`
- [ ] Verify model: `ollama list | grep collegeadvisor`
- [ ] Start Ollama service

### **Phase 2: Integration** ⏳
- [ ] Copy `college_advisor_api.py` to repository
- [ ] Install dependencies: `pip install requests flask flask-cors python-dotenv`
- [ ] Create `config.py` configuration file
- [ ] Create `.env` environment file
- [ ] Add 5 API endpoints (ask, compare, counseling, admission, health)

### **Phase 3: Testing** ⏳
- [ ] Create test suite: `tests/test_model_integration.py`
- [ ] Install pytest: `pip install pytest`
- [ ] Run tests: `pytest tests/test_model_integration.py -v`
- [ ] Verify all tests pass

### **Phase 4: Deployment** ⏳
- [ ] Create `Dockerfile` (if using Docker)
- [ ] Create `docker-compose.yml` (if using Docker)
- [ ] Create `start.sh` script
- [ ] Build and deploy: `docker-compose up -d`
- [ ] Verify deployment: `curl http://localhost:5000/api/v1/health`

### **Phase 5: Monitoring** ⏳
- [ ] Add logging configuration
- [ ] Add rate limiting: `pip install flask-limiter`
- [ ] Add caching (optional): `pip install flask-caching`
- [ ] Set up monitoring dashboard
- [ ] Configure alerts

---

## 🎯 **EXPECTED API ENDPOINTS**

After integration, your API should have:

```
POST   /api/v1/ask                  - Simple Q&A
POST   /api/v1/compare              - School comparisons
POST   /api/v1/counseling           - Personalized counseling (NEW!)
GET    /api/v1/admission/<school>   - Admission info
GET    /api/v1/health               - Health check
```

---

## 📝 **EXAMPLE API USAGE**

### **1. Simple Question**
```bash
curl -X POST http://localhost:5000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the admission rate for Harvard?"}'
```

### **2. Personalized Counseling**
```bash
curl -X POST http://localhost:5000/api/v1/counseling \
  -H "Content-Type: application/json" \
  -d '{
    "student_profile": {
      "gpa": 3.9,
      "sat": 1520,
      "background": "first-generation, low-income",
      "interests": "mechanical engineering",
      "activities": ["robotics club", "community volunteer"]
    },
    "schools": ["MIT", "Stanford", "Caltech"],
    "question": "What are my chances and what should I emphasize?"
  }'
```

### **3. School Comparison**
```bash
curl -X POST http://localhost:5000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{
    "schools": ["MIT", "Stanford", "Caltech"],
    "criteria": ["admission rate", "engineering programs"]
  }'
```

---

## 🚀 **SUMMARY**

**What you need to do in collegeadvisor-api repository:**

1. ✅ **Transfer 2 files** (model + Modelfile)
2. ✅ **Install Ollama** and create model
3. ✅ **Add 5 API endpoints** (copy from integration guide)
4. ✅ **Create config files** (.env, config.py)
5. ✅ **Test integration** (pytest)
6. ✅ **Deploy** (Docker or direct)
7. ✅ **Monitor** (logging, rate limiting)

**Time estimate:** 2-4 hours for complete integration

**The model is ready and waiting for you! Just follow this checklist.** 🎉


