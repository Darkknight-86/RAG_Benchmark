#!/bin/bash

# Create proto directory if it doesn't exist
mkdir -p src/rag/proto

# Copy proto file from API Gateway
cp ../../API_Gateway/protos/rag_service.proto src/rag/proto/

# Generate gRPC code using poetry
poetry run python -m grpc_tools.protoc \
    -I./src/rag/proto \
    --python_out=./src/rag/proto \
    --grpc_python_out=./src/rag/proto \
    ./src/rag/proto/rag_service.proto

echo "Generated gRPC code in src/rag/proto/"