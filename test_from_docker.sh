#!/bin/bash
# Test connection from inside Docker container

echo "Testing connection from Docker to host..."

# Test if host.docker.internal resolves
ping -c 1 host.docker.internal

# Test if API is reachable
curl -v http://host.docker.internal:8000/health

# Test models endpoint
curl http://host.docker.internal:8000/v1/models
