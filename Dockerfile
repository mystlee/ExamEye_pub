FROM python:3.12.10

WORKDIR /workspace

ARG GITHUB_TOKEN
ARG GITHUB_USERNAME
ARG REPO_NAME

RUN echo "Cloning..." && \
    git clone https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git && \
    echo "Clone success" || echo "Clone failed"

WORKDIR /workspace/${REPO_NAME}

RUN pip install --no-cache-dir -r requirements.txt

ENV CSV_FILE=default.csv
ENV DB_FILE=default.db
ENV PORT=5000

CMD ["sh", "-c", "python server.py --csv $CSV_FILE --db $DB_FILE --port $PORT"]
