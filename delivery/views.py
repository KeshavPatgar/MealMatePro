from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.views.decorators.cache import never_cache
from django.contrib import messages

from .models import User, Restaurant, Item, Cart

import razorpay
from django.conf import settings

# Create your views here.
def index(request):
    return render(request, 'index.html')

@never_cache
def open_signin(request):
    # If already logged in, skip the signin page
    if request.session.get('username'):
        if request.session.get('username') == 'admin':
            return redirect('admin_home')
        return redirect('customer_home')
    return render(request, 'signin.html')

def open_signup(request):
    return render(request, 'signup.html')

@never_cache
def profile(request, username):
    if request.session.get('username') != username:
        return redirect('open_signin')
        
    customer = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
        password = request.POST.get('new_secure_p')
        
        if email: customer.email = email
        if mobile: customer.mobile = mobile
        if address: customer.address = address
        if password: customer.password = password
        
        customer.save()
        messages.success(request, 'Profile updated successfully!')
        # Redirect back to profile after POST to prevent form resubmission errors
        return redirect('profile', username=username)
        
    return render(request, 'profile.html', {'customer': customer, 'username': username})

@never_cache
def logout_view(request):
    request.session.flush()
    return redirect('open_signin')

@never_cache
def admin_home(request):
    if request.session.get('username') != 'admin':
        return redirect('open_signin')
    return render(request, 'admin_home.html')

@never_cache
def customer_home(request):
    username = request.session.get('username', '')
    if not username:
        return redirect('open_signin')
        
    restaurantList = Restaurant.objects.all()
    return render(request, 'customer_home.html', {"restaurantList": restaurantList, "username": username})

# def signin(request):
#     #DB's Data
#     user = "keshav"
#     pw = "123"
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         if user == username and pw == password:
#             # return HttpResponse(f"Username : {username} password : {password}")
#             return render(request, "success.html") 
#         else:
#             #return HttpResponse(f"Invalid response")
#             return render(request, "fail.html") 
    
#     else:
#         return HttpResponse("Invalid Request")

# def signin(request):
#     if request.method == 'POST':
#         # Fetching data from the form
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         try:
#             # Check if a user exists with the provided credentials
#             customer = User.objects.get(username=username, password=password)
#             return render(request, 'success.html')
#         except User.DoesNotExist:
#             # If credentials are invalid, show a failure page
#             return render(request, 'fail.html')
#     else:
#         return HttpResponse("Invalid Request")

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            User.objects.get(username = username, password = password)
            request.session['username'] = username
            if username == 'admin':
                return redirect('admin_home')
            else:
                return redirect('customer_home')

        except User.DoesNotExist:
            return render(request, 'fail.html')
    return redirect('open_signin')
    
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')

        if User.objects.filter(username=username).exists():
            return HttpResponse("This username is already registered. Please use a different email.")
        
        user = User(username=username, password=password, email=email, mobile=mobile, address=address)
        user.save()

        return redirect('open_signin') 
    else:
        return HttpResponse(f"Invalid response, Duplicate User")
    
def open_add_restaurant(request):
    return render(request, 'add_restaurant.html')

def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')
        
        try:
            Restaurant.objects.get(name = name)
            return HttpResponse("Duplicate restaurant!")
            
        except:
            Restaurant.objects.create(
                name = name,
                picture = picture,
                cuisine = cuisine,
                rating = rating,
            )
        return redirect('admin_home')

def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurants.html',{"restaurantList" : restaurantList})

def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    return render(request, 'update_restaurant.html', {"restaurant" : restaurant})

def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')
        
        restaurant.name = name
        restaurant.picture = picture
        restaurant.cuisine = cuisine
        restaurant.rating = rating

        restaurant.save()

    return redirect('open_show_restaurant')

def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    restaurant.delete()

    return redirect('open_show_restaurant')

def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    #itemList = Item.objects.all()
    return render(request, 'update_menu.html',{"itemList" : itemList, "restaurant" : restaurant})

def update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        vegeterian = request.POST.get('vegeterian') == 'on'
        picture = request.POST.get('picture')
        
        try:
            Item.objects.get(name = name)
            return HttpResponse("Duplicate item!")
        except:
            Item.objects.create(
                restaurant = restaurant,
                name = name,
                description = description,
                price = price,
                vegeterian = vegeterian,
                picture = picture,
            )
    return redirect('open_update_menu', restaurant_id=restaurant_id)

def delete_menu_item(request, restaurant_id, item_id):
    item = get_object_or_404(Item, id=item_id)
    item.delete()
    
    return redirect('open_update_menu', restaurant_id=restaurant_id)

def open_edit_menu_item(request, restaurant_id, item_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    item = get_object_or_404(Item, id=item_id)
    return render(request, 'edit_menu_item.html', {"restaurant": restaurant, "item": item})

def edit_menu_item(request, restaurant_id, item_id):
    item = get_object_or_404(Item, id=item_id)
    
    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.description = request.POST.get('description')
        item.price = request.POST.get('price')
        item.vegeterian = request.POST.get('vegeterian') == 'on'
        
        picture = request.POST.get('picture')
        if picture:
            item.picture = picture
            
        item.save()
        
    return redirect('open_update_menu', restaurant_id=restaurant_id)

def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    #return HttpResponse("Items collected")
    #itemList = Item.objects.all()
    return render(request, 'customer_menu.html'
                  ,{"itemList" : itemList,
                     "restaurant" : restaurant, 
                     "username":username})

def add_to_cart(request, item_id, username):
    item = Item.objects.get(id = item_id)
    customer = User.objects.get(username = username)

    cart, created = Cart.objects.get_or_create(customer = customer)
    is_new_item = not cart.items.filter(id=item.id).exists()

    cart.items.add(item)

    # Quantity management using session
    cart_qty = request.session.get('cart_qty', {})
    item_id_str = str(item_id)
    
    if is_new_item:
        cart_qty[item_id_str] = 1
    else:
        cart_qty[item_id_str] = cart_qty.get(item_id_str, 1) + 1
        
    request.session['cart_qty'] = cart_qty

    return redirect('show_cart', username=username)

def remove_from_cart(request, item_id, username):
    item = get_object_or_404(Item, id=item_id)
    customer = get_object_or_404(User, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    
    cart_qty = request.session.get('cart_qty', {})
    item_id_str = str(item_id)
    
    if request.GET.get('delete') == '1':
        if item_id_str in cart_qty:
            del cart_qty[item_id_str]
            request.session['cart_qty'] = cart_qty
        if cart:
            cart.items.remove(item)
    else:
        current_qty = cart_qty.get(item_id_str, 1)
        if current_qty > 1:
            cart_qty[item_id_str] = current_qty - 1
            request.session['cart_qty'] = cart_qty
        else:
            if item_id_str in cart_qty:
                del cart_qty[item_id_str]
                request.session['cart_qty'] = cart_qty
            if cart:
                cart.items.remove(item)
        
    return redirect('show_cart', username=username)

@never_cache
def show_cart(request, username):
    if request.session.get('username') != username:
        return redirect('open_signin')
        
    customer = User.objects.get(username = username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    
    cart_qty = request.session.get('cart_qty', {})
    total_price = 0
    for item in items:
        item.quantity = cart_qty.get(str(item.id), 1)
        item.subtotal = item.price * item.quantity
        total_price += item.subtotal

    return render(request, 'cart.html',{"itemList" : items, "total_price" : total_price, "username":username})

@never_cache
def checkout(request, username):
    if request.session.get('username') != username:
        return redirect('open_signin')
        
    # Fetch customer and their cart
    customer = get_object_or_404(User, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    
    cart_qty = request.session.get('cart_qty', {})
    total_price = 0
    for item in cart_items:
        item.quantity = cart_qty.get(str(item.id), 1)
        item.subtotal = item.price * item.quantity
        total_price += item.subtotal

    if total_price == 0:
        return render(request, 'checkout.html', {
            'error': 'Your cart is empty!',
        })
    
    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order
    order_data = {
        'amount': int(total_price * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1',  # Automatically capture payment
    }
    order = client.order.create(data=order_data)

    # Pass the order details to the frontend
    return render(request, 'checkout.html', {
        'username': username,
        'cart_items': cart_items,
        'total_price': total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],  # Razorpay order ID
        'amount': total_price,
    })

@never_cache
def orders(request, username):
    if request.session.get('username') != username:
        return redirect('open_signin')
        
    customer = get_object_or_404(User, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    # Fetch cart items and total price before clearing the cart
    cart_items = cart.items.all() if cart else []
    cart_qty = request.session.get('cart_qty', {})
    total_price = 0
    for item in cart_items:
        item.quantity = cart_qty.get(str(item.id), 1)
        item.subtotal = item.price * item.quantity
        total_price += item.subtotal

    # Clear the cart after fetching its details
    if cart:
        cart.items.clear()
    if 'cart_qty' in request.session:
        del request.session['cart_qty']

    return render(request, 'orders.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
    })

def search(request):
    query = request.GET.get('q', '')
    username = request.GET.get('username', '')
    if query:
        itemList = Item.objects.filter(Q(name__icontains=query) | Q(restaurant__name__icontains=query)).distinct()
    else:
        itemList = Item.objects.all()
        
    return render(request, 'customer_menu.html', {
        'itemList': itemList,
        'search_query': query,
        'username': username
    })