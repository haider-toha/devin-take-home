#!/bin/bash

# Script to run the application using Docker Compose

echo "Starting Devin Issue Assistant with Docker..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Creating .env from env.example..."
    cp env.example .env
    echo ""
    echo "WARNING: Please edit .env file with your credentials before continuing."
    echo ""
    exit 1
fi

# Start Docker Compose
docker-compose up --build

# Handle shutdown
trap "echo ''; echo 'Stopping containers...'; docker-compose down; exit 0" INT TERM

