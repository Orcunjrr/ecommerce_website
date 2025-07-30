from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from .models import Product, SellRequest, WithdrawRequest

class OrderCreateForm(forms.Form):
    billingName = forms.CharField(max_length=250)
    billingAddress1 = forms.CharField(max_length=250)
    billingCity = forms.CharField(max_length=100)
    billingPostcode = forms.CharField(max_length=20)
    billingCountry = forms.CharField(max_length=100)
    emailAddress = forms.EmailField()

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=250, help_text='eg. youremail@gmail.com')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password1', 'password2', 'email')

class ContactForm(forms.Form):
    subject = forms.CharField(max_length=50, required=True)
    name = forms.CharField(max_length=20, required=True)
    from_email = forms.EmailField(max_length=50, required=True)
    message = forms.CharField(
        max_length=500,
        widget=forms.Textarea(),
        help_text='Write here your message!'
    )
    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'base_product', 'description', 'category', 'price', 'image', 'stock', 'available']

class SellRequestForm(forms.ModelForm):
    class Meta:
        model = SellRequest
        fields = ['product_name', 'description', 'offered_price', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class CheckoutForm(forms.Form):
    billingName = forms.CharField(max_length=250)
    billingAddress1 = forms.CharField(max_length=250)
    billingCity = forms.CharField(max_length=100)
    billingPostcode = forms.CharField(max_length=20)
    billingCountry = forms.CharField(max_length=100)
    shippingName = forms.CharField(max_length=250)
    shippingAddress1 = forms.CharField(max_length=250)
    shippingCity = forms.CharField(max_length=100)
    shippingPostcode = forms.CharField(max_length=20)
    shippingCountry = forms.CharField(max_length=100)

class WithdrawRequestForm(forms.ModelForm):
    class Meta:
        model = WithdrawRequest
        fields = ['amount', 'iban']
