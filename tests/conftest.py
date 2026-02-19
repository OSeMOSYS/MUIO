import pytest
import os
import sys

# Ensure the API directory is in the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'API')))

from app import app as flask_app

@pytest.fixture
def app():
    """Yields a configured Flask application for testing."""
    flask_app.config.update({
        "TESTING": True,
    })
    
    yield flask_app
    
@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
