# factory-pulse-frontend/Dockerfile
FROM node:22-alpine

WORKDIR /app

# Dependencies (separate layer for better cache usage)
COPY package.json package-lock.json ./
RUN npm install

# Application source
COPY . .

# Vite dev server port
EXPOSE 5173

# Expose dev server to the network
CMD ["npm", "run", "dev", "--", "--host"]
