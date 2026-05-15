#!/bin/bash

echo "Starting deployment preparation..."

# Ensure the script stops if any command fails
set -e

# Build the Docker image
echo "Building Docker image 'trading-bot'..."
docker build -t trading-bot .

echo ""
echo "====================================================="
echo "Deployment Ready!"
echo "To run the container locally with your API keys, use:"
echo "docker run -d --name trading-engine -e APCA_API_KEY_ID='your_key' -e APCA_API_SECRET_KEY='your_secret' trading-bot"
echo "====================================================="
echo "For cloud hosting (e.g. Railway, Render, DigitalOcean):"
echo "1. Push this repository to GitHub."
echo "2. Connect the repository to your hosting provider."
echo "3. The provider will automatically detect the Dockerfile and deploy the container."
echo "4. Do not forget to add your APCA_API_KEY_ID and APCA_API_SECRET_KEY in the provider's Environment Variables dashboard."
