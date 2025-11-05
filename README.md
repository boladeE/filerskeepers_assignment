# Web Crawling Project for Filers Keepers

A production-ready web crawling solution for books.toscrape.com with MongoDB storage, change detection, and RESTful API.

## Features

- **Async Web Crawling**: Fast, efficient crawling using httpx and BeautifulSoup
- **MongoDB Storage (Beanie ODM)**: Pydantic-first document models with indexes managed in code
- **Change Detection**: Automatic detection of new books and price/availability changes
- **Daily Scheduler**: Automated daily updates using APScheduler
- **RESTful API**: FastAPI-based API with authentication and rate limiting
- **Production Ready**: Comprehensive error handling, logging, and retry logic

## Project Structure

```
assessment/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── crawler/
│   │   ├── scraper.py      # Main web scraper
│   │   ├── models.py       # Pydantic models
│   │   └── storage.py      # MongoDB storage operations
│   ├── scheduler/
│   │   ├── scheduler.py    # APScheduler setup
│   │   ├── change_detector.py  # Change detection logic
│   │   └── reports.py      # Report generation
│   ├── api/
│   │   ├── auth.py         # API key authentication
│   │   ├── rate_limit.py   # Rate limiting middleware
│   │   └── routes/
│   │       ├── books.py    # Books API endpoints
│   │       ├── changes.py  # Changes API endpoints
│   │       └── auth.py     # Auth endpoints (API key management)
│   ├── database/
│   │   ├── mongodb.py      # MongoDB connection & Beanie initialization
│   │   ├── models.py       # Beanie (Pydantic) document models
│   │   └── schemas.py      # (No-op) Index creation placeholder (managed by Beanie)
│   └── utils/
│       ├── config.py       # Configuration management
│       └── logger.py       # Logging setup
├── tests/
│   ├── test_crawler.py
│   ├── test_api.py
│   └── test_scheduler.py
├── docker-compose.yml      # MongoDB service
├── pyproject.toml          # Dependencies
└── README.md
```

## Prerequisites

- Python 3.12+
- Docker and Docker Compose (for MongoDB)
- UV package manager (recommended) or pip

## Setup

### 1. Install Dependencies

Using UV (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=books_crawler

# API Configuration
API_SECRET_KEY=your-secret-key-change-in-production
API_RATE_LIMIT_PER_HOUR=100

# Crawler Configuration
BASE_URL=https://books.toscrape.com
MAX_RETRIES=3
RETRY_DELAY=1.0
REQUEST_TIMEOUT=30.0
MAX_CONCURRENT_REQUESTS=10

# Scheduler Configuration
SCHEDULER_TIMEZONE=UTC
SCHEDULER_DAILY_HOUR=2

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=crawler.log
```

### 3. Start MongoDB

Compose V2 (Docker CLI integrated) uses `docker compose` while the legacy Compose V1 uses `docker-compose`. Check which you have with `docker compose version` or `docker-compose version`, and use the matching command below.

```bash
# Compose V2
docker compose up -d
```

```bash
# Compose V1 (legacy)
docker-compose up -d
```

This will start MongoDB on `localhost:27017`.

### 4. Indexes

Indexes are defined in Beanie model Settings and initialized automatically when the app starts. No manual action required.

## Usage

### Running the Crawler

The crawler now starts automatically in the background when the API server starts (no separate script needed). It resumes from previously crawled URLs by default.

### Running the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using UV:
```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running the Scheduler

The scheduler runs automatically when the API server starts. It will:
- Run daily at the configured hour (default: 2 AM UTC)
- Detect new books and changes
- Generate daily reports
- Log alerts for significant changes

## API Documentation

### Authentication

All API endpoints require authentication via API key header:

```
X-API-Key: your-api-key-here
```

### Creating API Keys

Create an API key via the REST API:

```bash
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name":"test-key","description":"Test API key"}'
```

Response:

```json
{ "api_key": "fk_abc123..." }
```

### Endpoints

#### GET /books

Get books with filtering and pagination.

**Query Parameters:**
- `category` (optional): Filter by category
- `min_price` (optional): Minimum price
- `max_price` (optional): Maximum price
- `rating` (optional): Filter by rating (One, Two, Three, Four, Five)
- `sort_by` (optional): Sort by `rating`, `price`, or `reviews` (default: `rating`)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/books?category=Poetry&min_price=10&page=1&limit=10"
```

**Response:**
```json
{
  "books": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "pages": 10
  }
}
```

#### GET /books/{book_id}

Get book details by ID.

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/books/507f1f77bcf86cd799439011"
```

#### GET /changes

Get recent changes (new books, price changes, etc.).

**Query Parameters:**
- `date` (optional): Date in YYYY-MM-DD format
- `change_type` (optional): Filter by change type (`new_book`, `price`, `availability`, etc.)
- `limit` (optional): Maximum number of changes (default: 50, max: 200)

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/changes?date=2024-01-01&limit=20"
```

### Rate Limiting

Rate limiting is set to 100 requests per hour per API key. When exceeded, you'll receive a `429 Too Many Requests` response with a `Retry-After` header.

## MongoDB Schema

### Books Collection

```json
{
  "_id": ObjectId("..."),
  "name": "A Light in the Attic",
  "description": "It's hard to imagine a world without A Light in the Attic...",
  "category": "Poetry",
  "price_including_tax": 51.77,
  "price_excluding_tax": 51.77,
  "availability": "In stock (22 available)",
  "number_of_reviews": 51,
  "image_url": "http://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg",
  "rating": "Three",
  "source_url": "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "crawl_timestamp": ISODate("2024-01-01T00:00:00Z"),
  "status": "active",
  "content_hash": "abc123...",
  "raw_html": "<html>...</html>",
  "created_at": ISODate("2024-01-01T00:00:00Z")
}
```

**Indexes:**
- `source_url` (unique)
- `category`
- `price_including_tax`
- `rating`
- `number_of_reviews`
- `crawl_timestamp`

### Change Log Collection

```json
{
  "_id": ObjectId("..."),
  "book_id": ObjectId("..."),
  "change_type": "price",
  "old_value": "10.00",
  "new_value": "15.00",
  "book_url": "http://books.toscrape.com/catalogue/...",
  "timestamp": ISODate("2024-01-01T00:00:00Z")
}
```

**Indexes:**
- `timestamp`
- `book_id`
- `change_type`

### API Keys Collection

```json
{
  "_id": ObjectId("..."),
  "api_key": "fk_abc123...",
  "name": "test-key",
  "description": "Test API key",
  "is_active": true,
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "last_used": ISODate("2024-01-01T00:00:00Z")
}
```

**Indexes:**
- `api_key` (unique)
- `is_active`

## Daily Reports

Daily change reports are generated in the `reports/` directory in JSON or CSV format:

- `changes_report_YYYY-MM-DD.json`
- `changes_report_YYYY-MM-DD.csv`

Reports include:
- Summary of changes
- Detailed change log
- New books count
- Price changes count
- Availability changes count

## Testing

Run tests using pytest:

```bash
pytest tests/
```

Or with coverage:

```bash
pytest --cov=app tests/
```

## Logging

Logs are written to:
- Console (INFO level)
- File: `crawler.log` (DEBUG level)

Log levels can be configured via `LOG_LEVEL` environment variable.

## Error Handling

The crawler includes:
- Retry logic with exponential backoff
- Resume capability (continues from last successful crawl)
- Graceful error handling and logging
- Connection pooling for MongoDB

## Production Considerations

1. **Security**: Change default API keys and secrets
2. **MongoDB**: Use MongoDB Atlas or a production MongoDB instance
3. **Rate Limiting**: Adjust rate limits based on your needs
4. **CORS**: Configure CORS origins appropriately
5. **Monitoring**: Set up monitoring and alerting for production
6. **Backup**: Implement regular MongoDB backups
7. **Scaling**: Consider horizontal scaling for high load

## Troubleshooting

### MongoDB Connection Issues

Ensure MongoDB is running:
```bash
# Compose V2
docker compose ps
```

```bash
# Compose V1 (legacy)
docker-compose ps
```

Check MongoDB logs:
```bash
# Compose V2
docker compose logs mongodb
```

```bash
# Compose V1 (legacy)
docker-compose logs mongodb
```

### API Authentication Issues

Verify API keys exist in MongoDB:
```javascript
db.api_keys.find({is_active: true})
```

### Crawler Issues

Check logs:
```bash
tail -f crawler.log
```

## License

This project is part of the Filers Keepers assessment.

## Contact

For questions or issues, contact: sudipto@filerskeepers.co

