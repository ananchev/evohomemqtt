## Create image
```console
docker build -t evohomemqtt .
```

## Export image to file
Generate image tar file to copy and load into the intended docker host
```console
docker save -o evohomemqtt.tar evohomemqtt
```

## Load tar image
Once image copied to the docker host, can be loaded with the command below
```console
docker load -i evohomemqtt.tar
```

## Run image on host
```console
docker run \
        --name evohomemqtt \
        --net=host \
        -v /etc/localtime:/etc/localtime:ro \
        -v /etc/timezone:/etc/timezone:ro \
        -e USER=<username> \
        -e PASSWORD=<password> \
        -e MQTT_BROKER=<mqtt broker ip> \
        -d \
        --restart=always \
        evohomemqtt:latest
```