#!/bin/bash
cd /home/pkkumar/AGGY/spark-test-tool
echo "Starting Spark Test Tool..."
docker compose --ansi never --progress plain up --build -d > docker_up.log 2>&1
echo ""
echo "Gateway:  http://localhost:5050"
echo "Whisper:  http://localhost:8010"
echo "F5-TTS:   http://localhost:8020"
echo ""
echo "Logs: docker compose logs -f"
echo "Stop: docker compose down"
