import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from main import app, Base, get_db
from models import User, Master, Service, Schedule, Booking
from database import engine

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestAuth:
    """Test authentication endpoints"""

    def test_register_user(self):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
                "business_name": "Test Business",
                "specialization": "Hair Styling",
            },
        )
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"

    def test_register_duplicate_email(self):
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "testpassword123",
                "business_name": "Test Business",
                "specialization": "Hair Styling",
            },
        )

        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "testpassword123",
                "business_name": "Another Business",
                "specialization": "Nails",
            },
        )
        assert response.status_code == 400

    def test_login(self):
        # Register first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "testpassword123",
                "business_name": "Test Business",
                "specialization": "Hair Styling",
            },
        )

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self):
        # Register first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "testpassword123",
                "business_name": "Test Business",
                "specialization": "Hair Styling",
            },
        )

        # Try login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpass@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401


class TestServices:
    """Test service endpoints"""

    @pytest.fixture
    def auth_token(self):
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "services@example.com",
                "password": "testpassword123",
                "business_name": "Test Business",
                "specialization": "Hair Styling",
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "services@example.com", "password": "testpassword123"},
        )
        return response.json()["access_token"]

    def test_create_service(self, auth_token):
        response = client.post(
            "/api/v1/services",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Haircut",
                "description": "Professional haircut",
                "duration_minutes": 30,
                "price": 50.0,
            },
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Haircut"

    def test_list_services(self, auth_token):
        # Create a service first
        client.post(
            "/api/v1/services",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Haircut",
                "description": "Professional haircut",
                "duration_minutes": 30,
                "price": 50.0,
            },
        )

        # List services
        response = client.get(
            "/api/v1/services",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert len(response.json()) > 0


class TestPublicBooking:
    """Test public booking endpoints"""

    def test_get_master_info(self):
        # Register master
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "master@example.com",
                "password": "testpassword123",
                "business_name": "Test Salon",
                "specialization": "Hair Styling",
            },
        )

        # Get master info by slug
        response = client.get("/api/v1/public/test-salon/info")
        assert response.status_code == 200
        assert response.json()["business_name"] == "Test Salon"

    def test_get_available_slots(self):
        # Register master and create service
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "slots@example.com",
                "password": "testpassword123",
                "business_name": "Test Salon",
                "specialization": "Hair Styling",
            },
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "slots@example.com", "password": "testpassword123"},
        )
        token = login_response.json()["access_token"]

        # Create service
        service_response = client.post(
            "/api/v1/services",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Haircut",
                "description": "Professional haircut",
                "duration_minutes": 30,
                "price": 50.0,
            },
        )
        service_id = service_response.json()["id"]

        # Get available slots
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = client.get(
            f"/api/v1/public/test-salon/slots",
            params={"date": tomorrow, "service_id": service_id},
        )
        assert response.status_code == 200


class TestHealth:
    """Test health check endpoint"""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
