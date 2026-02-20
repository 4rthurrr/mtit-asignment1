# FastAPI Auth Module

A simple authentication module using Python FastAPI, SQLite, and JWT.

## Features
- User registration (`POST /auth/register`)
- JWT authentication (`POST /auth/login`)
- Current user profile (`GET /auth/me`)
- Password hashing with bcrypt
- 15-minute token expiry

## Setup and Running

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Access API Documentation**
   Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.

## Project Structure
```
auth-service/
├── requirements.txt
├── README.md
└── app/
    ├── __init__.py
    ├── auth.py
    ├── database.py
    ├── main.py
    ├── models.py
    └── schemas.py
```
