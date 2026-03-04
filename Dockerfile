# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

# Stage 2: Build Backend & Runner
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies
# gcc and libffi-dev are sometimes needed for python crypto/cffi packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend source
COPY backend /app/backend
RUN pip install --no-cache-dir -e /app/backend

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /app/frontend_dist

# Set default environment variables for production
ENV FLASK_APP="snipsel_api.app"
ENV SNIPSEL_FRONTEND_DIR="/app/frontend_dist"
ENV SNIPSEL_UPLOAD_DIR="/app/uploads"
ENV SNIPSEL_DATABASE_URL="sqlite:////app/data/snipsel.db"
ENV SNIPSEL_DOMAIN="localhost"
ENV SNIPSEL_FRONTEND_URL="http://localhost:5000"

# Create directories for data and uploads
RUN mkdir -p /app/data /app/uploads && \
    chmod 777 /app/data /app/uploads

EXPOSE 5000

# Create an entrypoint script
RUN echo '#!/bin/sh\n\
set -e\n\
echo "Running database migrations..."\n\
cd /app/backend\n\
flask db upgrade\n\
echo "Starting backend..."\n\
cd /app\n\
exec gunicorn -w 4 -b 0.0.0.0:5000 "snipsel_api.app:create_app()"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
