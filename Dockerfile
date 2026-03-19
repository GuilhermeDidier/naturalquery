FROM python:3.13-slim

# Install Node.js 20
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build frontend
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build && \
    mkdir -p ../backend/frontend_dist && \
    cp -r dist/. ../backend/frontend_dist/

# Copy backend
COPY backend/ ./backend/

# Collect static files (dummy secret key just for this step)
RUN cd backend && DJANGO_SECRET_KEY=build-only DEBUG=False python manage.py collectstatic --noinput

WORKDIR /app/backend

EXPOSE 8000

CMD python manage.py migrate && python manage.py seed_demo && gunicorn core.wsgi --bind 0.0.0.0:$PORT --workers 2
