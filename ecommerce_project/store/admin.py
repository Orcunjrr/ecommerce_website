from django.contrib import admin
from .models import Category, Product, Order, OrderItem, SellRequest, Review, WithdrawRequest, UserProfile
# Register your models here.


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Category, CategoryAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'available', 'created', 'updated']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20


admin.site.register(Product, ProductAdmin)


class OrderItemAdmin(admin.TabularInline):
    model = OrderItem
    fieldsets = [
        ('Product', {'fields': ['product'], }),
        ('Quantity', {'fields': ['quantity'], }),
        ('Price', {'fields': ['price'], }),
    ]
    readonly_fields = ['product', 'quantity', 'price']
    can_delete = False
    max_num = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'is_paid', 'is_delivered', 'buyer_confirmed', 'shipping_status', 'billingName', 'emailAddress', 'created']
    list_display_links = ('id', 'billingName')
    search_fields = ['id', 'billingName', 'emailAddress']
    readonly_fields = ['id', 'token', 'total', 'emailAddress', 'created',
                       'billingName', 'billingAddress1', 'billingCity', 'billingPostcode',
                       'billingCountry', 'shippingName', 'shippingAddress1', 'shippingCity',
                       'shippingPostcode', 'shippingCountry']

    fieldsets = [
        ('ORDER INFORMATION', {'fields': ['id', 'token', 'total', 'created', 'shipping_status', 'is_delivered', 'buyer_confirmed']}),
        ('BILLING INFORMATION', {'fields': ['billingName', 'billingAddress1',
                                            'billingCity', 'billingPostcode', 'billingCountry', 'emailAddress']}),
        ('SHIPPING INFORMATION', {'fields': ['shippingName', 'shippingAddress1',
                                             'shippingCity', 'shippingPostcode', 'shippingCountry']}),
    ]

    inlines = [
        OrderItemAdmin,
    ]

    def has_delete_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def colored_shipping_status(self, obj):
        status = obj.shipping_status
        if status == 'delivered':
            return format_html('<span style="color:green;">✔ Delivered</span>')
        elif status == 'shipped':
            return format_html('<span style="color:orange;">📦 Shipped</span>')
        elif status == 'in_transit':
            return format_html('<span style="color:orange;">⏳ In Transit</span>')
        elif status == 'order_received':
            return format_html('<span style="color:blue;">📥 Order Received</span>')
        return obj.get_shipping_status_display()

    colored_shipping_status.short_description = 'Shipping Status'

admin.site.register(Review)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'balance']

@admin.register(SellRequest)
class SellRequestAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'user', 'offered_price', 'is_approved']
    actions = ['approve_requests']

    def approve_requests(self, request, queryset):
        for req in queryset.filter(is_approved=False):
            profile = UserProfile.objects.get(user=req.user)
            profile.balance += req.offered_price
            profile.save()
            req.is_approved = True
            req.save()
        self.message_user(request, "Selected Requests Approved and Balances Updated.")
    approve_requests.short_description = "Approve Requests and Add Balance"

@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'iban', 'is_processed', 'created_at']
    list_filter = ['is_processed']
    actions = ['mark_as_processed']

    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
