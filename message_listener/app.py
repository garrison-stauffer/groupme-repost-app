import json
import requests
import urllib3
import numpy as np
import cv2
from datetime import datetime
from pytz import timezone


from groupme_message import GroupmeMessage

from notifier import send_message_to_main_channel, send_info_message

import boto3
from boto3.dynamodb.conditions import Key

HASH_SIZE = 8

http = urllib3.PoolManager()

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('GroupMeImages')


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    message = GroupmeMessage(event)

    if should_drop_request(message):
        return ok()

    cv2_image = get_cv2_image(message)

    dhash_digest = dhash(cv2_image)
    print("dhash =", dhash_digest)

    try:
        query_result = table.query(
            IndexName="img_dhash-created_at-index-copy",
            KeyConditionExpression=Key('img_dhash').eq(dhash_digest)
        )

        if (len(query_result['Items']) > 0):
            reposter_string = get_reposter_string(query_result['Items'])
            repost_alert = "Repost detected! Prior posters include: {}".format(reposter_string)
            send_message_to_main_channel(repost_alert)

    except Exception as e:
        print("Error while querying dynamodb for prior examples:", e)
        traceback.print_exc()
        send_info_message("Error ocurred while querying for image")

    insert_item(message, dhash_digest)

    return ok()


def get_reposter_string(dynamo_results):
    return ", ".join(
        map(map_record_to_string, dynamo_results)
    )

def map_record_to_string(record):
    print("attempting to process record:", record)
    name = record["created_by_name"]
    timestamp = datetime.fromtimestamp(record["created_at"]).astimezone(timezone('US/Eastern')).strftime("%m/%d/%Y at %H:%M %p")

    return "{} on {}".format(name, timestamp)

def insert_item(message, dhash_digest):
    try:
        table.put_item(
            Item={
                "id": message.request["id"],
                "image_url": message.get_image_url(),
                "created_at": message.request["created_at"],
                "favorited_by": [], # No one has had a chance to favorite this image
                "created_by_name": message.request["name"],
                "created_by_id": message.request["sender_id"],
                "img_dhash": dhash_digest
            })
    except Exception as e:
        print("Error while inserting item: ", e)
        traceback.print_exc()
        send_info_message("Error ocurred saving new image")

def should_drop_request(message):
    return message.is_bot_post() or not message.is_image_post()

def get_cv2_image(message):
    get_image_response = http.request('GET', message.get_image_url())
    image = np.asarray(bytearray(get_image_response.data), dtype="uint8")
    return cv2.imdecode(image, cv2.IMREAD_COLOR)

def dhash(cv2_image, hash_size=HASH_SIZE):
    gray_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)

    resized = cv2.resize(gray_image, (hash_size + 1, hash_size))

    # Creates 8x8 matrix of true/false
    diff = resized[:, 1:] > resized[:, :-1]

    # Each "pixel" in 8x8 image gets a bit, 2^64 options
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

def ok():
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "why are you reading this huh?"
        }),
    }
