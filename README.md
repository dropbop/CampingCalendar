# Camping Coordinator App

A simple web app for Jack, Payton, Nick, and Alyssa to coordinate camping dates for May-August 2025.

Built with Flask (Python), Neon (Postgres), and deployed on Vercel.

## Features

* Displays calendars for May, June, July, August 2025.
* Allows selection of user (Jack, Payton, Nick, Alyssa).
* Allows selection of preference ("Prefer Not", "No", "Clear").
* Clicking a date marks it with the selected preference for the selected user.
* Shows the current preferences of all users on the calendar.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd your-camping-coordinator
    ```
2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up Neon Database:**
    * Create a free Neon account and project/database.
    * Get the connection string (URL looks like `postgres://user:password@host.neon.tech/dbname?sslmode=require`).
    * Run the SQL command below in Neon's SQL editor to create the table.
5.  **Configure Environment:**
    * Create a `.env` file in the project root.
    * Add your Neon `DATABASE_URL` to the `.env` file:
        ```
        DATABASE_URL=postgres://user:password@host.neon.tech/dbname?sslmode=require
        ```
    * **IMPORTANT:** Add `.env` to your `.gitignore` file if it's not already there.
6.  **Run Locally:**
    ```bash
    flask run
    # or python api/index.py
    ```
    Access the app at `http://127.0.0.1:5000` (or the port Flask indicates).

7.  **Deploy to Vercel:**
    * Push your code to GitHub/GitLab/Bitbucket.
    * Connect your repository to a new Vercel project.
    * Vercel should detect the Flask framework.
    * Add your `DATABASE_URL` as an Environment Variable in the Vercel project settings.
    * Deploy!

## Database Schema (PostgreSQL)

```sql
CREATE TABLE preferences (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL CHECK (user_name IN ('Jack', 'Payton', 'Nick', 'Alyssa')),
    event_date DATE NOT NULL,
    preference_type VARCHAR(20) NOT NULL CHECK (preference_type IN ('prefer_not', 'no')), -- 'prefer_not' or 'no'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Ensures only one 'prefer_not' or 'no' entry per user per date
    UNIQUE(user_name, event_date)
);