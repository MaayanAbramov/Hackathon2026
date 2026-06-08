# Hackathon 2026 Solution🚀🚀🚀

## Prerequisites
* Python 3.10+
* Git

## Local Setup

**1. Clone the repository:**

    git clone https://github.com/MaayanAbramov/Hackathon2026.git
    cd Hackathon2026

**2. Create and activate a virtual environment:**

* **Linux / Mac:**

    python3 -m venv venv
    source venv/bin/activate

* **Windows (Git Bash / CMD):**

    python -m venv venv
    venv\Scripts\activate

**3. Install dependencies:**

    pip install -r requirements.txt

**4. Install the pre-commit hook (Required):**

    pre-commit install --hook-type pre-push

**5. Configure secrets:**
Create a `.env` file in the root directory and add the database connection string:

    DATABASE_URL="your_database_connection_string"

## Run the Server

Make sure your virtual environment is active, then run:

    python Server.py
