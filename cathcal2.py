import requests
import datetime
import boto3
import os
import json


def format_url(url):
    d = datetime.datetime.today() - datetime.timedelta(hours=4)
    print('Current date and time: ', d)

    formatted_url = url.format(d.year, d.month, d.day)
    print("formatted Url ", formatted_url)

    return formatted_url


def retrieve_celebrations():
    calapi_response = requests.get(format_url("http://calapi.inadiutorium.cz/api/v0/en/calendars/general-en/{}/{}/{}"),
                                   timeout=1)
    calapi_response_json = calapi_response.json()
    print('calapi response ', json.dumps(calapi_response_json, indent=2))

    celebrations = calapi_response_json['celebrations']

    message = ''
    i = 1
    for c in celebrations:
        message = message + '[' + str(i) + '] '
        message = message + c.get('title') + ' (' + c.get('rank') + ')\n'
        i += 1

    print('calapi message:', message)
    return message


def retrieve_readings():
    ewtn_response = requests.get(format_url("https://www.ewtn.com/se/readings/readingsservice.svc/day/{}-{}-{}/en"),
                                 timeout=1)
    ewtn_response_json = ewtn_response.json()
    print('ewtn response ', json.dumps(ewtn_response_json, indent=2))

    reading_groups = ewtn_response_json.get('ReadingGroups')
    default_readings = reading_groups[0]
    readings = default_readings['Readings']

    message = ''
    for i in range(0, len(readings)):
        text = readings[i]['Citations'][0]['Reference']
        message = message + "\n" + text

    return message


def deliver_message(message):
    if 'SNS_ENABLED' in os.environ:
        if os.environ['SNS_ENABLED'] == 'TRUE':
            sns = boto3.client('sns')
            sns_response = sns.publish(
                TopicArn=os.environ['ARN_TOPIC'],
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            print(sns_response)
        else:
            print('SNS_ENABLED is false:\n' + message)
    else:
        print('Could not find SNS_ENABLED env var')


def lambda_handler(event, context):
    message = '\nToday\'s celebration(s):\n' + retrieve_celebrations()

    message = message + "\nToday\'s readings:" + retrieve_readings()

    print('final message:', message)

    deliver_message(message)

    return {
        'statusCode': 200,
        'body': ''
    }


# remove below for deployment
def main():
    lambda_handler(None, None)


main()
