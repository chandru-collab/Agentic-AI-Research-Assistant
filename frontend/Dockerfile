# Stage 1: Build React App
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install

# Copy source and configurations
COPY vite.config.js ./
COPY index.html ./
COPY src/ ./src/

# Compile React project to static assets
RUN npm run build

# Stage 2: Serve React App using Nginx
FROM nginx:alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
