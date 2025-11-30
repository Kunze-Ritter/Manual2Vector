# Frontend Dockerfile for KRAI Dashboard
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ .

# Copy production environment configuration
# Vite automatically reads .env.production when NODE_ENV=production
# These environment variables are baked into the static build at compile time
COPY frontend/.env.production .env.production

# Build the application for production
# Uses the dedicated production build script from package.json
RUN npm run build:production

# Production stage
# The nginx stage doesn't need environment variables since they're already
# compiled into the JavaScript bundle from the builder stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx/nginx-simple.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
