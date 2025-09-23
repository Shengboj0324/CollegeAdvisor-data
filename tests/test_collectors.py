"""
Tests for data collectors.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))

from collectors.base_collector import BaseCollector, CollectorConfig, CollectionResult
from collectors.government import CollegeScorecardCollector


class TestCollectorConfig:
    """Test collector configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CollectorConfig()
        
        assert config.requests_per_second == 1.0
        assert config.requests_per_minute == 60
        assert config.max_retries == 3
        assert config.cache_enabled is True
        assert config.output_format == "json"
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = CollectorConfig(
            requests_per_second=2.0,
            max_retries=5,
            cache_enabled=False,
            api_key="test_key"
        )
        
        assert config.requests_per_second == 2.0
        assert config.max_retries == 5
        assert config.cache_enabled is False
        assert config.api_key == "test_key"


class TestCollectionResult:
    """Test collection result tracking."""
    
    def test_result_initialization(self):
        """Test result initialization."""
        result = CollectionResult(
            collector_name="TestCollector",
            source_url="https://example.com"
        )
        
        assert result.collector_name == "TestCollector"
        assert result.source_url == "https://example.com"
        assert result.total_records == 0
        assert result.successful_records == 0
        assert result.failed_records == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = CollectionResult(
            collector_name="TestCollector",
            source_url="https://example.com"
        )
        
        # Test with no records
        assert result.success_rate == 0.0
        
        # Test with some records
        result.total_records = 100
        result.successful_records = 80
        assert result.success_rate == 0.8
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        result = CollectionResult(
            collector_name="TestCollector",
            source_url="https://example.com"
        )
        
        # Test with no end time
        assert result.duration is None
        
        # Test with end time
        result.end_time = result.start_time
        assert result.duration.total_seconds() == 0


class TestCollegeScorecardCollector:
    """Test College Scorecard API collector."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return CollectorConfig(
            api_key="test_api_key",
            cache_enabled=False,  # Disable cache for testing
            requests_per_second=10.0  # Faster for testing
        )
    
    @pytest.fixture
    def collector(self, config):
        """Create test collector."""
        return CollegeScorecardCollector(config)
    
    def test_initialization(self, collector):
        """Test collector initialization."""
        assert collector.api_key == "test_api_key"
        assert collector.BASE_URL == "https://api.data.gov/ed/collegescorecard/v1/schools"
        assert len(collector.FIELD_GROUPS) > 0
    
    def test_source_info(self, collector):
        """Test source information."""
        info = collector.get_source_info()
        
        assert info["name"] == "College Scorecard"
        assert info["provider"] == "U.S. Department of Education"
        assert "api_url" in info
        assert "data_categories" in info
        assert "total_fields" in info
        assert info["total_fields"] > 0
    
    def test_field_groups(self, collector):
        """Test field group definitions."""
        field_groups = collector.FIELD_GROUPS
        
        # Check that all expected groups exist
        expected_groups = ["basic", "academics", "admissions", "student_body", "costs", "aid", "completion", "earnings"]
        for group in expected_groups:
            assert group in field_groups
            assert len(field_groups[group]) > 0
        
        # Check that fields are strings
        for group, fields in field_groups.items():
            for field in fields:
                assert isinstance(field, str)
                assert len(field) > 0
    
    @patch('collectors.government.CollegeScorecardCollector._collect_year_data')
    def test_collect_basic(self, mock_collect_year, collector):
        """Test basic collection functionality."""
        # Mock the year data collection
        mock_data = [
            {"id": 1, "school.name": "Test University 1"},
            {"id": 2, "school.name": "Test University 2"}
        ]
        # Return tuple (data, api_calls) as expected by the method
        mock_collect_year.return_value = (mock_data, 1)
        
        # Run collection
        result = collector.collect(years=[2022], field_groups=["basic"])
        
        # Verify results
        assert result.collector_name == "CollegeScorecardCollector"
        assert result.total_records == 2
        assert result.successful_records == 2
        assert result.failed_records == 0
        assert len(result.errors) == 0
        
        # Verify metadata
        assert result.metadata["years_collected"] == [2022]
        assert result.metadata["field_groups"] == ["basic"]
        assert result.metadata["total_fields"] > 0
    
    @patch('requests.Session.get')
    def test_collect_year_data_success(self, mock_get, collector):
        """Test successful year data collection."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [
                {"id": 1, "school.name": "Test University 1"},
                {"id": 2, "school.name": "Test University 2"}
            ],
            "metadata": {"total": 2}
        }
        mock_get.return_value = mock_response
        
        # Test data collection
        fields = ["id", "school.name"]
        data, api_calls = collector._collect_year_data(2022, fields, None, 100)

        # Verify results
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["school.name"] == "Test University 2"
        assert api_calls == 1
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "api_key" in call_args[1]["params"]
        assert call_args[1]["params"]["fields"] == "id,school.name"
    
    @patch('requests.Session.get')
    def test_collect_year_data_pagination(self, mock_get, collector):
        """Test pagination in year data collection."""
        # Mock multiple pages
        responses = [
            {
                "results": [{"id": 1}, {"id": 2}],
                "metadata": {"total": 4}
            },
            {
                "results": [{"id": 3}, {"id": 4}],
                "metadata": {"total": 4}
            },
            {
                "results": [],
                "metadata": {"total": 4}
            }
        ]
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = responses
        mock_get.return_value = mock_response
        
        # Test data collection with small page size
        fields = ["id"]
        data, api_calls = collector._collect_year_data(2022, fields, None, 2)

        # Verify results
        assert len(data) == 4
        assert api_calls == 2  # Two API calls for pagination (stops when total reached)
        assert mock_get.call_count == 2  # Two API calls for pagination
    
    @patch('requests.Session.get')
    def test_collect_year_data_with_states_filter(self, mock_get, collector):
        """Test year data collection with states filter."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [{"id": 1, "school.state": "CA"}],
            "metadata": {"total": 1}
        }
        mock_get.return_value = mock_response
        
        # Test with states filter
        fields = ["id", "school.state"]
        states = ["CA", "NY"]
        data, api_calls = collector._collect_year_data(2022, fields, states, 100)
        
        # Verify API call includes state filter
        call_args = mock_get.call_args
        assert call_args[1]["params"]["school.state"] == "CA,NY"
    
    @patch('requests.Session.get')
    def test_collect_year_data_api_error(self, mock_get, collector):
        """Test handling of API errors."""
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        # Test data collection
        fields = ["id"]
        data, api_calls = collector._collect_year_data(2022, fields, None, 100)

        # Should return empty list on error
        assert len(data) == 0
        assert api_calls == 0
    
    def test_save_data(self, collector, tmp_path):
        """Test data saving functionality."""
        # Test data
        test_data = [
            {"id": 1, "school.name": "Test University 1"},
            {"id": 2, "school.name": "Test University 2"}
        ]
        
        # Save data
        output_path = tmp_path / "test_output.json"
        collector._save_data(test_data, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify file content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert "metadata" in saved_data
        assert "data" in saved_data
        assert saved_data["metadata"]["total_records"] == 2
        assert len(saved_data["data"]) == 2
        assert saved_data["data"][0]["id"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
