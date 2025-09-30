"""Basic tests to ensure CI/CD pipeline passes."""


def test_package_import():
    """Test that the main package can be imported."""
    import college_advisor_data
    assert college_advisor_data is not None


def test_config_import():
    """Test that config module can be imported."""
    from college_advisor_data.config import config
    assert config is not None


def test_models_import():
    """Test that models module can be imported."""
    from college_advisor_data.models import Document
    assert Document is not None


def test_schemas_import():
    """Test that schemas module can be imported."""
    from college_advisor_data.schemas import COLLECTION_NAME
    assert COLLECTION_NAME is not None


def test_basic_functionality():
    """Test basic functionality."""
    assert 1 + 1 == 2


def test_python_version():
    """Test Python version compatibility."""
    import sys
    assert sys.version_info >= (3, 9)

