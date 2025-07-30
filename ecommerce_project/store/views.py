from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review
from django.core.exceptions import ObjectDoesNotExist
import stripe
from django.conf import settings
from django.contrib.auth.models import Group, User
from .forms import SignUpForm, ContactForm, ProductForm, CheckoutForm, SellRequestForm, WithdrawRequestForm
from django.http import HttpResponseForbidden
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template.loader import get_template
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib import messages
import smtplib
import ssl
# from email.message import EmailMessage
from django.urls import reverse
from django.utils.text import slugify
import uuid



def home(request, category_slug=None):
    category_page = None
    products_list = None
    if category_slug != None:
        category_page = get_object_or_404(Category, slug=category_slug)
        products_list = Product.objects.filter(category=category_page, available=True)
    else:
        products_list = Product.objects.all().filter(available=True)

    paginator = Paginator(products_list, 4)

    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1

    try:
        products = paginator.page(page)
    except(EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)

    return render(request, 'home.html', {'category': category_page, 'products': products})


def productPage(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Product.DoesNotExist:
        raise Http404("Product doesnt exist")


    other_variants = Product.objects.filter(base_product=product.base_product).exclude(id=product.id) if product.base_product else []


    if request.method == 'POST' and request.user.is_authenticated and request.POST['content'].strip() != '':
        Review.objects.create(product=product, user=request.user, content=request.POST['content'])

    reviews = Review.objects.filter(product=product)

    return render(request, 'product.html', {
        'product': product,
        'reviews': reviews,
        'other_variants': other_variants,
    })




def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        cart.save()
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart
        )
        cart_item.save()

    return redirect('cart_detail')


def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            counter += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = int(total * 100)
    description = 'Z-Store - New Order'
    data_key = settings.STRIPE_PUBLISHABLE_KEY
    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']
            email = request.POST['stripeEmail']
            billingName = request.POST['stripeBillingName']
            billingAddress1 = request.POST['stripeBillingAddressLine1']
            billingCity = request.POST['stripeBillingAddressCity']
            billingPostcode = request.POST['stripeBillingAddressZip']
            billingCountry = request.POST['stripeBillingAddressCountryCode']
            shippingName = request.POST['stripeShippingName']
            shippingAddress1 = request.POST['stripeShippingAddressLine1']
            shippingCity = request.POST['stripeShippingAddressCity']
            shippingPostcode = request.POST['stripeShippingAddressZip']
            shippingCountry = request.POST['stripeShippingAddressCountryCode']
            customer = stripe.Customer.create(
                email=email,
                source=token
            )
            charge = stripe.Charge.create(
                amount=stripe_total,
                currency='usd',
                description=description,
                customer=customer.id
            )

            try:
                order_details = Order.objects.create(
                    token=token,
                    total=total,
                    emailAddress=email,
                    billingName=billingName,
                    billingAddress1=billingAddress1,
                    billingCity=billingCity,
                    billingPostcode=billingPostcode,
                    billingCountry=billingCountry,
                    shippingName=shippingName,
                    shippingAddress1=shippingAddress1,
                    shippingCity=shippingCity,
                    shippingPostcode=shippingPostcode,
                    shippingCountry=shippingCountry
                )
                order_details.save()
                for order_item in cart_items:
                    or_item = OrderItem.objects.create(
                        product=order_item.product.name,
                        quantity=order_item.quantity,
                        price=order_item.product.price,
                        order=order_details
                    )
                    or_item.save()


                    products = Product.objects.get(id=order_item.product.id)
                    products.stock = int(order_item.product.stock - order_item.quantity)
                    products.save()
                    order_item.delete()


                    print('the order has been created')
                try:
                    sendEmail(order_details.id)
                    print('The order email has been sent')
                except IOError as e:
                    return e

                return redirect('thanks_page', order_details.id)
            except ObjectDoesNotExist:
                pass

        except stripe.error.CardError as e:
            return False, e

    return render(request, 'cart.html', dict(cart_items=cart_items, total=total, counter=counter, data_key=data_key, stripe_total=stripe_total, description=description))


def cart_remove(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_detail')


def cart_remove_product(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart_detail')


def thanks_page(request, order_id):
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thankyou.html', {'customer_order': customer_order})

@login_required
def thankyou(request, order_id):
    from django.shortcuts import get_object_or_404

    order = get_object_or_404(Order, id=order_id, user=request.user)


    checkout_data = request.session.get('checkout_data', {})


    order.billingName = checkout_data.get('billingName')
    order.billingAddress1 = checkout_data.get('billingAddress1')
    order.billingCity = checkout_data.get('billingCity')
    order.billingPostcode = checkout_data.get('billingPostcode')
    order.billingCountry = checkout_data.get('billingCountry')
    order.shippingName = checkout_data.get('shippingName')
    order.shippingAddress1 = checkout_data.get('shippingAddress1')
    order.shippingCity = checkout_data.get('shippingCity')
    order.shippingPostcode = checkout_data.get('shippingPostcode')
    order.shippingCountry = checkout_data.get('shippingCountry')
    order.emailAddress = request.user.email
    order.is_paid = True
    order.save()


    cart_id = _cart_id(request)
    try:
        cart = Cart.objects.get(cart_id=cart_id)
    except Cart.DoesNotExist:
        return redirect('home')

    cart_items = CartItem.objects.filter(cart=cart, active=True)
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )
        item.product.stock -= item.quantity
        item.product.save()
        item.delete()

    cart.delete()


    if 'checkout_data' in request.session:
        del request.session['checkout_data']

    return render(request, 'thankyou.html', {'customer_order': order})

def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)
            login(request, signup_user)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def signinView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('signin')


@login_required(redirect_field_name='next', login_url='signin')
def orderHistory(request):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order_details = Order.objects.filter(emailAddress=email)
        print(email)
        print(order_details)
    return render(request, 'orders_list.html', {'order_details': order_details})


@login_required(redirect_field_name='next', login_url='signin')
def viewOrder(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
    return render(request, 'order_detail.html', {'order': order, 'order_items': order_items})


def search(request):
    products = Product.objects.filter(name__contains=request.GET['title'])
    return render(request, 'home.html', {'products': products})


def sendEmail(order_id):
    transaction = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=transaction)

    try:
        subject = "ZStore - New Order #{}".format(transaction.id)
        from_email = "bale11.ok@gmail.com"
        print("Gönderilecek e-posta:", transaction.emailAddress)
        to_email = [transaction.emailAddress]

        context = {
            'transaction': transaction,
            'order_items': order_items
        }

        message = get_template('email/email.html').render(context)

        msg = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=to_email,
        )
        msg.content_subtype = 'html'
        msg.send()
        print("Email sent successfully!")

    except Exception as e:
        print(f"Email sending failed: {e}")
        return e

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data.get('subject')
            from_email = form.cleaned_data.get('from_email')
            message = form.cleaned_data.get('message')
            name = form.cleaned_data.get('name')

            message_format = "{0} has sent you a new message:\n\n{1}".format(name, message)

            msg = EmailMessage(
                subject,
                message_format,
                to=['orcun.karaarslan@stu.pirireis.edu.tr'],
                from_email=from_email
            )

            msg.send()

            return render(request, 'contact_success.html')

    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})

@csrf_exempt
@login_required
def create_checkout_session(request):
    import stripe
    from django.urls import reverse

    stripe.api_key = settings.STRIPE_SECRET_KEY

    cart_id = _cart_id(request)
    try:
        cart = Cart.objects.get(cart_id=cart_id)
    except Cart.DoesNotExist:
        return redirect('cart_detail')

    cart_items = CartItem.objects.filter(cart=cart, active=True)
    if not cart_items.exists():
        return redirect('cart_detail')

    total = sum(item.product.price * item.quantity for item in cart_items)


    order = Order.objects.create(
        user=request.user,
        emailAddress=request.user.email,
        total=total,
        is_paid=False
    )
    sendEmail(order.id)
    line_items = []
    for item in cart_items:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(item.product.price * 100),
                'product_data': {
                    'name': item.product.name,
                },
            },
            'quantity': item.quantity,
        })

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri(reverse('thankyou', args=[order.id])),
        cancel_url=request.build_absolute_uri(reverse('cart_detail')),
    )

    return redirect(session.url)

def checkout(request):
    if request.method == 'POST':

        billingName = request.POST.get('billingName')
        billingAddress1 = request.POST.get('billingAddress1')
        billingCity = request.POST.get('billingCity')
        billingPostcode = request.POST.get('billingPostcode')
        billingCountry = request.POST.get('billingCountry')

        shippingName = request.POST.get('shippingName')
        shippingAddress1 = request.POST.get('shippingAddress1')
        shippingCity = request.POST.get('shippingCity')
        shippingPostcode = request.POST.get('shippingPostcode')
        shippingCountry = request.POST.get('shippingCountry')


        request.session['checkout_data'] = {
            'billingName': billingName,
            'billingAddress1': billingAddress1,
            'billingCity': billingCity,
            'billingPostcode': billingPostcode,
            'billingCountry': billingCountry,
            'shippingName': shippingName,
            'shippingAddress1': shippingAddress1,
            'shippingCity': shippingCity,
            'shippingPostcode': shippingPostcode,
            'shippingCountry': shippingCountry,
        }

        return redirect('create_checkout_session')

    return render(request, 'checkout.html')

@login_required
def add_product(request):
    if request.user.userprofile.role != 'seller':
        return HttpResponseForbidden("Ürün eklemek için yetkiniz yok.")

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.slug = slugify(product.name) + "-" + str(uuid.uuid4())[:8]
            product.save()
            return redirect('home')
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form})

def seller_products(request, user_id):
    seller = get_object_or_404(User, id=user_id)
    products = Product.objects.filter(user=seller)

    return render(request, 'seller_products.html', {'seller': seller, 'products': products})

@login_required
def sell_to_us(request):
    if request.method == 'POST':
        form = SellRequestForm(request.POST, request.FILES)
        if form.is_valid():
            sell_request = form.save(commit=False)
            sell_request.user = request.user
            sell_request.save()
            return redirect('sell_thank_you')
    else:
        form = SellRequestForm()
    return render(request, 'sell_to_us.html', {'form': form})

def sell_thank_you(request):
    return render(request, 'sell_thank_you.html')

@login_required
def withdraw_request(request):
    if request.method == 'POST':
        form = WithdrawRequestForm(request.POST)
        if form.is_valid():
            withdraw = form.save(commit=False)
            withdraw.user = request.user
            if withdraw.amount <= request.user.userprofile.balance:
                withdraw.save()
                request.user.userprofile.balance -= withdraw.amount
                request.user.userprofile.save()
                messages.success(request, "Your withdrawal request has been received.")
            else:
                messages.error(request, "Insufficient funds.")
            return redirect('withdraw_success')
    else:
        form = WithdrawRequestForm()
    return render(request, 'withdraw_request.html', {'form': form})

from django.shortcuts import render

def withdraw_success(request):
    return render(request, 'withdraw_success.html')

@login_required
def confirm_received(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST' and order.is_delivered:
        order.buyer_confirmed = True
        order.save()
        messages.success(request, "Delivery confirmed.")
    return redirect('order_detail', order_id=order.id)
