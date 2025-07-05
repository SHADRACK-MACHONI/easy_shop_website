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
    data = json.loads(request.body.decode('utf-8'))

    try:
        checkout_id = data["Body"]["stkCallback"]["CheckoutRequestID"]
        result_code = data["Body"]["stkCallback"]["ResultCode"]

        if result_code == 0:
            mpesa_receipt_number = next(
                (item["Value"] for item in data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
                 if item["Name"] == "MpesaReceiptNumber"), None
            )

            # Find the order by checkout_request_id
            order = Order.objects.get(checkout_request_id=checkout_id)
            order.payment_confirmed = True
            order.mpesa_transaction_id = mpesa_receipt_number
            order.save()
    except Exception as e:
        print("M-Pesa callback error:", e)

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

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
def mark_delivered(request, pk):
    order = get_object_or_404(Order, pk=pk, customer_phone=request.user.username)
    if request.method == 'POST':
        order.status = 'Delivered'
        order.save()
    return redirect('my_orders')

@login_required
def my_orders(request):
    orders = Order.objects.filter(customer_name=request.user.username)
    return render(request, 'my_order.html', {'orders': orders})

