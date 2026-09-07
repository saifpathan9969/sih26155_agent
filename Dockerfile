# Multi-stage Dockerfile for SIH26155 Auditor

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend & Static Server
FROM python:3.11-slim
WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY sih26155_agent/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY sih26155_agent/ ./sih26155_agent/

# Copy built frontend assets to the expected static directory
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port (Render automatically sets $PORT)
ENV PORT=8000
EXPOSE 8000

WORKDIR /app/sih26155_agent
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
