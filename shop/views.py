from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Order
from .forms import ProductForm, OrderForm
from django.http import JsonResponse
from .mpesa import lipa_na_mpesa_online
from .models import Order
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, get_object_or_404
import requests
import datetime
import base64

def get_mpesa_access_token():
    consumer_key = 'mciyeGVWIqGBlUOMCfdcjlj1J3s8u0RgrskAf4uKukpCQACZ'
    consumer_secret = 'KOQBGKf727x0kxMpgkLEQPbMH0EtD976PAljlQQEWS3Sgx3zxJWWKbO2GHbpN0AC'
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    response = requests.get(api_URL, auth=(consumer_key, consumer_secret))
    json_response = response.json()
    return json_response['access_token']

def lipa_na_mpesa_online(phone, amount, order_id):
    access_token = get_mpesa_access_token()
    shortcode = '174379'
    passkey = 'N/A'

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

@login_required
def initiate_payment(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == 'POST':
        phone = request.POST.get('phone')
        amount = order.product.price

        order.phone_number = phone
        order.save()

        response = lipa_na_mpesa_online(phone, int(amount), order.id)
        return render(request, 'store/payment_processing.html', {'response': response, 'order': order})
    return render(request, 'store/payment_form.html', {'order': order})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@csrf_exempt
def mpesa_callback(request):
    from django.http import JsonResponse
    import json

    mpesa_body = json.loads(request.body.decode('utf-8'))
    result_code = mpesa_body['Body']['stkCallback']['ResultCode']
    metadata = mpesa_body['Body']['stkCallback']['CallbackMetadata']
    order_id = int(metadata['Item'][0]['Value'])  # This is our AccountReference

    order = Order.objects.get(pk=order_id)
    if result_code == 0:
        receipt = metadata['Item'][1]['Value']
        order.payment_confirmed = True
        order.mpesa_receipt = receipt
        order.save()

    return JsonResponse({"Result": "Success"})

def initiate_mpesa_payment(request, order_id):
    order = Order.objects.get(pk=order_id)
    response = lipa_na_mpesa_online(order.customer_phone, int(order.product.price), order_id)
    
    # Save CheckoutRequestID
    checkout_request_id = response.get("CheckoutRequestID")
    if checkout_request_id:
        order.checkout_request_id = checkout_request_id
        order.save()

    return JsonResponse(response)
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
            order.payment_confirmed = True  # Simulated payment confirmation
            order.save()
            return redirect('home')
    else:
        form = OrderForm()
    return render(request, 'product_detail.html', {'product': product, 'form': form})
@staff_member_required
def admin_dashboard(request):
    orders = Order.objects.exclude(pk__isnull=True)
    return render(request, 'admin_dashboard.html', {'orders': orders})

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

def update_order_status(request, pk, status):
    order = get_object_or_404(Order, pk=pk)
    order.status = status
    if status == 'Out for Delivery':
        order.admin_seen = True
    if status == 'Delivered':
        order.payment_confirmed = True
    order.save()
    return redirect('admin_dashboard')

@staff_member_required
def mark_out_for_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'Out for Delivery'
    order.save()
    return redirect('admin_dashboard')
@login_required
def mark_delivered(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.delivered = True
    order.save()
    return redirect('admin_dashboard')

@login_required
def my_orders(request):
    orders = Order.objects.filter(customer_name=request.user.username)
    return render(request, 'my_order.html', {'orders': orders})

