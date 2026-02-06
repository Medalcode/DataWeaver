@echo off
REM Macro Builder - Quick Start Script (Windows)

echo Starting Macro Builder services...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Start services
echo Starting PostgreSQL, Redis, API, and Celery...
docker-compose up -d

REM Wait for services
echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul

REM Check health
echo Checking API health...
curl -s http://localhost:8000/health | find "healthy" >nul
if errorlevel 1 (
    echo Services failed to start. Check logs with: docker-compose logs
    pause
    exit /b 1
)

echo.
echo ========================================
echo  All services are running!
echo ========================================
echo.
echo Available endpoints:
echo    API:          http://localhost:8000
echo    API Docs:     http://localhost:8000/docs
echo    PostgreSQL:   localhost:5432
echo    Redis:        localhost:6379
echo.
echo Next steps:
echo    1. Visit http://localhost:8000/docs for interactive API documentation
echo    2. Create an account via POST /api/v1/auth/register
echo    3. Login to get your JWT token
echo    4. Start creating workflows!
echo.
echo To stop services: docker-compose down
echo.
pause
