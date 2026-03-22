#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Lost & Found Portal ==="
echo "Initialising database..."
python3 init_db.py

echo ""
echo "Starting Datasette on http://localhost:8001 ..."
datasette serve lost_found.db \
  --metadata datasette_metadata.json \
  --port 8001 \
  --cors \
  --host 0.0.0.0 &
DATASETTE_PID=$!

echo "Starting Flask app on http://localhost:5000 ..."
echo ""
echo "  Frontend → http://localhost:5000"
echo "  Datasette → http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop both servers."
echo "==================================="

# Kill datasette when flask exits
trap "kill $DATASETTE_PID 2>/dev/null; exit" INT TERM

python3 app.py
kill $DATASETTE_PID 2>/dev/null
