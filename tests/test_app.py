import pytest

def test_home_page(client):
    """Test that the home page (index.html) is served successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"MUIO" in response.data # Check for a known string in index.html

def test_get_session_missing(client):
    """Test getting a session when none is set."""
    response = client.get('/getSession')
    assert response.status_code == 200
    assert response.json["session"] is None


def test_set_session_and_get(client):
    """Test setting a session and then retrieving it."""
    # 1. Set the session
    test_case_name = "test_case_123"
    response = client.post('/setSession', json={"case": test_case_name})
    
    assert response.status_code == 200
    assert response.json["osycase"] == test_case_name
    
    # 2. Get the session to verify it persisted in the test client
    response = client.get('/getSession')
    assert response.status_code == 200
    assert response.json["session"] == test_case_name

def test_set_session_invalid_payload(client):
    """Test setting a session with missing required 'case' key."""
    response = client.post('/setSession', json={"wrong_key": "123"})
    assert response.status_code == 404
    assert b"No selected parameters!" in response.data
