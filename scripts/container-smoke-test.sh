#!/usr/bin/env bash

set -Eeuo pipefail

IMAGE_NAME="${IMAGE_NAME:-url-shortener:local}"
CONTAINER_NAME="${CONTAINER_NAME:-url-shortener-smoke-test}"
HOST_PORT="${HOST_PORT:-8000}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-15}"
RETRY_DELAY="${RETRY_DELAY:-2}"

cleanup() {
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
}

show_logs() {
    echo
    echo "Container logs:"
    docker logs "$CONTAINER_NAME" 2>&1 || true
}

trap cleanup EXIT

echo "Removing stale test container..."
cleanup

echo "Starting container from image: $IMAGE_NAME"

docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$HOST_PORT:8000" \
    "$IMAGE_NAME"

echo "Waiting for application health endpoint..."

for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
    if curl --fail --silent \
        "http://localhost:${HOST_PORT}/health" \
        >/dev/null; then

        echo "Health check passed on attempt $attempt."
        break
    fi

    if [[ "$attempt" -eq "$MAX_ATTEMPTS" ]]; then
        echo "Application failed to become healthy."
        show_logs
        exit 1
    fi

    echo "Attempt $attempt/$MAX_ATTEMPTS failed. Retrying..."
    sleep "$RETRY_DELAY"
done

echo "Testing URL creation..."

CREATE_RESPONSE=$(
    curl --fail --silent \
        -X POST \
        "http://localhost:${HOST_PORT}/urls" \
        -H "Content-Type: application/json" \
        -d '{"url":"https://example.com"}'
)

echo "Create response: $CREATE_RESPONSE"

SHORT_CODE=$(
    python -c \
        'import json,sys; print(json.load(sys.stdin)["short_code"])' \
        <<< "$CREATE_RESPONSE"
)

if [[ -z "$SHORT_CODE" ]]; then
    echo "No short code returned."
    show_logs
    exit 1
fi

echo "Created short code: $SHORT_CODE"

echo "Testing redirect..."

HTTP_STATUS=$(
    curl --silent \
        --output /dev/null \
        --write-out "%{http_code}" \
        "http://localhost:${HOST_PORT}/${SHORT_CODE}"
)

if [[ "$HTTP_STATUS" != "307" ]]; then
    echo "Expected HTTP 307, received HTTP $HTTP_STATUS."
    show_logs
    exit 1
fi

echo "Redirect test passed."

echo "Testing click counter..."

URL_INFO=$(
    curl --fail --silent \
        "http://localhost:${HOST_PORT}/urls/${SHORT_CODE}"
)

CLICK_COUNT=$(
    python -c \
        'import json,sys; print(json.load(sys.stdin)["clicks"])' \
        <<< "$URL_INFO"
)

if [[ "$CLICK_COUNT" != "1" ]]; then
    echo "Expected click count 1, received $CLICK_COUNT."
    show_logs
    exit 1
fi

echo "Click counter test passed."

echo
echo "All container smoke tests passed."