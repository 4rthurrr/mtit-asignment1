import sys
import os
# Add the project directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_me_failure():
    # 1. Register a user
    print("Step 1: Registering user 'testuser1'...")
    reg_response = client.post("/auth/register", json={
        "username": "testuser1",
        "email": "test@example.com",
        "password": "strongpassword123"
    })
    # If user already exists (from previous run), we just ignore and continue
    if reg_response.status_code in [201, 400]:
        print("Step 1 ready.")
    else:
        print(f"Registration status: {reg_response.status_code}")

    # 2. Login to get token
    print("Step 2: Logging in to get token...")
    login_response = client.post("/auth/login", data={
        "username": "testuser1",
        "password": "strongpassword123"
    })
    token = login_response.json().get("access_token")
    if token:
        print(f"Token obtained: {token[:20]}...")
    else:
        print("Failed to get token!")
        return

    # 3. Call /auth/me (THIS SHOULD FAIL WITH 401)
    print("Step 3: Calling /auth/me with the token...")
    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    
    print(f"Response status: {me_response.status_code}")
    print(f"Response body: {me_response.json()}")

    if me_response.status_code == 401:
        print("\n[RESULT] Bug reproduced! Token verification failed (401) as expected due to secret key mismatch.")
    else:
        print("\n[RESULT] Bug NOT reproduced. The token was surprisingly verified. Status code: " + str(me_response.status_code))

if __name__ == "__main__":
    test_auth_me_failure()
