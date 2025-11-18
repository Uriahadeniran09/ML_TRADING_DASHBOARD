# 📚 Quick File Reference Guide

> **One-line descriptions of every file in the project**

---

## 🎯 Configuration Files

| File | Description |
|------|-------------|
| `docker-compose.yml` | Defines 3 services: PostgreSQL, Redis, FastAPI backend |
| `backend/Dockerfile` | Container setup for FastAPI app |
| `backend/requirements.txt` | Python dependencies (FastAPI, SQLAlchemy, Redis, etc.) |

---

## 🗂️ Config / Static Data

| File | What It Does |
|------|-------------|
| `backend/config/stocks.py` | **Static list of 50 stocks (symbol, name, sector) - NO database calls, just Python list for validation** |

---

## 🗄️ Database Layer

| File | What It Does |
|------|-------------|
| `backend/database/models.py` | **Defines 3 PostgreSQL tables: Stock, StockPrice, Prediction** |
| `backend/database/db.py` | **Database connection setup (SQLAlchemy engine, session factory)** |
| `backend/database/crud.py` | **Database CRUD functions: save prices, get prices, create stocks - used by SCRIPTS** |

---

## 🌐 API / Web Server

| File | What It Does |
|------|-------------|
| `backend/app/main.py` | **FastAPI app with 4 endpoints: /stocks, /sectors, /price, /history - uses config/stocks.py NOT database** |

---

## 🔧 Services / Business Logic

| File | What It Does |
|------|-------------|
| `backend/services/data_fetcher.py` | **Fetches live stock data from Polygon.io API (current price + historical data)** |
| `backend/services/cache.py` | **Redis caching layer: stores API responses to reduce Polygon.io calls** |
| `backend/services/ml_predictor.py` | **ML price predictions - NOT IMPLEMENTED YET** |
| `backend/services/portfolio_optimizer.py` | **Portfolio optimization - NOT IMPLEMENTED YET** |
| `backend/services/risk_calculator.py` | **Risk metrics (VaR, Sharpe ratio) - NOT IMPLEMENTED YET** |

---

## 🤖 Scripts / Automation

| File | What It Does |
|------|-------------|
| `backend/scripts/populate_db.py` | **ONE-TIME: Fetch 5 years data for all 50 stocks, save to database via crud.py** |
| `backend/scripts/daily_update.py` | **DAILY CRON: Check for new trading day, add latest prices if missing** |
| `backend/scripts/setup_cron.sh` | **Sets up cron job to run daily_update.py automatically** |

---

## 🎨 Frontend (Not Built Yet)

| File | What It Does |
|------|-------------|
| `frontend/README.md` | **Placeholder - React/Next.js app will go here** |

---

## 📖 Documentation

| File | What It Does |
|------|-------------|
| `README.md` | **Main project README (overview, setup instructions, features)** |
| `ARCHITECTURE.md` | **Detailed architecture explanation (this was just created!)** |
| `FILE_GUIDE.md` | **This file - quick reference for all files** |
| `idea.txt` | **Original project ideas / notes** |

---

## 🔑 Key Relationships

```
Frontend (future)
    ↓
app/main.py (FastAPI endpoints)
    ↓
┌─────────────────┬──────────────────┐
│                 │                  │
config/stocks.py  services/*.py      database/crud.py
(static list)     (business logic)   (DB operations)
                  ↓                  ↓
            Polygon.io API      PostgreSQL DB
                  ↓
              Redis Cache
```

---

## 🎯 Which File Do I Need?

### **To add a new stock to track:**
→ Edit `config/stocks.py` (add to AVAILABLE_STOCKS list)

### **To change how data is fetched from Polygon.io:**
→ Edit `services/data_fetcher.py`

### **To add a new API endpoint:**
→ Edit `app/main.py`

### **To change database schema:**
→ Edit `database/models.py`

### **To change how data is saved to database:**
→ Edit `database/crud.py`

### **To change cache duration:**
→ Edit `services/cache.py`

### **To add ML prediction logic:**
→ Edit `services/ml_predictor.py`

### **To populate database with historical data:**
→ Run `docker exec ml_trading_backend python scripts/populate_db.py`

### **To manually update today's prices:**
→ Run `docker exec ml_trading_backend python scripts/daily_update.py`

---

## 📊 Database vs Config - IMPORTANT!

| | `config/stocks.py` | `database/crud.py` |
|---|---|---|
| **Type** | Static Python list | Database operations |
| **Data** | 50 stock symbols, names, sectors | OHLCV price data (24,950 records) |
| **Purpose** | Validation & reference | Persistent storage |
| **Used by** | API endpoints, scripts | Scripts only (API should use it!) |
| **Speed** | Instant (in-memory) | Slower (query needed) |
| **Persistent** | No (code only) | Yes (survives restarts) |

**Current State:** API uses `stocks.py`, scripts use `crud.py`  
**Future Fix:** API should also query database via `crud.py`

---

## 🚦 File Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully implemented and working |
| 🚧 | Partially implemented |
| ❌ | Not implemented (placeholder) |
| 🔄 | Needs refactoring |

### Status by File

```
✅ config/stocks.py              - Static list working
✅ database/models.py            - Tables defined
✅ database/db.py                - Connection working
✅ database/crud.py              - CRUD functions working
🔄 app/main.py                   - Works but should use database
✅ services/data_fetcher.py      - API integration working
✅ services/cache.py             - Redis caching working
❌ services/ml_predictor.py      - Empty placeholder
❌ services/portfolio_optimizer.py - Empty placeholder
❌ services/risk_calculator.py   - Empty placeholder
✅ scripts/populate_db.py        - Data population working
✅ scripts/daily_update.py       - Update script working
❌ frontend/*                    - Not started
```

---

**Last Updated:** November 17, 2025
