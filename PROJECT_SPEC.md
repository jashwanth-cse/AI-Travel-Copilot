# AI Travel Copilot - Project Specification (MVP v1)

## 1. Project Goal

Build an AI-powered travel planning platform that:

* Collects live travel data from APIs
* Performs ETL processing
* Stores cleaned data in SQLite
* Generates personalized travel recommendations
* Uses GenAI to create itineraries
* Provides an AI travel assistant

This project demonstrates:

* Data Engineering
* ETL Pipelines
* Full Stack Development
* GenAI Integration
* Recommendation Systems

---

# 2. Locked Technology Stack

## Backend

* Python 3.12+
* FastAPI
* SQLAlchemy ORM
* SQLite
* Pydantic
* Requests / HTTPX
* Python Logging

## Frontend

* React
* TypeScript
* Vite
* TailwindCSS
* Axios

## AI

* Groq API
* Model:

  * llama-3.3-70b-versatile

## APIs

### Travel Data

Preferred order:

1. Geoapify Places API
2. OpenTripMap API (optional fallback)

### Weather

* OpenWeather API

### Geocoding

* Geoapify Geocoding

---

# 3. Engineering Principles

## Code Quality Rules

All backend code MUST:

* Use type hints
* Include docstrings
* Include structured comments
* Include debug logging
* Follow modular architecture
* Avoid hardcoded values

---

# 4. Logging Standard

Every service should have logging.

Example:

```python
logger.info("Fetching attractions for city=%s", city)
logger.debug("Raw API response=%s", response.json())
logger.warning("Missing rating for place=%s", place_name)
logger.error("Weather API failed: %s", error)
```

Log levels:

* DEBUG
* INFO
* WARNING
* ERROR

---

# 5. Backend Folder Structure

backend/
│
├── app/
│
├── api/
│   ├── trip_routes.py
│   ├── ai_routes.py
│   └── health_routes.py
│
├── services/
│   ├── geocoding_service.py
│   ├── places_service.py
│   ├── weather_service.py
│   ├── etl_service.py
│   ├── recommendation_service.py
│   └── ai_service.py
│
├── models/
│   ├── attraction.py
│   ├── restaurant.py
│   ├── trip.py
│   ├── weather.py
│   └── itinerary.py
│
├── schemas/
│   ├── request_schema.py
│   └── response_schema.py
│
├── db/
│   ├── database.py
│   └── init_db.py
│
├── utils/
│   ├── logger.py
│   ├── constants.py
│   └── helpers.py
│
├── tests/
│
├── scripts/
│   ├── test_geocoding.py
│   ├── test_places.py
│   ├── test_weather.py
│   ├── test_etl.py
│   ├── test_recommendation.py
│   └── test_ai.py
│
├── main.py
├── .env
├── requirements.txt
└── travel.db

---

# 6. Database Schema

## trips

Stores user trip requests.

Fields:

* id
* destination
* days
* budget
* travelers
* food_preference
* senior_citizen
* created_at

---

## attractions

Stores tourist attractions.

Fields:

* id
* place_id
* name
* rating
* latitude
* longitude
* category
* city
* description

---

## restaurants

Stores restaurants.

Fields:

* id
* place_id
* name
* rating
* vegetarian
* price_level
* latitude
* longitude

---

## weather

Stores weather forecasts.

Fields:

* id
* city
* date
* temperature
* condition

---

## itineraries

Stores generated itineraries.

Fields:

* id
* trip_id
* generated_plan
* created_at

---

# 7. ETL Pipeline Design

## Extract

Fetch data from:

* Geoapify
* OpenWeather

---

## Transform

Cleaning rules:

* Remove duplicates
* Remove null names
* Convert ratings to float
* Normalize categories
* Validate coordinates

---

## Load

Store cleaned data in SQLite.

Use:

INSERT OR REPLACE

---

# 8. Recommendation Engine

Inputs:

* Budget
* Travelers
* Food preference
* Senior citizen mode

Rules:

### Senior Citizen

Avoid:

* Trekking
* Steep hills

Prefer:

* Lakes
* Gardens
* Parks

### Vegetarian

Prioritize vegetarian restaurants.

### Budget

Filter expensive options.

---

# 9. AI Itinerary Generation

Workflow:

User Input
↓
Fetch DB Data
↓
Filter Recommendations
↓
Fetch Weather
↓
Construct Prompt
↓
Call Groq API
↓
Store Itinerary
↓
Return Response

---

# 10. API Endpoints

GET /health

Returns server status.

---

POST /api/trips/generate

Input:

{
"destination": "Ooty",
"days": 3,
"budget": 15000,
"travelers": 2,
"food_preference": "vegetarian",
"senior_citizen": true
}

Returns:

* Attractions
* Restaurants
* Weather
* AI itinerary

---

POST /api/chat

Travel assistant endpoint.

---

# 11. Development Strategy

IMPORTANT:

Backend development happens before frontend.

Every module must be independently executable.

---

# 12. Script-by-Script Testing

## Step 1

test_geocoding.py

Input:

"Ooty"

Output:

latitude
longitude

---

## Step 2

test_places.py

Input:

lat/lon

Output:

list of attractions

---

## Step 3

test_weather.py

Output:

5-day forecast

---

## Step 4

test_etl.py

Verify:

API → Clean → SQLite

---

## Step 5

test_recommendation.py

Verify filtering logic.

---

## Step 6

test_ai.py

Verify Groq itinerary generation.

---

# 13. FastAPI Integration

After scripts work:

Expose APIs.

Never develop APIs before validating services.

---

# 14. Frontend Phase

Pages:

1. Home
2. Results

Components:

* Trip Form
* Weather Card
* Attraction Card
* Restaurant Card
* Itinerary Card
* Chat Widget

---

# 15. Future Scope

* PostgreSQL
* pgvector
* RAG
* Kafka
* Airflow
* Authentication
* Trip sharing

---

# 16. Codex Workflow

Codex MUST implement features in this exact order:

1. Project setup
2. Logging system
3. SQLite setup
4. Database models
5. Geocoding service
6. Places service
7. Weather service
8. ETL service
9. Recommendation service
10. AI service
11. Test scripts
12. FastAPI APIs
13. React frontend
14. Integration testing

Never skip steps.

Each step must be fully tested before proceeding.
