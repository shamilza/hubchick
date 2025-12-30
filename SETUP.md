# Hubchick CRM - Setup Guide

This guide will help you set up and run the Hubchick CRM project locally.

## Prerequisites

Before you begin, ensure you have the following installed:
- **Docker** and **Docker Compose** (recommended for local development)
- **Python 3.11+** (if running without Docker)
- **Node.js 18+** and **pnpm** (for frontend development)
- **PostgreSQL 15+** (if not using Docker)
- **Redis 7+** (if not using Docker)

## Quick Start with Docker (Recommended)

### 1. Clone the Repository
```bash
git clone https://github.com/shamilza/hubchick.git
cd hubchick
```

### 2. Start Services
```bash
docker-compose up --build
```

This will start:
- PostgreSQL database on `localhost:5432`
- Redis cache on `localhost:6379`
- FastAPI backend on `localhost:8000`

### 3. Access the Application
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000 (if running separately)

## Manual Setup (Without Docker)

### Backend Setup

#### 1. Create Virtual Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/hubchick_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
```

#### 4. Initialize Database
```bash
alembic upgrade head
```

#### 5. Run the Backend
```bash
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

#### 1. Install Dependencies
```bash
cd frontend
pnpm install
```

#### 2. Configure Environment Variables
Create a `.env.local` file in the `frontend/` directory:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

#### 3. Run Development Server
```bash
pnpm dev
```

The frontend will be available at `http://localhost:3000`

## Project Structure

```
hubchick/
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── models.py           # SQLAlchemy models
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Docker configuration
├── frontend/               # React frontend
│   ├── client/
│   │   ├── src/            # React components and pages
│   │   ├── public/         # Static assets
│   │   └── index.html      # HTML entry point
│   ├── package.json        # Node dependencies
│   └── vite.config.ts      # Vite configuration
├── docs/                   # Documentation
│   └── TZ.md              # Technical specification
├── docker-compose.yml      # Docker Compose configuration
└── README.md              # Project overview
```

## API Endpoints (MVP)

### Authentication
- `POST /api/v1/auth/register` - Register new master
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Master Profile
- `GET /api/v1/master/profile` - Get profile
- `PATCH /api/v1/master/profile` - Update profile
- `GET /api/v1/master/schedule` - Get schedule
- `PATCH /api/v1/master/schedule` - Update schedule

### Services
- `POST /api/v1/services` - Create service
- `GET /api/v1/services` - List services
- `PATCH /api/v1/services/{id}` - Update service
- `DELETE /api/v1/services/{id}` - Delete service

### Bookings
- `POST /api/v1/bookings` - Create booking
- `GET /api/v1/bookings` - List bookings
- `PATCH /api/v1/bookings/{id}` - Update booking
- `DELETE /api/v1/bookings/{id}` - Cancel booking

### Public Booking (Client)
- `GET /api/v1/public/{slug}/info` - Get master info
- `GET /api/v1/public/{slug}/slots?date=YYYY-MM-DD` - Get available slots
- `POST /api/v1/public/{slug}/book` - Create booking

### Customers
- `GET /api/v1/customers` - List customers
- `GET /api/v1/customers/{phone}` - Get customer details
- `PATCH /api/v1/customers/{phone}` - Update customer

### Finance
- `GET /api/v1/finance/dashboard` - Get financial dashboard
- `GET /api/v1/finance/history` - Get transaction history
- `POST /api/v1/finance/add-expense` - Add expense

## Development Workflow

### Backend Development
1. Make changes to `backend/` files
2. The server will auto-reload (if using `--reload` flag)
3. Test endpoints using Swagger UI at `http://localhost:8000/docs`

### Frontend Development
1. Make changes to `frontend/client/src/` files
2. The dev server will hot-reload automatically
3. Check the browser console for any errors

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
pnpm test
```

## Deployment

### Production Build

#### Backend
```bash
docker build -t hubchick-backend ./backend
docker run -e DATABASE_URL=... -e REDIS_URL=... -p 8000:8000 hubchick-backend
```

#### Frontend
```bash
cd frontend
pnpm build
# Deploy dist/public to static hosting (Vercel, Netlify, etc.)
```

### Environment Variables for Production
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key (generate with `openssl rand -hex 32`)
- `ENVIRONMENT` - Set to `production`
- `CORS_ORIGINS` - Comma-separated list of allowed origins

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Verify credentials

### Redis Connection Error
- Ensure Redis is running
- Check `REDIS_URL` in `.env`

### Frontend Build Error
- Clear `node_modules` and reinstall: `pnpm install`
- Clear Vite cache: `rm -rf frontend/.vite`

### Port Already in Use
- Backend: Change port in `uvicorn` command
- Frontend: Change port in `vite.config.ts`
- Database: Change port in `docker-compose.yml`

## Support

For issues and questions:
1. Check the [Technical Specification](./docs/TZ.md)
2. Review existing GitHub issues
3. Create a new issue with detailed description

## License

MIT License - see LICENSE file for details
