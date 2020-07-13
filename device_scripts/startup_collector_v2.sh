#!/bin/bash

# Author: Gary A. Stafford
# Start IoT data collector script and tails output
# Usage:
# ./aws_iot/sensor_collector_v2.sh \
#   iot-device-001 \
#   mnwdhx07n1asx1-ats.iot.us-west-1.amazonaws.com \
#   3

if [[ $# -ne 3 ]]; then
  echo "Script requires 3 parameters..."
  exit 1
fi

DEVICE=$1    # e.g. iot-device-001
ENDPOINT=$2  # e.g mnwdhx07n1asx1-ats.iot.us-west-1.amazonaws.com
FREQUENCY=$3 # e.g 3

echo "DEVICE: ${DEVICE}"
echo "ENDPOINT: ${ENDPOINT}"
echo "FREQUENCY: ${FREQUENCY}"

nohup python3 sensor_collector_v2.py \
  --endpoint "${ENDPOINT}" \
  --cert "work/${DEVICE}.cert.pem" \
  --key "work/${DEVICE}.private.key" \
  --root-ca "work/root-CA.crt" \
  --client-id "${DEVICE}" \
  --topic "iot-device-data" \
  --frequency "${FREQUENCY}" \
  --verbosity "Info" \
  >collector.log 2>&1 </dev/null &

sleep 2

tail -f aws_iot/collector.log
