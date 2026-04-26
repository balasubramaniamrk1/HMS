#!/bin/bash

# Configuration
SERVER_USER="bala"      # The user to run the application
SERVER_IP="$1"          # Pass IP as first argument
# If second argument is provided, use it as domain. Otherwise default to SERVER_IP (IP-based access)
if [ -n "$2" ] && [[ "$2" != "production/"* ]] && [[ "$2" != "ubuntu" ]]; then
    DOMAIN_NAME="$2"
    SSH_KEY="$3"
    SSH_USER="${4:-ubuntu}"
else
    # Handle case where user skipped domain name and went straight to pem file
    # Check if $2 looks like a key file or user just skipped it
    DOMAIN_NAME="$SERVER_IP"
    SSH_KEY="$2"
    SSH_USER="${3:-ubuntu}"
fi

APP_DIR="/home/$SERVER_USER/hms_project"
PROJECT_DIR="$APP_DIR"
DB_NAME="hms_db"
DB_USER="hms_user"
DB_PASSWORD="hms123$" # Should match what's on server or be passed in
SECRET_KEY="Qhzy6r_UNiJM7uWn4PAC0h7De-hrtzJZk-8iapTdJiAQy-I4T0gkjzCLDis9988IuAU"

if [ -z "$SERVER_IP" ] || [ -z "$SSH_KEY" ]; then
    echo "Usage: ./production/update_remote_config.sh <SERVER_IP> [DOMAIN_NAME] <SSH_KEY_PATH> [SSH_USER]"
    echo "Example (IP Access): ./production/update_remote_config.sh 3.94.31.213 production/hms.pem ubuntu"
    echo "Example (Domain):    ./production/update_remote_config.sh 3.94.31.213 mydomain.com production/hms.pem ubuntu"
    exit 1
fi

echo "========================================================"
echo "Updating Config on EC2: $SERVER_IP ($DOMAIN_NAME)"
echo "User: $SSH_USER -> $SERVER_USER"
echo "Key: $SSH_KEY"
echo "========================================================"

# Helper for SSH commands
SSH_CMD="ssh -i $SSH_KEY -o StrictHostKeyChecking=no"

$SSH_CMD -t $SSH_USER@$SERVER_IP << EOF
    set -e

    echo "--> Updating .env file..."
    # Write to a temp file first since ubuntu user might not have write access to bala's home
    cat > /tmp/.env.tmp << ENV
SECRET_KEY='$SECRET_KEY'
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP,$DOMAIN_NAME
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
ENV
    
    # Move to destination with sudo and fix permissions
    sudo mv /tmp/.env.tmp $APP_DIR/.env
    sudo chown $SERVER_USER:$SERVER_USER $APP_DIR/.env
    sudo chmod 600 $APP_DIR/.env

    echo "--> Updating Nginx Config..."
    # Assuming nginx.conf is already there, we just want to ensure server_name is correct
    # But since we aren't copying files, we simply sed the existing one on the server
    
    # Update server_name in nginx config
    # We look for the server_name line and replace it
    sudo sed -i "s|server_name .*;|server_name $DOMAIN_NAME;|g" /etc/nginx/sites-available/hms_project
    
    # Reload Nginx
    sudo nginx -t
    sudo systemctl reload nginx
    
    # Restart Gunicorn to pick up .env changes
    echo "--> Restarting Gunicorn..."
    sudo systemctl restart gunicorn

    echo "Configuration updated successfully."
EOF
