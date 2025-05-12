#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Check if domain name is set
if [ -z "$DOMAIN_NAME" ]; then
    echo "Error: DOMAIN_NAME not set in .env file"
    exit 1
fi

# Create SSL directory if it doesn't exist
mkdir -p deployment/nginx/ssl/live/$DOMAIN_NAME

# Check if SSL certificates exist
if [ ! -f "deployment/nginx/ssl/live/$DOMAIN_NAME/fullchain.pem" ] || \
   [ ! -f "deployment/nginx/ssl/live/$DOMAIN_NAME/privkey.pem" ]; then
    echo "SSL certificates not found. Please obtain SSL certificates for $DOMAIN_NAME"
    echo "You can use Let's Encrypt with certbot to obtain free SSL certificates"
    exit 1
fi

# Build and start the containers
echo "Building and starting containers..."
docker-compose -f deployment/docker-compose.yml up -d --build

# Check if containers are running
echo "Checking container status..."
if [ "$(docker-compose -f deployment/docker-compose.yml ps -q | wc -l)" -eq 0 ]; then
    echo "Error: Containers failed to start"
    exit 1
fi

echo "Deployment completed successfully!"
echo "Your application is now running at https://$DOMAIN_NAME" 