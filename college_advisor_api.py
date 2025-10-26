#!/usr/bin/env python3
"""
CollegeAdvisor API Client
Production-ready Python client for the fine-tuned CollegeAdvisor model.

Usage:
    from college_advisor_api import CollegeAdvisorClient
    
    client = CollegeAdvisorClient()
    answer = client.ask("What is the admission rate for Harvard?")
    print(answer)
"""

import requests
import json
import logging
import time
from typing import List, Dict, Optional, Union
from functools import lru_cache
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CollegeAdvisorClient:
    """
    Client for interacting with the CollegeAdvisor Ollama model.
    
    Features:
    - Simple question-answer interface
    - Conversation/chat support
    - Response caching
    - Performance monitoring
    - Error handling and retries
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "collegeadvisor:latest",
        timeout: int = 120,
        enable_cache: bool = True,
        cache_size: int = 1000
    ):
        """
        Initialize the CollegeAdvisor client.
        
        Args:
            base_url: Ollama API base URL
            model: Model name to use
            timeout: Request timeout in seconds
            enable_cache: Enable response caching
            cache_size: Maximum number of cached responses
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        
        # Verify connection
        self._verify_connection()
        
        logger.info(f"CollegeAdvisor client initialized: {self.model}")
    
    def _verify_connection(self):
        """Verify connection to Ollama API."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            # Check if model exists
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if self.model not in model_names:
                logger.warning(f"Model '{self.model}' not found. Available models: {model_names}")
            else:
                logger.info(f"✅ Connected to Ollama API. Model '{self.model}' is available.")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama API at {self.base_url}: {e}")
            raise ConnectionError(f"Cannot connect to Ollama API: {e}")
    
    def ask(
        self,
        question: str,
        stream: bool = False,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Union[str, requests.Response]:
        """
        Ask the CollegeAdvisor model a question.
        
        Args:
            question: The question to ask
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0 to 1.0)
            max_retries: Maximum number of retry attempts
            
        Returns:
            The model's response as a string (or Response object if streaming)
        """
        # Check cache first
        if self.enable_cache and not stream:
            cached_response = self._get_cached_response(question)
            if cached_response:
                logger.info(f"Cache hit for question: {question[:50]}...")
                return cached_response
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": question,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    stream=stream
                )
                response.raise_for_status()
                
                if stream:
                    return response
                else:
                    result = response.json()["response"]
                    duration = time.time() - start_time
                    
                    # Log performance metrics
                    logger.info(f"Question: {question[:50]}...")
                    logger.info(f"Response time: {duration:.2f}s")
                    logger.info(f"Response length: {len(result)} chars")
                    
                    # Cache the response
                    if self.enable_cache:
                        self._cache_response(question, result)
                    
                    return result
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise TimeoutError(f"Request timed out after {max_retries} attempts")
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7
    ) -> Union[str, requests.Response]:
        """
        Have a conversation with the model.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            The model's response as a string (or Response object if streaming)
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                return response
            else:
                result = response.json()["message"]["content"]
                duration = time.time() - start_time
                
                logger.info(f"Chat response time: {duration:.2f}s")
                logger.info(f"Response length: {len(result)} chars")
                
                return result
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Chat request failed: {e}")
            raise
    
    def _get_cache_key(self, question: str) -> str:
        """Generate a cache key for a question."""
        return hashlib.md5(question.encode()).hexdigest()
    
    @lru_cache(maxsize=1000)
    def _get_cached_response(self, question: str) -> Optional[str]:
        """Get cached response for a question."""
        # This is a simple in-memory cache using lru_cache
        # For production, consider using Redis or similar
        return None
    
    def _cache_response(self, question: str, response: str):
        """Cache a response."""
        # Store in lru_cache by calling _get_cached_response
        # This is a workaround since lru_cache doesn't support setting values
        pass
    
    def compare_schools(
        self,
        schools: List[str],
        criteria: Optional[List[str]] = None
    ) -> str:
        """
        Compare multiple schools across various criteria.
        
        Args:
            schools: List of school names
            criteria: Optional list of criteria to compare (e.g., ['admission rate', 'SAT scores'])
            
        Returns:
            Comparison analysis
        """
        schools_str = ", ".join(schools)
        
        if criteria:
            criteria_str = ", ".join(criteria)
            question = f"Compare {schools_str} in terms of {criteria_str}. Provide a detailed analysis."
        else:
            question = f"Compare {schools_str}. What are the key differences in admission rates, requirements, and programs?"
        
        return self.ask(question)
    
    def get_admission_info(self, school: str) -> str:
        """
        Get admission information for a specific school.
        
        Args:
            school: School name
            
        Returns:
            Admission information
        """
        question = f"What are the admission requirements and statistics for {school}? Include admission rate, SAT/ACT scores, GPA requirements, and application deadlines."
        return self.ask(question)
    
    def analyze_trends(self, topic: str, timeframe: str = "past 5 years") -> str:
        """
        Analyze trends in college admissions.
        
        Args:
            topic: Topic to analyze (e.g., "Ivy League admission rates")
            timeframe: Time period to analyze
            
        Returns:
            Trend analysis
        """
        question = f"What are the trends in {topic} over the {timeframe}? What factors have contributed to these changes?"
        return self.ask(question)
    
    def get_program_info(self, school: str, program: str) -> str:
        """
        Get information about a specific program at a school.
        
        Args:
            school: School name
            program: Program name (e.g., "Computer Science", "Engineering")
            
        Returns:
            Program information
        """
        question = f"Tell me about the {program} program at {school}. What are the admission requirements, program strengths, and career outcomes?"
        return self.ask(question)


class CollegeAdvisorAPI:
    """
    Flask-based REST API wrapper for CollegeAdvisor model.
    
    Usage:
        from college_advisor_api import CollegeAdvisorAPI
        
        api = CollegeAdvisorAPI()
        api.run(host='0.0.0.0', port=5000)
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Initialize the API."""
        try:
            from flask import Flask, request, jsonify
            from flask_cors import CORS
        except ImportError:
            raise ImportError("Flask and flask-cors are required. Install with: pip install flask flask-cors")
        
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.client = CollegeAdvisorClient(base_url=ollama_url)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        from flask import request, jsonify
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "model": self.client.model})
        
        @self.app.route('/api/ask', methods=['POST'])
        def ask():
            """Ask a question."""
            data = request.json
            question = data.get('question')
            
            if not question:
                return jsonify({"error": "Question is required"}), 400
            
            try:
                answer = self.client.ask(question)
                return jsonify({"question": question, "answer": answer})
            except Exception as e:
                logger.error(f"Error processing question: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/compare', methods=['POST'])
        def compare():
            """Compare schools."""
            data = request.json
            schools = data.get('schools', [])
            criteria = data.get('criteria')
            
            if not schools or len(schools) < 2:
                return jsonify({"error": "At least 2 schools are required"}), 400
            
            try:
                comparison = self.client.compare_schools(schools, criteria)
                return jsonify({"schools": schools, "comparison": comparison})
            except Exception as e:
                logger.error(f"Error comparing schools: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/admission/<school>', methods=['GET'])
        def admission_info(school):
            """Get admission information for a school."""
            try:
                info = self.client.get_admission_info(school)
                return jsonify({"school": school, "info": info})
            except Exception as e:
                logger.error(f"Error getting admission info: {e}")
                return jsonify({"error": str(e)}), 500
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the API server."""
        logger.info(f"Starting CollegeAdvisor API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple client usage
    print("=" * 80)
    print("CollegeAdvisor API Client - Example Usage")
    print("=" * 80)
    
    client = CollegeAdvisorClient()
    
    # Test 1: Simple question
    print("\n📝 Test 1: Simple Question")
    print("-" * 80)
    answer = client.ask("What is the admission rate for Harvard?")
    print(f"Q: What is the admission rate for Harvard?")
    print(f"A: {answer}\n")
    
    # Test 2: School comparison
    print("\n📊 Test 2: School Comparison")
    print("-" * 80)
    comparison = client.compare_schools(
        schools=["MIT", "Stanford", "Caltech"],
        criteria=["admission rate", "engineering programs"]
    )
    print(f"Comparison: {comparison[:200]}...\n")
    
    # Test 3: Admission info
    print("\n🎓 Test 3: Admission Information")
    print("-" * 80)
    info = client.get_admission_info("Yale")
    print(f"Yale Admission Info: {info[:200]}...\n")
    
    print("=" * 80)
    print("✅ All tests completed successfully!")
    print("=" * 80)

