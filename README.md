# SmartCampus AI

## Local setup (Windows)
1. Copy `.env.example` to `.env` and paste the Neon connection string (ask Member A).
2. Create the environment:
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
3. Test the database connection:
   python check_db.py
   You should see the PostgreSQL version and `vector` in the list.

## Database
Hosted on Neon (PostgreSQL 18 + pgvector). Web console: https://console.neon.tech