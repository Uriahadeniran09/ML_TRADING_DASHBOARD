# 🏗️ ML Trading Dashboard - Architecture Overview

**Created:** November 17, 2025  
**Status:** Backend complete, Frontend not started

---

## 📊 Current State Summary

### ✅ **What's Working**
- **Docker Environment**: PostgreSQL, Redis, FastAPI all running
- **Database**: 50 stocks × ~500 records = 24,950 price records (Oct-Nov 2024 data)
- **Redis Cache**: Caching API responses (5 min for prices, 1 hour for history)
- **REST API**: 4 working endpoints for stock data
- **Scripts**: Database population and daily update scripts ready

### 🚧 **What's Not Built Yet**
- Frontend (React/Next.js - not started)
- ML prediction models (service file exists, but empty)
- Portfolio optimization (service file exists, but empty)
- Risk calculation (service file exists, but empty)

---

## 🗂️ File Organization & Purpose

### **`config/stocks.py`** - STATIC STOCK LIST (In-Memory)
```
Purpose: Master list of 50 tracked stocks
Type: Python list (NOT database)
Contains: Symbol, name, sector for each stock
Used by: API validation, scripts to know which stocks to fetch
Why exists: Fast lookups without database queries
```

### **`database/crud.py`** - DATABASE OPERATIONS (PostgreSQL)
```
Purpose: Save/read data TO/FROM database
Functions:
  - get_or_create_stock() - Ensure stock exists in DB
  - add_stock_price() - Insert/update price records
  - add_prediction() - Save ML predictions
  - get_stock_prices() - Query historical data
  - get_latest_price() - Get most recent price
Used by: Scripts (populate_db.py, daily_update.py)
NOT used by: API yet (API uses config/stocks.py instead)
```

**🤔 Are they redundant?**
- **NO!** `stocks.py` = validation list | `crud.py` = database storage
- **Current issue**: API reads from `stocks.py` but should read from database
- **Future fix**: Make API use `crud.py` to get stock list from database

---

## 🔄 Data Flow

### **1. Initial Setup (One-time)**
```
populate_db.py (script)
    ↓
Uses config/stocks.py (get list of 50 symbols)
    ↓
Calls services/data_fetcher.py (Polygon.io API)
    ↓
Saves via database/crud.py
    ↓
PostgreSQL database (24,950 records)
```

### **2. Daily Updates (Automated)**
```
daily_update.py (cron job)
    ↓
Checks database for latest date
    ↓
Fetches new data from Polygon.io
    ↓
Saves new records via crud.py
```

### **3. API Requests (User/Frontend)**
```
Frontend (not built yet)
    ↓
GET /api/stocks
    ↓
main.py (FastAPI endpoint)
    ↓
config/stocks.py (returns static list)
    ↓
Response to user
```

**🔴 Problem:** API doesn't use database! It uses the static list.  
**✅ Solution:** Update API to query database via crud.py

---

## 📁 Complete File Map

### **Backend Services**
| File | Purpose | Status | Used By |
|------|---------|--------|---------|
| `services/data_fetcher.py` | Fetch from Polygon.io API | ✅ Working | Scripts, API |
| `services/cache.py` | Redis caching layer | ✅ Working | API (could be used more) |
| `services/ml_predictor.py` | ML price predictions | ❌ Not implemented | Future API endpoint |
| `services/portfolio_optimizer.py` | Portfolio optimization | ❌ Not implemented | Future API endpoint |
| `services/risk_calculator.py` | Risk metrics (VaR, Sharpe) | ❌ Not implemented | Future API endpoint |

### **Database Layer**
| File | Purpose | Status | Used By |
|------|---------|--------|---------|
| `database/models.py` | PostgreSQL table definitions | ✅ Working | SQLAlchemy ORM |
| `database/crud.py` | Database CRUD operations | ✅ Working | Scripts (not API yet) |
| `database/db.py` | Database connection setup | ✅ Working | Everything |

### **Configuration**
| File | Purpose | Status | Used By |
|------|---------|--------|---------|
| `config/stocks.py` | Static list of 50 stocks | ✅ Working | API, Scripts |

### **API Endpoints**
| File | Purpose | Status | Used By |
|------|---------|--------|---------|
| `app/main.py` | FastAPI REST endpoints | ✅ 4 endpoints working | Frontend (future) |

### **Scripts**
| File | Purpose | Status | Run When |
|------|---------|--------|----------|
| `scripts/populate_db.py` | Initial 5-year data load | ✅ Working | Once (setup) |
| `scripts/daily_update.py` | Add latest trading day | ✅ Working | Daily (cron) |

---

## 🌐 API Endpoints

### **Current Endpoints (Working)**
```
GET /                              - Health check
GET /api/stocks                    - List all 50 stocks
GET /api/stocks?sector=Technology  - Filter by sector
GET /api/sectors                   - List all sectors
GET /api/price?symbol=AAPL         - Current price (Polygon API)
GET /api/history?symbol=AAPL&period=1mo - Historical data
```

**Note:** These endpoints use `config/stocks.py` (static list), NOT the database.

### **Future Endpoints (TODO)**
```
GET /api/prediction?symbol=AAPL    - ML price prediction
GET /api/risk?symbol=AAPL          - Risk metrics
POST /api/portfolio/optimize       - Portfolio optimization
```

---

## 🗃️ Database Schema

### **Tables in PostgreSQL**
```sql
stocks (50 records)
├── id (primary key)
├── symbol (AAPL, MSFT, etc.)
├── name (Apple Inc., Microsoft Corporation)
└── created_at

stock_prices (24,950 records)
├── id (primary key)
├── stock_id (foreign key → stocks.id)
├── date (trading day)
├── open, high, low, close (prices)
├── volume
└── created_at

predictions (0 records - not implemented yet)
├── id (primary key)
├── stock_id (foreign key → stocks.id)
├── prediction_date (when we made prediction)
├── target_date (date we're predicting)
├── predicted_price
├── actual_price (filled in later)
├── model_name (LSTM, RandomForest)
└── confidence
```

---

## 🔧 Redis Cache

### **Cache Keys**
```
price:current:{symbol}     - TTL: 5 minutes
history:{symbol}:{period}  - TTL: 1 hour
```

### **Why Cache?**
- Polygon.io free tier: 5 requests/minute
- Reduces API calls for repeated requests
- Speeds up response time

---

## 🚀 Next Steps (What to Build)

### **1. Fix API to Use Database**
Currently API uses `config/stocks.py`. Should query database for stock list.

### **2. Build Frontend**
- React/Next.js dashboard
- Charts (Chart.js or Recharts)
- Stock list, price display, historical charts

### **3. Implement ML Predictions**
- Train LSTM model on historical data
- Create `predict_price()` function in `ml_predictor.py`
- Add `GET /api/prediction` endpoint

### **4. Implement Risk Metrics**
- Calculate volatility, VaR, Sharpe ratio
- Create `calculate_risk()` function
- Add `GET /api/risk` endpoint

### **5. Implement Portfolio Optimizer**
- Modern Portfolio Theory (efficient frontier)
- Create `optimize_portfolio()` function
- Add `POST /api/portfolio/optimize` endpoint

---

## 🐳 Docker Services

```yaml
services:
  postgres:    Port 5432 - Database storage
  redis:       Port 6379 - Caching layer
  backend:     Port 8000 - FastAPI application
```

---

## 📝 Summary for Your Understanding

**CONFUSION CLARIFIED:**

1. **stocks.py vs crud.py** - NOT redundant!
   - `stocks.py` = Static list for validation (fast, in-memory)
   - `crud.py` = Database operations (persistent storage)
   - Currently API uses `stocks.py`, scripts use `crud.py`

2. **Why API doesn't use database yet?**
   - Quick start approach: static list faster to implement
   - Database has the data, but API endpoints not updated yet
   - **TODO:** Update API to query database instead of static list

3. **What you've built:**
   - ✅ Database with 50 stocks, 24,950 price records
   - ✅ Redis caching working
   - ✅ API endpoints returning stock data
   - ✅ Scripts to populate and update database

4. **What's missing:**
   - ❌ Frontend (no React app yet)
   - ❌ ML models (files exist but empty)
   - ❌ API doesn't query database (uses static list)

---

**You're in great shape! The backend infrastructure is solid. Now you can:**
1. Start building the frontend
2. Connect API to database
3. Build the ML prediction models
