#!/bin/bash

# Usage: ./production/update_server_ip.sh <OLD_IP> <NEW_IP>

OLD_IP=$1
NEW_IP=$2

if [ -z "$OLD_IP" ] || [ -z "$NEW_IP" ]; then
    echo "Usage: $0 <OLD_IP> <NEW_IP>"
    echo "Example: $0 3.219.217.0 3.94.31.213"
    exit 1
fi

echo "Updating IP from $OLD_IP to $NEW_IP..."

# Update .env
if [ -f .env ]; then
    sed -i '' "s/$OLD_IP/$NEW_IP/g" .env
    echo "Updated .env"
else
    echo "Warning: .env not found"
fi

# Update production/nginx.conf
if [ -f production/nginx.conf ]; then
    sed -i '' "s/$OLD_IP/$NEW_IP/g" production/nginx.conf
    echo "Updated production/nginx.conf"
else
    echo "Warning: production/nginx.conf not found"
fi

echo "Configuration files updated. You can now run the deployment script to push changes."
