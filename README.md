# ML Trading Dashboard 📈

A full-stack ML-powered trading dashboard with real-time predictions, risk metrics, and portfolio optimization.

## 🚀 Features

- **Real-time Market Data**: Live stock prices from multiple data sources
- **ML Predictions**: LSTM/GRU price forecasting models
- **Risk Analytics**: Volatility, VaR, Sharpe ratio calculations
- **Portfolio Optimization**: Efficient frontier and optimal allocation
- **Interactive Dashboard**: Real-time charts and visualizations

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Relational database
- **Redis**: Caching and real-time data
- **TensorFlow/PyTorch**: ML model training
- **Pandas/NumPy**: Data processing

### Frontend (Coming Soon)
- **React/Next.js**: UI framework
- **Chart.js/D3.js**: Data visualization
- **TailwindCSS**: Styling

## 📦 Docker Setup

### Prerequisites
- Docker Desktop installed
- Docker Compose installed

### Quick Start

1. **Clone and navigate to the project**
   ```bash
   cd ML_trading_dashboard
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

3. **Build and start services**
   ```bash
   docker-compose up --build
   ```

4. **Access the API**
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

### Docker Commands

```bash
# Start services
docker-compose up

# Start in detached mode (background)
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Rebuild after code changes
docker-compose up --build

# Stop and remove volumes (fresh start)
docker-compose down -v
```

## 🔧 Development

### Without Docker (Local Development)

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📚 API Endpoints

### Current Endpoints
- `GET /` - Health check
- `GET /health` - Detailed health status

### Planned Endpoints
- `GET /api/price?symbol=AAPL` - Current price
- `GET /api/history?symbol=AAPL&period=1y` - Historical data
- `GET /api/prediction?symbol=AAPL` - ML predictions
- `GET /api/risk?symbol=AAPL` - Risk metrics
- `POST /api/portfolio/optimize` - Portfolio optimization

## 🗄️ Database Schema

Coming soon...

## 🧠 ML Models

Coming soon...

## 🚢 Deployment

### Production Deployment Options

1. **Railway.app** (Recommended)
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli
   
   # Login and deploy
   railway login
   railway up
   ```

2. **Render.com**
   - Connect your GitHub repo
   - Select Docker deployment
   - Deploy automatically

3. **DigitalOcean/AWS/GCP**
   - Use docker-compose in production
   - Set up reverse proxy (Nginx)
   - Configure SSL certificates

## 📝 Environment Variables

See `backend/.env.example` for required environment variables.

## 🤝 Contributing

This is a personal project, but suggestions are welcome!

## 📄 License

MIT License

## 🎯 Project Goals

This project demonstrates:
- Full-stack development skills
- ML/AI implementation in production
- Financial domain knowledge
- System design and architecture
- DevOps and deployment expertise

Perfect for interviews at: Two Sigma, Citadel, Point72, BlackRock, AQR, Jane Street, DE Shaw
