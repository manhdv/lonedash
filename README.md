# Lonedash

Self-hosted portfolio tracker built with Django. Track your investments, trades, and performance over time — fully local, no vendor lock-in, no analytics junk.

## Features

- User accounts (Django auth)  
- Manually log trades (buy/sell)  
- Track performance by stock or total portfolio  
- Support for per-user price API keys (e.g. Alpha Vantage, Finnhub)  
- Clean, minimal dashboard  
- No third-party dependencies — host it yourself

## Tech Stack

- Django 5  
- PostgreSQL  
- TailwindCSS or Bootstrap  
- Docker + docker-compose (optional)

## Local Setup (with PostgreSQL)

Requirements: Python 3.10+, PostgreSQL installed

1. Clone repo and set up virtualenv:

```bash
git clone https://github.com/manhdv/lonedash.git
cd lonedash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Create PostgreSQL database and user:

```bash
psql -U postgres
CREATE DATABASE lonedash;
CREATE USER lonedash WITH PASSWORD 'lonedash';
GRANT ALL PRIVILEGES ON DATABASE lonedash TO lonedash;
GRANT ALL ON SCHEMA public TO lonedash;
```
3. Create a .env file:

```bash
HOST=http://localhost:8000
DEBUG=True
SECRET_KEY=replace-this-with-something-secret
POSTGRES_DB=lonedash
POSTGRES_USER=lonedash
POSTGRES_PASSWORD=lonedash
POSTGRES_HOST=localhost

SUPERUSER_NAME=admin
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=admin
```

4. Apply migrations and create admin user:

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Run the server:

```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000)


## Docker Setup

1. Create a .env file with the following content:

```bash
HOST=http://localhost:8000
DEBUG=True
SECRET_KEY=replace-this-with-something-secret
POSTGRES_DB=lonedash
POSTGRES_USER=lonedash
POSTGRES_PASSWORD=lonedash
POSTGRES_HOST=db

SUPERUSER_NAME=admin
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_PASSWORD=admin
```

2. Run docker compose:

```bash
docker-compose up --build
```

The app will auto-create the database and superuser on first boot.

VVisit the app at [localhost:8000](http://localhost:8000)

## Notes

-FIFO cost basis used for gain/loss
-Price fetching API keys are per-user
-Not yet supported: stock splits, advance report.
-Not yet support background task

## License
MIT — use it, fork it, strip it, break it. Your data, your rules.