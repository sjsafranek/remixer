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

psql -p 5431 -U postgres -d remixerdb -h 127.0.0.1






## Tools

### loader.py

Imports analyzed song chunks to database

python3 loader.py -file songs/Ain\'t\ No\ Mountain\ High\ Enough.mp3 -dbport 5431


### finder.py

Finds songs with given noteset

python3 finder.py G# B -dbport 5431

[{"song":{"matches":46,"total":308,"song":{"genre":null,"created_at":"2020-10-24T05:04:32Z","updated_at":"2020-10-24T05:04:32Z","url":null,"name":"songs/Ain't No Mountain High Enough.mp3","artist":null,"id":1}}}]
