import argparse
import json
import sys
import threading
import time

import adafruit_dht
from awscrt import io, mqtt, auth, http, exceptions
from awsiot import mqtt_connection_builder
from getmac import get_mac_address as gma
from gpiozero import LightSensor, MotionSensor, LED

from MQ import MQ

# Author: Gary A. Stafford
# V2 uses AWS IoT SDK for Python v2 and newer Adafruit_CircuitPython_DHT library
# MQTT connection code is modified version of aws-iot-device-sdk-python-v2 sample:
# https://github.com/aws/aws-iot-device-sdk-python-v2/blob/master/samples/pubsub.py
# https://github.com/adafruit/Adafruit_CircuitPython_DHT


# Constants
PIN_DHT = 18
PIN_LIGHT = 24
PIN_PIR = 23
PIN_PIR_LED = 25

# Global Variables
count: int = 0  # from args
received_count: int = 0
received_all_event = threading.Event()


def main():
    # Parse command line arguments
    parser, args = parse_args()

    global count
    count = args.count

    # set log level
    io.init_logging(getattr(io.LogLevel, args.verbosity), 'stderr')

    # Print MAC address
    print(gma())

    # Initialize and Calibrate Gas Sensor 1x
    mq = MQ()

    # Initial the dht device, with data pin connected to:
    dht_device = adafruit_dht.DHT22(PIN_DHT)

    # Initialize Light Sensor
    ls = LightSensor(PIN_LIGHT)

    # Initialize PIR Sensor
    pir = MotionSensor(PIN_PIR)
    led = LED(PIN_PIR_LED)

    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    # Set MQTT connection
    mqtt_connection = set_mqtt_connection(args, client_bootstrap)

    print("Connecting to {} with client ID '{}'...".format(
        args.endpoint, args.client_id))

    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    # # Subscribe (this will pull in messages down from other devices)
    # print("Subscribing to topic '{}'...".format(args.topic))
    # subscribe_future, packet_id = mqtt_connection.subscribe(
    #     topic=args.topic,
    #     qos=mqtt.QoS.AT_LEAST_ONCE,
    #     callback=on_message_received)
    #
    # subscribe_result = subscribe_future.result()
    # print("Subscribed with {}".format(str(subscribe_result['qos'])))

    while True:
        led.off()

        # Create message payload
        payload_dht = get_sensor_data_dht(dht_device)
        payload_gas = get_sensor_data_gas(mq)
        payload_light = get_sensor_data_light(ls)
        payload_motion = get_sensor_data_motion(pir, led)

        payload = {
            "device_id": gma(),
            "ts": time.time(),
            "data": {
                "temp": payload_dht["temp"],
                "humidity": payload_dht["humidity"],
                "lpg": payload_gas["lpg"],
                "co": payload_gas["co"],
                "smoke": payload_gas["smoke"],
                "light": payload_light["light"],
                "motion": payload_motion["motion"]
            }
        }

        # Don't send bad messages!
        if payload["data"]["temp"] is not None \
                and payload["data"]["humidity"] is not None \
                and payload["data"]["co"] is not None:
            # Publish Message
            message_json = json.dumps(payload, sort_keys=True, indent=None, separators=(',', ':'))

            try:
                mqtt_connection.publish(
                    topic=args.topic,
                    payload=message_json,
                    qos=mqtt.QoS.AT_LEAST_ONCE)
            except mqtt.SubscribeError as err:
                print(".SubscribeError: {}".format(err))
            except exceptions.AwsCrtError as err:
                print("AwsCrtError: {}".format(err))
            else:
                time.sleep(args.frequency)
        else:
            print("sensor failure...retrying...")


def set_mqtt_connection(args, client_bootstrap):
    if args.use_websocket:
        proxy_options = None
        if args.proxy_host:
            proxy_options = http.HttpProxyOptions(host_name=args.proxy_host, port=args.proxy_port)

        credentials_provider = auth.AwsCredentialsProvider.new_default_chain(client_bootstrap)
        mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
            endpoint=args.endpoint,
            client_bootstrap=client_bootstrap,
            region=args.signing_region,
            credentials_provider=credentials_provider,
            websocket_proxy_options=proxy_options,
            ca_filepath=args.root_ca,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            client_id=args.client_id,
            clean_session=False,
            keep_alive_secs=6)

    else:
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=args.endpoint,
            cert_filepath=args.cert,
            pri_key_filepath=args.key,
            client_bootstrap=client_bootstrap,
            ca_filepath=args.root_ca,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            client_id=args.client_id,
            clean_session=False,
            keep_alive_secs=6)

    return mqtt_connection


def get_sensor_data_dht(dht_device):
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity
        payload = {
            "temp": temperature,
            "humidity": humidity
        }
    except RuntimeError as err:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(".RuntimeError: {}".format(err))
        payload = {
            "temp": None,
            "humidity": None
        }
        return payload

    return payload


def get_sensor_data_gas(mq):
    try:
        mqp = mq.MQPercentage()
        payload = {
            "lpg": mqp["GAS_LPG"],
            "co": mqp["CO"],
            "smoke": mqp["SMOKE"]
        }
    except ValueError as err:
        print("Error: {}".format(err))
        payload = {
            "lpg": None,
            "co": None,
            "smoke": None
        }

    return payload


def get_sensor_data_light(ls):
    # print("ls.value: {}".format(ls.value))

    if ls.value == 0.0:  # > 0.1:
        payload = {"light": True}
    else:
        payload = {"light": False}

    return payload


def get_sensor_data_motion(pir, led):
    # print("pir.value: {}".format(pir.value))

    if pir.value == 1.0:  # > 0.5:
        payload = {"motion": True}
        led.on()
    else:
        payload = {"motion": False}
        led.off()

    return payload


# Read in command-line parameters
def parse_args():
    parser = argparse.ArgumentParser(description="Send and receive messages through and MQTT connection.")
    parser.add_argument('--endpoint', required=True, help="Your AWS IoT custom endpoint, not including a port. " +
                                                          "Ex: \"abcd123456wxyz-ats.iot.us-east-1.amazonaws.com\"")
    parser.add_argument('--cert', help="File path to your client certificate, in PEM format.")
    parser.add_argument('--key', help="File path to your private key, in PEM format.")
    parser.add_argument('--root-ca', help="File path to root certificate authority, in PEM format. " +
                                          "Necessary if MQTT server uses a certificate that's not already in " +
                                          "your trust store.")
    parser.add_argument('--client-id', default='samples-client-id', help="Client ID for MQTT connection.")
    parser.add_argument('--topic', default="samples/test", help="Topic to subscribe to, and publish messages to.")
    parser.add_argument('--message', default="Hello World!", help="Message to publish. " +
                                                                  "Specify empty string to publish nothing.")
    parser.add_argument('--count', default=0, type=int, help="Number of messages to publish/receive before exiting. " +
                                                             "Specify 0 to run forever.")
    parser.add_argument('--use-websocket', default=False, action='store_true',
                        help="To use a websocket instead of raw mqtt. If you specify this option you must "
                             "specify a region for signing, you can also enable proxy mode.")
    parser.add_argument('--signing-region', default='us-east-1',
                        help="If you specify --use-web-socket, this is the region that will be used for computing "
                             "the Sigv4 signature")
    parser.add_argument('--proxy-host', help="Hostname for proxy to connect to. Note: if you use this feature, " +
                                             "you will likely need to set --root-ca to the ca for your proxy.")
    parser.add_argument('--proxy-port', type=int, default=8080, help="Port for proxy to connect to.")
    parser.add_argument('--verbosity', choices=[x.name for x in io.LogLevel], default=io.LogLevel.NoLogs.name,
                        help='Logging level')
    parser.add_argument("--frequency", action="store", dest="frequency", type=int, default=5,
                        help="IoT event message frequency")

    args = parser.parse_args()
    return parser, args


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    if received_count == count:
        received_all_event.set()


if __name__ == "__main__":
    sys.exit(main())
