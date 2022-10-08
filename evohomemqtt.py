#! /usr/bin/env python

"""Uses the brilliant Evohome Client from Andrew Stock to query the status of
a Honeywell Evohome heat system and publishes the responses to an a MQTT broker.

Evohome Client available https://github.com/watchforstock/evohome-client

Run with your username and password
eventcmd = /home/pi/bin/evohomemqtt.py -u username -p password
"""

import argparse
import logging
import logging.handlers
from evohomeclient2 import EvohomeClient
import paho.mqtt.publish as mqtt

# Global Logger
_LOG = logging.getLogger('evohome')

_LOG = logging.getLogger()
_HANDLER = logging.StreamHandler()
_FORMATTER = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
_HANDLER.setFormatter(_FORMATTER)
_LOG.addHandler(_HANDLER)

def main():
    """Main function, parse args and read alarm files, send resulting events to mqtt broker"""
    parser = argparse.ArgumentParser(description="An Honeywell Evohome to MQTT inteface",
                                     epilog="V0.1 by Dave Sargeant, Evohome Client by Andrew Stock")

    parser.add_argument("-u", "--username", required=True,
                        help="Username/Email to log into mytotalconnectcomfort.")
    parser.add_argument("-p", "--password", required=True,
                        help="Password for mytotalconnectcomfort.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("-m", "--mqtt-broker", dest='mqtt_broker', default='localhost',
                        help="Relay events to mqtt server")

    param = parser.parse_args()

    syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
    _LOG.addHandler(syslog_handler)

    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger



    scheduler = BlockingScheduler()
    scheduler.add_job(run, IntervalTrigger(seconds=60), (param,))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass 

def run(args):
    if args.verbose is True:
        _LOG.setLevel(logging.DEBUG)

    _LOG.info("Connecting to mytotalconnectcomfort as %s", args.username)

    try:
        client = EvohomeClient(args.username, args.password)
    except Exception as error: # pylint: disable=broad-except
        _LOG.error("Unable to connect to mytotalconnectcomfort %s", str(error))

    _LOG.info("client %s", str(client))

    msgs = []
    for device in client.temperatures():
        _LOG.info("device %s", str(device))
        # Remove spaces and lower case
        topic = device['name'].replace(' ', '_').lower()
        if device['thermostat'] == 'EMEA_ZONE':

            for thing in ['temp', 'setpoint']:
                mqtt_topic = "evohome/{}/{}".format(thing, topic)
                
                try:
                    value = float(device[thing])
                except TypeError:
                    _LOG.error("For topic {} rejecting non-float {} {}".format(mqtt_topic, thing, device[thing]))
                    continue

                if value > 75:
                    _LOG.error("For topic {} rejecting out of range {} {}".format(mqtt_topic, thing, device[thing]))
                    continue

                payload = "{}".format(value)
                msg = {'topic':mqtt_topic, 'payload':payload}
                _LOG.debug("Adding (topic=%s) : %s to %s", mqtt_topic, payload, args.mqtt_broker)
                msgs.append(msg)

        elif device['thermostat'] == 'DOMESTIC_HOT_WATER':
            topic = "evohome/temp/domestic_hot_water"

            temp = float(device['temp'])

            if temp > 75:
                _LOG.error("For topic {} rejecting out of range temp {}".format(topic, temp))
                continue

            payload = "{temp}".format(temp=device['temp'])
            msg = {'topic':topic, 'payload':payload}
            _LOG.debug("Adding (topic=%s) : %s to %s", topic, payload, args.mqtt_broker)
            msgs.append(msg)           

        else:
            _LOG.info("Unknown device: %s", str(device))
            continue

    mqtt.multiple(msgs, hostname=args.mqtt_broker)
    if len(msgs):
        _LOG.info("Sending %d messages to broker %s", len(msgs), args.mqtt_broker)


if __name__ == "__main__":
     main()