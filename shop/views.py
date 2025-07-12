from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from .models import Product, Order
from .forms import ProductForm, OrderForm
import requests
import datetime
import base64
import json

# M-Pesa Auth
def get_mpesa_access_token():
    consumer_key = 'YOUR_CONSUMER_KEY'
    consumer_secret = 'YOUR_CONSUMER_SECRET'
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(api_URL, auth=(consumer_key, consumer_secret))
    json_response = response.json()
    return json_response['access_token']

def lipa_na_mpesa_online(phone, amount, order_id):
    access_token = get_mpesa_access_token()
    shortcode = '174379'
    passkey = 'YOUR_PASSKEY'

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode('utf-8')

    stk_push_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {'Authorization': 'Bearer ' + access_token}
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": "https://yourdomain.com/store/mpesa-callback/",
        "AccountReference": str(order_id),
        "TransactionDesc": "Payment for EasyShop Order"
    }

    response = requests.post(stk_push_url, json=payload, headers=headers)
    return response.json()

# Pages
@login_required
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.product = product
            order.customer_name = request.user.username
            order.save()
            return redirect('my_orders')
    else:
        form = OrderForm()
    return render(request, 'product_detail.html', {'product': product, 'form': form})

@login_required
def my_orders(request):
    orders = Order.objects.filter(customer_name=request.user.username)
    return render(request, 'my_order.html', {'orders': orders})

@staff_member_required
def admin_dashboard(request):
    orders = Order.objects.all()
    return render(request, 'admin_dashboard.html', {'orders': orders})

# Order status views
@staff_member_required
def update_order_status(request, pk, status):
    order = get_object_or_404(Order, pk=pk)
    if status == 'Out for Delivery':
        order.out_for_delivery = True
    elif status == 'Delivered':
        order.delivered = True
    order.save()
    return redirect('admin_dashboard')

@login_required
def mark_delivered(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.delivered = True
        order.save()
    return redirect('my_orders')

# M-Pesa Payment
@csrf_exempt
def mpesa_callback(request):
    mpesa_body = json.loads(request.body.decode('utf-8'))
    result_code = mpesa_body['Body']['stkCallback']['ResultCode']
    metadata = mpesa_body['Body']['stkCallback']['CallbackMetadata']
    order_id = int(metadata['Item'][0]['Value'])
    order = Order.objects.get(pk=order_id)

    if result_code == 0:
        receipt = metadata['Item'][1]['Value']
        order.payment_confirmed = True
        order.mpesa_receipt = receipt
        order.save()

    return JsonResponse({"Result": "Success"})

@login_required
def initiate_mpesa_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    response = lipa_na_mpesa_online(order.customer_phone, int(order.product.price), order_id)

    checkout_request_id = response.get("CheckoutRequestID")
    if checkout_request_id:
        order.checkout_request_id = checkout_request_id
        order.save()

    return JsonResponse(response)

# Admin Product
@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

# User Registration
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


