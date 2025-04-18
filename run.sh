#!/bin/bash

set -e 

REPO_NAME=ExamEye
IMAGE_NAME=exameye:latest
CONTAINER_NAME=exameye_server
GITHUB_USERNAME=mystlee
GITHUB_TOKEN= # GitHub Personal Access Token
CSV_FILE=java2025.csv
DB_FILE=JAVA_MIDTERM_2025.db
HOST_PORT=5001
GUEST_PORT=5001

. ./parse_arg.sh "$@"

# Docker image build
docker build -t ${IMAGE_NAME} \
  --build-arg GITHUB_USERNAME=${GITHUB_USERNAME} \
  --build-arg GITHUB_TOKEN=${GITHUB_TOKEN} \
  --build-arg REPO_NAME=${REPO_NAME} \
  .

# Remove container if it exists
docker rm -f ${CONTAINER_NAME} 2>/dev/null

# Run docker
docker run -it \
  --name ${CONTAINER_NAME} \
  --shm-size 16G \
  --ipc host \
  -p ${HOST_PORT}:${GUEST_PORT} \
  -e CSV_FILE=${CSV_FILE} \
  -e DB_FILE=${DB_FILE} \
  -e PORT=${GUEST_PORT} \
  -v $(pwd)/${CSV_FILE}:/workspace/${REPO_NAME}/${CSV_FILE} \
  -v $(pwd)/${DB_FILE}:/workspace/${REPO_NAME}/${DB_FILE} \
  ${IMAGE_NAME}
