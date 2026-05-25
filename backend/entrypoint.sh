#!/bin/sh
set -e

# Wait for MySQL to be reachable
echo "Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT}..."
i=0
until python -c "import socket,sys; s=socket.socket(); s.settimeout(2); s.connect(('${MYSQL_HOST}', ${MYSQL_PORT})); s.close()" 2>/dev/null; do
  i=$((i+1))
  if [ $i -gt 60 ]; then
    echo "MySQL did not become ready in time"
    exit 1
  fi
  sleep 1
done
echo "MySQL is up."

# Auto-migrate on api boot if requested (default yes)
if [ "${AUTO_MIGRATE:-1}" = "1" ] && [ "${1:-}" = "gunicorn" ]; then
  echo "Running migrations..."
  flask db upgrade || echo "(migrations already up to date or failed)"
fi

exec "$@"
