# remixer
Python3 tool chain using TimeScaleDB to analyze music tracks


## Installation

python3 -m pip install --upgrade -r requirements.txt


## Convert mp3 to wav

Requires ffmpeg

`./helper_scripts/convert2wav.sh "Ain't No Mountain High Enough.mp3"`




## Setup TimeScaleDB database

### TimeScaleDB Docker Container

docker run -d --name timescaledb -p 127.0.0.1:5431:5432 -e POSTGRES_PASSWORD=dev timescale/timescaledb:1.7.4-pg12

sleep 1

docker exec -it timescaledb psql -U postgres
