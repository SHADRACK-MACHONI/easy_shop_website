import requests
import base64
from datetime import datetime
from django.conf import settings

def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(api_URL, auth=(consumer_key, consumer_secret))
    json_response = response.json()
    access_token = json_response["access_token"]
    return access_token

def lipa_na_mpesa_online(phone_number, amount, order_id):
    access_token = get_access_token()

    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = shortcode + passkey + timestamp
    encoded_password = base64.b64encode(data_to_encode.encode()).decode('utf-8')

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": "Bearer %s" % access_token}

    payload = {
        "BusinessShortCode": shortcode,
        "Password": encoded_password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"Order-{order_id}",
        "TransactionDesc": "Easy Shop Purchase"
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()