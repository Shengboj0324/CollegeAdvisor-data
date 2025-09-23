"""Advanced text preprocessing with normalization, cleaning, and entity extraction."""

import re
import logging
import unicodedata
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

from ..models import Document
from ..config import config

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')


@dataclass
class PreprocessingResult:
    """Result of text preprocessing."""
    cleaned_text: str
    keywords: List[str]
    entities: Dict[str, List[str]]
    statistics: Dict[str, int]


class TextPreprocessor:
    """Advanced text preprocessor with multiple cleaning and extraction capabilities."""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Academic and college-specific stop words
        self.academic_stop_words = {
            'university', 'college', 'school', 'program', 'course', 'student', 'students',
            'degree', 'bachelor', 'master', 'phd', 'undergraduate', 'graduate',
            'admission', 'application', 'requirement', 'requirements'
        }
        
        # Patterns for entity extraction
        self.patterns = {
            'gpa': re.compile(r'\b(?:gpa|grade point average)\s*:?\s*(\d+\.?\d*)\b', re.IGNORECASE),
            'sat_score': re.compile(r'\bsat\s*:?\s*(\d{3,4})\b', re.IGNORECASE),
            'act_score': re.compile(r'\bact\s*:?\s*(\d{1,2})\b', re.IGNORECASE),
            'tuition': re.compile(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'percentage': re.compile(r'(\d{1,3})%', re.IGNORECASE),
            'year': re.compile(r'\b(19|20)\d{2}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'website': re.compile(r'https?://[^\s]+|www\.[^\s]+', re.IGNORECASE)
        }
        
        # Subject area keywords
        self.subject_areas = {
            'computer_science': ['computer science', 'cs', 'programming', 'software', 'algorithms', 'data structures'],
            'engineering': ['engineering', 'mechanical', 'electrical', 'civil', 'chemical', 'aerospace'],
            'business': ['business', 'management', 'finance', 'economics', 'marketing', 'accounting'],
            'medicine': ['medicine', 'medical', 'health', 'biology', 'pre-med', 'healthcare'],
            'liberal_arts': ['liberal arts', 'humanities', 'literature', 'history', 'philosophy', 'art'],
            'science': ['physics', 'chemistry', 'biology', 'mathematics', 'statistics', 'research']
        }
    
    def preprocess(self, document: Document) -> PreprocessingResult:
        """Perform comprehensive text preprocessing."""
        text = document.content
        
        # Step 1: Basic cleaning
        cleaned_text = self._basic_cleaning(text)
        
        # Step 2: Extract entities
        entities = self._extract_entities(text)
        
        # Step 3: Extract keywords
        keywords = self._extract_keywords(cleaned_text)
        
        # Step 4: Add subject area tags
        subject_tags = self._identify_subject_areas(cleaned_text)
        keywords.extend(subject_tags)
        
        # Step 5: Calculate statistics
        statistics = self._calculate_statistics(text, cleaned_text)
        
        return PreprocessingResult(
            cleaned_text=cleaned_text,
            keywords=list(set(keywords)),  # Remove duplicates
            entities=entities,
            statistics=statistics
        )
    
    def _basic_cleaning(self, text: str) -> str:
        """Perform basic text cleaning and normalization."""
        # Unicode normalization
        text = unicodedata.normalize('NFKD', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs (but keep them in entities)
        text = re.sub(r'https?://[^\s]+|www\.[^\s]+', '', text, flags=re.IGNORECASE)
        
        # Remove email addresses (but keep them in entities)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{3,}', '...', text)
        
        # Clean up quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r"['']", "'", text)
        
        return text.strip()
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract structured entities from text."""
        entities = {}
        
        for entity_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                entities[entity_type] = list(set(matches))  # Remove duplicates
        
        return entities
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract important keywords using TF-IDF."""
        try:
            # Tokenize and clean
            tokens = word_tokenize(text.lower())
            
            # Filter tokens
            filtered_tokens = []
            for token in tokens:
                if (len(token) > 2 and 
                    token.isalpha() and 
                    token not in self.stop_words and 
                    token not in self.academic_stop_words):
                    filtered_tokens.append(self.lemmatizer.lemmatize(token))
            
            if not filtered_tokens:
                return []
            
            # Use TF-IDF for keyword extraction
            vectorizer = TfidfVectorizer(
                max_features=max_keywords,
                ngram_range=(1, 2),
                stop_words='english'
            )
            
            # Create a document from filtered tokens
            doc_text = ' '.join(filtered_tokens)
            
            try:
                tfidf_matrix = vectorizer.fit_transform([doc_text])
                feature_names = vectorizer.get_feature_names_out()
                scores = tfidf_matrix.toarray()[0]
                
                # Get top keywords
                keyword_scores = list(zip(feature_names, scores))
                keyword_scores.sort(key=lambda x: x[1], reverse=True)
                
                return [kw for kw, score in keyword_scores if score > 0]
            
            except ValueError:
                # Fallback to simple frequency-based extraction
                from collections import Counter
                word_freq = Counter(filtered_tokens)
                return [word for word, freq in word_freq.most_common(max_keywords)]
        
        except Exception as e:
            logger.warning(f"Error extracting keywords: {e}")
            return []
    
    def _identify_subject_areas(self, text: str) -> List[str]:
        """Identify subject areas mentioned in the text."""
        text_lower = text.lower()
        identified_areas = []
        
        for area, keywords in self.subject_areas.items():
            for keyword in keywords:
                if keyword in text_lower:
                    identified_areas.append(area)
                    break
        
        return identified_areas
    
    def _calculate_statistics(self, original_text: str, cleaned_text: str) -> Dict[str, int]:
        """Calculate text statistics."""
        sentences = sent_tokenize(original_text)
        words = word_tokenize(cleaned_text)
        
        return {
            'original_length': len(original_text),
            'cleaned_length': len(cleaned_text),
            'sentence_count': len(sentences),
            'word_count': len(words),
            'avg_sentence_length': len(words) // len(sentences) if sentences else 0,
            'unique_words': len(set(word.lower() for word in words if word.isalpha()))
        }
    
    def batch_preprocess(self, documents: List[Document]) -> List[PreprocessingResult]:
        """Process multiple documents efficiently."""
        results = []
        
        for doc in documents:
            try:
                result = self.preprocess(doc)
                results.append(result)
            except Exception as e:
                logger.error(f"Error preprocessing document {doc.id}: {e}")
                # Create empty result for failed documents
                results.append(PreprocessingResult(
                    cleaned_text=doc.content,
                    keywords=[],
                    entities={},
                    statistics={'error': str(e)}
                ))
        
        return results
