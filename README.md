# Cisco Threat Monitoring API (CFM API)

A high-performance, real-time threat monitoring and analysis API built with FastAPI. Processes network security events from Cisco eStreamer, performs real-time aggregation and geolocation enrichment, and provides REST and WebSocket interfaces for threat analytics and notifications.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-green)
![License](https://img.shields.io/badge/License-MIT-blue)

## Features

- **Real-Time Event Processing**: Stream-based architecture using Redis Streams for continuous threat monitoring
- **Event Aggregation**: Time-windowed aggregation with threat severity tracking and statistics
- **Geolocation Enrichment**: Automatic IP geolocation using MaxMind GeoLite2 database
- **WebSocket Support**: Real-time threat data streaming to connected clients
- **JWT Authentication**: Secure token-based API authentication with configurable TTL
- **Telegram Notifications**: Alert delivery with IP-based rate limiting
- **RESTful API**: Comprehensive endpoints for threat analytics, statistics, and event queries
- **Structured Logging**: Production-ready JSON logging with contextual information
- **High Performance**: Async-first design with uvloop for optimized event handling

## Prerequisites

- **Python**: 3.10 or higher
- **Redis**: 6.0 or higher (for stream processing and caching)
- **MaxMind GeoIP Database**: GeoLite2-City (included in repo)
- **Optional**: Telegram Bot (for notifications)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cisco-threat-api.git
cd cisco-threat-api
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example configuration and update with your settings:

```bash
cp .env.example .env
```

## Quick Start

### 1. Start Redis

```bash
redis-server
```

### 2. Run the Application

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

API documentation (interactive Swagger UI): `http://localhost:8000/docs`

## Architecture

### Event Processing Pipeline

```
Redis Stream → Stream Consumer → Event Enrichment
                                      ↓
                            Event Aggregation
                                      ↓
                    ┌─────────┬─────────┬─────────┐
                    ↓         ↓         ↓         ↓
              WebSocket    REST API  Telegram  Statistics Cache
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **StreamConsumer** | Reads events from Redis Streams with GeoIP enrichment |
| **ThreatAggregator** | Time-windowed event aggregation and statistics calculation |
| **ThreatService** | Business logic for analytics and filtering |
| **WebSocketManager** | Manages real-time client connections |
| **TelegramNotifier** | Sends alerts to Telegram with rate limiting |
| **GeoIPService** | Cached IP geolocation lookups |

## API Endpoints

### Authentication

```http
POST /api/v1/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your-password
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Health Checks

```http
GET /health
GET /health/ready
```

### Statistics

```http
# Live statistics snapshot
GET /api/v1/stats/live

# Top attacking IPs
GET /api/v1/stats/top-attackers?limit=10

# Attack type distribution
GET /api/v1/stats/attack-types

# Severity breakdown
GET /api/v1/stats/severity

# Geographic distribution
GET /api/v1/stats/geo

# Blocked vs allowed ratio
GET /api/v1/stats/blocked-ratio
```

### Events

```http
# List events with filters
GET /api/v1/events?severity=high&page=1&page_size=20
```

**Query Parameters:**
- `severity`: Filter by severity (low, medium, high, critical)
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 20)

### WebSocket

Real-time threat event streaming:

```javascript
// Connect with authentication token
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/connect?token=YOUR_JWT_TOKEN');

ws.onmessage = (event) => {
  const threat = JSON.parse(event.data);
  console.log('New threat:', threat);
};
```

**Event Format:**
```json
{
  "timestamp": "2026-05-21T10:30:45.123Z",
  "type": "network_threat",
  "title": "Suspicious Connection",
  "severity": "high",
  "protocol": "tcp",
  "src_ip": "192.168.1.100",
  "dst_ip": "203.0.113.45",
  "src_country": "US",
  "src_city": "New York",
  "blocked": true,
  "threat_score": 85
}
```

## Dependencies

### Core Framework
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server with uvloop support
- **Pydantic** - Data validation and serialization

### Data & Async
- **Redis** - Event streaming and caching
- **geoip2** - MaxMind database queries
- **httpx** - Async HTTP client

### Security & Auth
- **passlib** - Password hashing (bcrypt)
- **PyJWT** - JWT token handling

### Logging & Utils
- **structlog** - Structured logging
- **python-dotenv** - Environment configuration

## Security Considerations

1. **JWT Secret**: Change `SECRET_KEY` in production to a strong, random value
2. **HTTPS**: Deploy behind a reverse proxy (nginx) with SSL/TLS
3. **CORS**: Restrict `ALLOWED_ORIGINS` to trusted domains
4. **Rate Limiting**: Consider adding rate limiting middleware
5. **Redis**: Secure Redis with authentication and network isolation
6. **Logs**: Monitor structured logs for suspicious activities

##  Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY GeoLite2-City_* ./GeoLite2-City/
COPY .env .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Set `APP_ENV=production`
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Update `ALLOWED_ORIGINS` for your domain
- [ ] Configure Redis with authentication
- [ ] Enable Telegram notifications (optional)
- [ ] Set up log aggregation (Datadog, ELK, etc.)
- [ ] Configure health checks for monitoring
- [ ] Use a reverse proxy (nginx) for SSL/TLS
- [ ] Set appropriate resource limits and scaling policies

## Performance Tuning

- **Event Batch Size**: Increase `STREAM_BATCH_SIZE` for higher throughput (requires more memory)
- **Aggregation Window**: Adjust `AGGREGATION_WINDOW_SECONDS` for finer/coarser granularity
- **WebSocket Heartbeat**: Increase `WS_HEARTBEAT_INTERVAL` to reduce overhead
- **Redis Connections**: Tune `REDIS_MAX_CONNECTIONS` based on concurrent clients

## Troubleshooting

### Redis Connection Failed
```
Error: ConnectionRefusedError at 127.0.0.1:6379
```
**Solution**: Ensure Redis is running and accessible:
```bash
redisd return PzONG
```

### GeoIP Database Not Found
```
Error: FileNotFoundError: GeoLite2-City.mmdb
```
**Solution**: Ensure `GeoLite2-City_*/GeoLite2-City.mmdb` exists and path is correct

### JWT Token Expired
```
Error: Unauthorized - Token has expired
```
**Solution**: Get a new token via `/api/v1/login`

### WebSocket Connection Refused
```
Error: Failed to fetch - WebSocket is closed before the connection is established
```
**Solution**: Verify token is valid and add it to the connection query string

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! 


## Acknowledgments

- Cisco eStreamer for event source
- MaxMind for GeoLite2 database
- FastAPI community for the excellent framework
- Redis community for the streaming solution

---

**Last Updated**: May 2026  
**Status**: Production Ready
