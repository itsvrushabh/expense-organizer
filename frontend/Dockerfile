FROM oven/bun:1.4.0

WORKDIR /app

# Copy package files
COPY package.json bun.lock* ./

# Install dependencies
RUN bun install

# Copy application files
COPY . .

# Expose port
EXPOSE 3000

# Run the application
CMD ["bun", "start"]
