from django.urls import path
from . import views
from .views import add_product

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<slug:category_slug>', views.home, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>',
         views.productPage, name='product_detail'),
    path('cart/add/<int:product_id>', views.add_cart, name='add_cart'),
    path('cart', views.cart_detail, name='cart_detail'),
    path('cart/remove/<int:product_id>', views.cart_remove, name='cart_remove'),
    path('cart/remove_product/<int:product_id>', views.cart_remove_product, name='cart_remove_product'),
    path('thankyou/<int:order_id>', views.thanks_page, name='thanks_page'),
    path('thankyou/<int:order_id>/', views.thankyou, name='thankyou'),
    path('account/create/', views.signupView, name='signup'),
    path('account/signin/', views.signinView, name='signin'),
    path('account/signout/', views.signoutView, name='signout'),
    path('order_history/', views.orderHistory, name='order_history'),
    path('order/<int:order_id>', views.viewOrder, name='order_detail'),
    path('search/', views.search, name='search'),
    path('add-product/', add_product, name='add_product'),
    path('checkout/', views.checkout, name='checkout'),
    path('withdraw-success/', views.withdraw_success, name='withdraw_success'),
    path('withdraw-request/', views.withdraw_request, name='withdraw_request'),
    path('sell-to-us/', views.sell_to_us, name='sell_to_us'),
    path('confirm-received/<int:order_id>/', views.confirm_received, name='confirm_received'),
    path('sell-thank-you/', views.sell_thank_you, name='sell_thank_you'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('seller/<int:user_id>/', views.seller_products, name='seller_products'),
    path('contact/', views.contact, name='contact')
]
