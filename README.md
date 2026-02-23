# OneBigHub
Ramoy, Lorenzo <br />
Lopez, Chrisdale <br />
De Luna, Matthew <br />
Sulay, Danielle <br />
Felipe, Luis

# One Big Hub

## Setup Instructions

### 1. Clone the repo
git clone <your-repo-url>
cd one-big-hub

### 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Set up environment variables
cp .env.example .env
# Open .env and fill in your PostgreSQL credentials and secret key

### 5. Create the PostgreSQL database
psql -U your_postgres_username
CREATE DATABASE one_big_hub;
\q

### 6. Run migrations
python manage.py migrate

### 7. Run the server
python manage.py runserver