# =============================================================================
# Stage 1: Build the Vue3 frontend
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Build argument for API base URL
ARG VITE_API_BASE_URL=http://localhost:4000/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build for production
RUN npm run build

# =============================================================================
# Stage 2: Serve with nginx
# =============================================================================
FROM nginx:alpine

# Copy built static files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config for Vue Router history mode
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
