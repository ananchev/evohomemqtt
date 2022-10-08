FROM python:3.9-alpine

#setup the environment
WORKDIR /app
RUN apk add --no-cache git
RUN apk add --no-cache openssh

#obtain the evohome-client library
RUN git clone https://github.com/watchforstock/evohome-client.git

#fix the evohome-client limitation 
#comment out the check for only one location
RUN sed -e '/if len(self.locations) != 1:/s/^/#/g' -i evohome-client/evohomeclient2/__init__.py
RUN sed -e '/raise Exception("More (or less) than one location available")/s/^/#/g' -i evohome-client/evohomeclient2/__init__.py
#hardcode the second location to be used (first is Gerard Walschaphove, second is Woudsenderraklaan)
RUN sed -i 's/return self.locations\[0\]/return self.locations[1]/g' evohome-client/evohomeclient2/__init__.py

#copy the evohome mqtt client and install its dependencies
COPY evohomemqtt.py /app/
RUN pip install --no-cache-dir ./evohome-client
RUN pip install --no-cache-dir apscheduler
RUN pip install --no-cache-dir paho-mqtt

# run
ENTRYPOINT python /app/evohomemqtt.py -u $USER -p $PASSWORD -m $MQTT_BROKER