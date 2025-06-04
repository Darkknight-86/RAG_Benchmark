#!/bin/bash

# must install azure-cli and coreutils

# Azure Blob Storage monitoring script
CONTAINER="ragpipeline9319"
PREFIX="streamed/"
INTERVAL=600  # 10 minutes in seconds

echo "Starting Azure Blob Storage monitoring for: $CONTAINER/$PREFIX"
echo "Checking every 10 minutes. Press Ctrl+C to stop."
echo "----------------------------------------"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP]"

    # List blobs and sum their sizes
    TOTAL_SIZE=$(az storage blob list \
        --container-name "$CONTAINER" \
        --prefix "$PREFIX" \
        --account-name "ragpipeline9319" \
        --query "[].properties.contentLength" \
        --output tsv | awk '{s+=$1} END {print s}')

    # Convert bytes to human-readable format
    if [[ -n "$TOTAL_SIZE" ]]; then
        HR_SIZE=$(numfmt --to=iec-i --suffix=B $TOTAL_SIZE)
        echo "Total size: $HR_SIZE ($TOTAL_SIZE bytes)"
    else
        echo "No blobs found."
    fi

    echo "----------------------------------------"
    sleep $INTERVAL
done