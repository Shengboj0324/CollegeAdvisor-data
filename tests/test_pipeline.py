"""Comprehensive tests for the data pipeline."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from college_advisor_data.models import Document, DocumentType
from college_advisor_data.ingestion.pipeline import IngestionPipeline
from college_advisor_data.ingestion.loaders import CSVLoader, JSONLoader
from college_advisor_data.preprocessing.preprocessor import TextPreprocessor
from college_advisor_data.preprocessing.chunker import TextChunker
from college_advisor_data.embedding.embedder import EmbeddingService


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing."""
    return """id,name,location,description,website,gpa_requirement
1,"MIT","Cambridge, MA","Leading technology university","https://mit.edu",4.0
2,"Stanford","Stanford, CA","Innovation and entrepreneurship","https://stanford.edu",3.9
3,"Harvard","Cambridge, MA","Oldest university in US","https://harvard.edu",3.95"""


@pytest.fixture
def sample_json_data():
    """Create sample JSON data for testing."""
    return {
        "documents": [
            {
                "id": "summer_1",
                "title": "MIT Summer Research",
                "content": "Intensive research program for high school students",
                "metadata": {
                    "duration": "6 weeks",
                    "age_range": "16-18",
                    "cost": "Free"
                }
            },
            {
                "id": "summer_2", 
                "title": "Stanford AI Camp",
                "content": "Learn artificial intelligence and machine learning",
                "metadata": {
                    "duration": "2 weeks",
                    "age_range": "15-17",
                    "cost": "$2000"
                }
            }
        ]
    }


@pytest.fixture
def temp_csv_file(sample_csv_data):
    """Create temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(sample_csv_data)
        return Path(f.name)


@pytest.fixture
def temp_json_file(sample_json_data):
    """Create temporary JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_json_data, f)
        return Path(f.name)


class TestDataLoaders:
    """Test data loading functionality."""
    
    def test_csv_loader(self, temp_csv_file):
        """Test CSV loader functionality."""
        loader = CSVLoader(DocumentType.UNIVERSITY)
        documents = list(loader.load(temp_csv_file))
        
        assert len(documents) == 3
        assert documents[0].title == "MIT"
        assert documents[0].doc_type == DocumentType.UNIVERSITY
        assert "Cambridge, MA" in documents[0].metadata.get('location', '')
        
        # Clean up
        temp_csv_file.unlink()
    
    def test_json_loader(self, temp_json_file):
        """Test JSON loader functionality."""
        loader = JSONLoader(DocumentType.SUMMER_PROGRAM)
        documents = list(loader.load(temp_json_file))
        
        assert len(documents) == 2
        assert documents[0].title == "MIT Summer Research"
        assert documents[0].doc_type == DocumentType.SUMMER_PROGRAM
        assert "research program" in documents[0].content.lower()
        
        # Clean up
        temp_json_file.unlink()


class TestTextPreprocessing:
    """Test text preprocessing functionality."""
    
    def test_basic_cleaning(self):
        """Test basic text cleaning."""
        preprocessor = TextPreprocessor()
        
        # Test with messy text
        messy_text = """
        <p>This is a test with HTML tags!</p>
        Visit https://example.com for more info.
        Contact us at test@example.com
        Multiple    spaces   and   tabs.
        """
        
        document = Document(
            id="test_1",
            title="Test Document",
            content=messy_text,
            doc_type=DocumentType.UNIVERSITY
        )
        
        result = preprocessor.preprocess(document)
        
        # Check that HTML tags are removed
        assert "<p>" not in result.cleaned_text
        assert "</p>" not in result.cleaned_text
        
        # Check that URLs and emails are removed from cleaned text
        assert "https://example.com" not in result.cleaned_text
        assert "test@example.com" not in result.cleaned_text
        
        # Check that excessive whitespace is normalized
        assert "Multiple    spaces" not in result.cleaned_text
    
    def test_entity_extraction(self):
        """Test entity extraction."""
        preprocessor = TextPreprocessor()
        
        text_with_entities = """
        MIT requires a minimum GPA of 3.8 and SAT score of 1500.
        Tuition is $53,790 per year. Contact admissions@mit.edu.
        Visit https://mit.edu for more information.
        """
        
        document = Document(
            id="test_2",
            title="MIT Info",
            content=text_with_entities,
            doc_type=DocumentType.UNIVERSITY
        )
        
        result = preprocessor.preprocess(document)
        
        # Check entity extraction
        assert 'gpa' in result.entities
        assert 'sat_score' in result.entities
        assert 'tuition' in result.entities
        assert 'email' in result.entities
        assert 'website' in result.entities
    
    def test_keyword_extraction(self):
        """Test keyword extraction."""
        preprocessor = TextPreprocessor()
        
        text = """
        Computer science program at MIT focuses on algorithms, data structures,
        artificial intelligence, and machine learning. Students learn programming
        in Python, Java, and C++. The curriculum includes software engineering,
        database systems, and computer networks.
        """
        
        document = Document(
            id="test_3",
            title="CS Program",
            content=text,
            doc_type=DocumentType.PROGRAM
        )
        
        result = preprocessor.preprocess(document)
        
        # Check that relevant keywords are extracted
        keywords_lower = [kw.lower() for kw in result.keywords]
        assert any('computer' in kw for kw in keywords_lower)
        assert any('programming' in kw for kw in keywords_lower)
        assert any('algorithm' in kw for kw in keywords_lower)


class TestTextChunking:
    """Test text chunking functionality."""
    
    def test_basic_chunking(self):
        """Test basic chunking functionality."""
        chunker = TextChunker(chunk_size=100, overlap_size=20)
        
        # Create a long document
        long_text = " ".join([f"This is sentence {i} in a long document." for i in range(50)])
        
        document = Document(
            id="test_chunk",
            title="Long Document",
            content=long_text,
            doc_type=DocumentType.UNIVERSITY
        )
        
        chunks = chunker.chunk_document(document)
        
        assert len(chunks) > 1
        assert all(chunk.token_count <= chunker.max_chunk_size for chunk in chunks)
        assert all(chunk.token_count >= chunker.min_chunk_size for chunk in chunks[:-1])  # Last chunk might be smaller
    
    def test_chunk_metadata(self):
        """Test chunk metadata creation."""
        chunker = TextChunker()
        
        document = Document(
            id="test_meta",
            title="Test Document",
            content="This is a test document for metadata testing.",
            doc_type=DocumentType.PROGRAM,
            metadata={
                "university_name": "MIT",
                "program_name": "Computer Science",
                "location": "Cambridge, MA"
            }
        )
        
        chunks = chunker.chunk_document(document)
        
        assert len(chunks) >= 1
        chunk = chunks[0]
        assert chunk.metadata.document_id == "test_meta"
        assert chunk.metadata.doc_type == DocumentType.PROGRAM
        assert chunk.metadata.university_name == "MIT"
        assert chunk.metadata.chunk_index == 0


class TestEmbeddingService:
    """Test embedding service functionality."""
    
    @patch('college_advisor_data.embedding.sentence_transformer_embedder.SentenceTransformer')
    def test_sentence_transformer_embedder(self, mock_st):
        """Test sentence transformer embedder."""
        # Mock the SentenceTransformer
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_model.get_sentence_embedding_dimension.return_value = 3
        mock_st.return_value = mock_model
        
        from college_advisor_data.embedding.sentence_transformer_embedder import SentenceTransformerEmbedder
        
        embedder = SentenceTransformerEmbedder("test-model")
        
        # Test single embedding
        embedding = embedder.embed_single("test text")
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]
        
        # Test batch embedding
        embeddings = embedder.embed_texts(["text1", "text2"])
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]
    
    def test_embedding_service_factory(self):
        """Test embedding service factory."""
        # Test with sentence transformers
        with patch('college_advisor_data.config.config') as mock_config:
            mock_config.embedding_provider = "sentence_transformers"
            mock_config.embedding_model = "test-model"
            
            service = EmbeddingService()
            assert service.provider == "sentence_transformers"
            assert service.model_name == "test-model"


class TestIntegration:
    """Integration tests for the complete pipeline."""
    
    @patch('college_advisor_data.storage.chroma_client.chromadb')
    @patch('college_advisor_data.embedding.sentence_transformer_embedder.SentenceTransformer')
    def test_complete_pipeline(self, mock_st, mock_chromadb, temp_csv_file):
        """Test complete pipeline from CSV to ChromaDB."""
        # Mock SentenceTransformer
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model
        
        # Mock ChromaDB
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_collection.return_value = mock_collection
        mock_client.create_collection.return_value = mock_collection
        mock_client.heartbeat.return_value = True
        mock_chromadb.HttpClient.return_value = mock_client
        
        # Run pipeline
        pipeline = IngestionPipeline()
        stats = pipeline.ingest_from_file(temp_csv_file, "csv", "university", save_processed=False)
        
        # Verify results
        assert stats.total_documents == 3
        assert stats.total_chunks > 0
        assert stats.total_embeddings > 0
        assert len(stats.errors) == 0
        
        # Verify ChromaDB was called
        mock_collection.upsert.assert_called()
        
        # Clean up
        temp_csv_file.unlink()
    
    def test_pipeline_health_check(self):
        """Test pipeline health check."""
        with patch('college_advisor_data.embedding.embedder.EmbeddingService') as mock_embedding:
            with patch('college_advisor_data.storage.chroma_client.ChromaDBClient') as mock_chroma:
                # Mock healthy responses
                mock_embedding.return_value.health_check.return_value = {"status": "healthy"}
                mock_chroma.return_value.get_collection_count.return_value = 100
                
                pipeline = IngestionPipeline()
                health = pipeline.health_check()
                
                assert health["pipeline"] == "healthy"
                assert "embedding" in health["components"]
                assert "chromadb" in health["components"]


if __name__ == "__main__":
    pytest.main([__file__])
