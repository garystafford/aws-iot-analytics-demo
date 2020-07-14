# Getting Started with AWS IoT Analytics

Code for upcoming post, "Getting Started with AWS IoT Analytics".

## Code Usage

```bash
# clone project
git clone \
--branch master --single-branch --depth 1 --no-tags \
https://github.com/garystafford/kinesis-redshift-streaming-demo.git

# deploy AWS resources
aws cloudformation create-stack \
  --stack-name iot-analytics-demo \
  --template-body file://cloudformation/iot-analytics.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=iot-analytics-demo \
               ParameterKey=IoTTopicName,ParameterValue=iot-device-data \
  --capabilities CAPABILITY_NAMED_IAM

# test stack (5 messages)
cd sample_data
sh ./send_sample_messages.sh raw_data_small.json

# publish sample IoT messages (9,995 messages)
sh ./sample_data/send_sample_messages.sh raw_data_large.json

# OPTIONAL: publish 24hrs. of sample of IoT messages (50,270 messages)
sh ./sample_data/send_sample_messages.sh raw_data_xlarge.json

```