"""
Test suite for MedSync backend application
"""
import pytest
import httpx
from app import app

BASE_URL = "http://localhost:8000"

@pytest.fixture
async def client():
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as ac:
        yield ac

@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "MedSync"

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "rag_enabled" in data
    assert "database_connected" in data

@pytest.mark.asyncio
async def test_get_hospitals(client):
    """Test getting hospitals list"""
    response = await client.get("/api/hospitals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "name" in data[0]
        assert "address" in data[0]

@pytest.mark.asyncio
async def test_login_with_valid_credentials(client):
    """Test login with valid credentials"""
    response = await client.post("/api/login", json={
        "email": "user@medsync.com",
        "password": "user123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "role" in data

@pytest.mark.asyncio
async def test_login_with_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = await client.post("/api/login", json={
        "email": "user@medsync.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_register_new_user(client):
    """Test user registration"""
    import random
    random_email = f"test{random.randint(1000, 9999)}@test.com"
    
    response = await client.post("/api/register", json={
        "email": random_email,
        "password": "test123",
        "confirm_password": "test123",
        "role": "user"
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert data["email"] == random_email

@pytest.mark.asyncio
async def test_register_password_mismatch(client):
    """Test registration with password mismatch"""
    response = await client.post("/api/register", json={
        "email": "test@test.com",
        "password": "test123",
        "confirm_password": "test456",
        "role": "user"
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_symptom_analysis(client):
    """Test AI symptom analysis"""
    response = await client.post("/api/ai/symptom-analysis", json={
        "symptoms": "chest pain and shortness of breath",
        "include_rag": True
    })
    assert response.status_code == 200
    data = response.json()
    assert "possible_conditions" in data
    assert "recommended_department" in data
    assert "severity" in data

@pytest.mark.asyncio
async def test_rag_search(client):
    """Test RAG search functionality"""
    response = await client.post("/api/ai/search", json={
        "query": "heart attack symptoms",
        "top_k": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "query" in data

@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    """Test accessing protected endpoint without token"""
    response = await client.get("/api/management/hospitals")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_endpoint_with_token(client):
    """Test accessing protected endpoint with valid token"""
    # First login to get token
    login_response = await client.post("/api/login", json={
        "email": "hospital@medsync.com",
        "password": "hospital123"
    })
    token = login_response.json()["access_token"]
    
    # Use token to access protected endpoint
    response = await client.get("/api/management/hospitals", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_hospital_details(client):
    """Test getting hospital details"""
    response = await client.get("/api/hospitals/1/doctors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_hospital_departments(client):
    """Test getting hospital departments"""
    response = await client.get("/api/hospitals/1/departments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])