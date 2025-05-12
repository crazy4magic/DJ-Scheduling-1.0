#!/bin/bash

# Replace environment variables in nginx config
envsubst '${DOMAIN_NAME}' < /etc/nginx/nginx.conf > /etc/nginx/nginx.conf.tmp
mv /etc/nginx/nginx.conf.tmp /etc/nginx/nginx.conf

# Start Nginx in the background
nginx

# Start Streamlit
streamlit run /app/app/main.py 