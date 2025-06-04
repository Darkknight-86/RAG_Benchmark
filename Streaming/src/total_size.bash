#!/bin/bash

# S3 bucket monitoring script
BUCKET="s3://ragproject-store/streamed/"
INTERVAL=600  # 10 minutes in seconds

echo "Starting S3 bucket monitoring for: $BUCKET"
echo "Checking every 10 minutes. Press Ctrl+C to stop."
echo "----------------------------------------"

while true; do
    # Get current timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP]"
    
    # Execute the S3 command
    aws s3 ls "$BUCKET" --recursive --human-readable --summarize | grep "Total"
    
    echo "----------------------------------------"
    
    # Wait 10 minutes
    sleep $INTERVAL
done