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


def lambda_handler(event, context):
    calapi_response = requests.get(format_url("http://calapi.inadiutorium.cz/api/v0/en/calendars/general-en/{}/{}/{}"),
                                   timeout=1)
    calapi_response_json = calapi_response.json()
    print('calapi response ', json.dumps(calapi_response_json, indent=2))

    celebrations = calapi_response_json['celebrations']

    message = '\nToday\'s celebration(s):\n'

    i = 1
    for c in celebrations:
        message = message + '[' + str(i) + '] '
        message = message + c.get('title') + ' (' + c.get('rank') + ')\n'
        i += 1

    print('calapi message:', message)

    ewtn_response = requests.get(format_url("https://www.ewtn.com/se/readings/readingsservice.svc/day/{}-{}-{}/en"),
                                 timeout=1)
    ewtn_response_json = ewtn_response.json()
    print('ewtn response ', json.dumps(ewtn_response_json, indent=2))

    reading_groups = ewtn_response_json.get('ReadingGroups')
    default_readings = reading_groups[0]
    readings = default_readings['Readings']

    message = message + "\nToday\'s readings:"

    for i in range(0, len(readings)):
        text = readings[i]['Citations'][0]['Reference']
        message = message + "\n" + text

    print('final message:', message)

    if 'SNS_ENABLED' in os.environ:
        if os.environ['SNS_ENABLED'] == 'TRUE':
            sns = boto3.client('sns')
            sns_response = sns.publish(
                TopicArn=os.environ['ARN_TOPIC'],
                Message=message
            )
            print(sns_response)
        else:
            print('SNS_ENABLED is false:\n' + message)
    else:
        print('Did NOT publish to SNS:\n' + message)

    if calapi_response.status_code == ewtn_response.status_code:
        status_code = calapi_response.status_code
    else:
        status_code = max(calapi_response.status_code, ewtn_response.status_code)

    return_body = {}
    return_body.update(calapi_response_json)
    return_body.update(ewtn_response_json)

    return {
        'statusCode': status_code,
        'body': return_body
    }


def main():
    lambda_handler(None, None)


main()
