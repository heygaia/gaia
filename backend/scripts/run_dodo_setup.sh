#!/bin/bash

# GAIA Dodo Payments Setup Script
# This script sets up the subscription plans in the database

echo "🚀 Running GAIA Dodo Payments Setup..."
echo "==============================================="

# Set PYTHONPATH to include the current directory so Python can find 'app' module
export PYTHONPATH=/app:$PYTHONPATH

# Run the setup script with the Dodo product IDs
python dodo_setup.py \
  --monthly-product-id "abc" \
  --yearly-product-id "xyz"

echo "==============================================="
echo "✅ Setup completed!"
