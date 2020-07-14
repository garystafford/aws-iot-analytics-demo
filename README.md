# Getting Started with AWS IoT Analytics

Code for upcoming post, "Getting Started with AWS IoT Analytics".

## Code Usage

```bash
# clone project
git clone \
    --branch master --single-branch --depth 1 --no-tags \
    https://github.com/garystafford/aws-iot-analytics-demo.git

# deploy AWS resources
aws cloudformation create-stack \
    --stack-name iot-analytics-demo \
    --template-body file://cloudformation/iot-analytics.yaml \
    --parameters ParameterKey=ProjectName,ParameterValue=iot-analytics-demo \
               ParameterKey=IoTTopicName,ParameterValue=iot-device-data \
    --capabilities CAPABILITY_NAMED_IAM

# publish sample messages to test cfn stack (5 messages)
cd sample_data
time python3 ./send_sample_messages.py -f raw_data_small.json -t iot-device-data

# publish sample IoT messages (9,995 messages)
time python3 ./send_sample_messages.py -f raw_data_large.json -t iot-device-data

# OPTIONAL: publish 24hrs. of sample of IoT messages (50,270 messages)
unzip raw_data_xlarge.json.zip
time python3 ./send_sample_messages.py -f raw_data_xlarge.json -t iot-device-data
```