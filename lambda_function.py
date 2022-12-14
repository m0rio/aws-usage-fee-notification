import os
import boto3
import json
import calendar
from datetime import datetime, date
from linebot import LineBotApi
from linebot.models import TextSendMessage

ce_client = boto3.client('ce')

# Line API利用に必要な変数設定
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
line_bot_api = LineBotApi(channel_access_token)

user_id = os.getenv('USER_ID')

# Main
def lambda_handler(event, context):

    # 月初から今日までのAWS利用料金の取得
    today = datetime.today()
    first_day = today.replace(day=1)

    # Line送信用メッセージの作成
    message = get_aws_cost(first_day, today)

    # Lineにメッセージ送信
    message_obj = TextSendMessage(text=message)
    line_bot_api.push_message(user_id, message_obj)

    return {
        'statusCode': 200,
        'body': ''
    }


# 指定した期間のAWS利用料を返す関数
def get_aws_cost(start_day, end_day):
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': datetime.strftime(start_day, '%Y-%m-%d'),
                'End': datetime.strftime(end_day, '%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
        )
        aws_cost = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
        result_message = create_message(start_day, end_day, aws_cost)
    except Exception as e:
        # boto3 Client error でも以下の文が表示される
        err_res = e.response['Error']['Message']
        message = '[Error]' + '\n' + 'specify up to the past 12 months.'
        result_message = datetime.strftime(start_day, '%Y-%m-%d') + "-" + datetime.strftime(
            end_day, '%Y-%m-%d') + "\n" + message + "\n" + err_res
    return result_message


# 指定した年月の初日と最終日を返す関数
def get_frst_last_date(year, month):
    return calendar.monthrange(year, month)


# Lineに送信するメッセージを作成する関数
def create_message(start_day, end_day, aws_cost):

    message = '開始日: ' + start_day.strftime('%Y年%m月%d日') + '\n' + '終了日: ' + end_day.strftime(
        '%Y年%m月%d日') + '\n' + 'AWS利用料: $' + str(round(float(aws_cost), 1))
    return message
