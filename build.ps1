docker build -t news .
docker run -d -p 1252:8000 --env-file .env --rm --name news news