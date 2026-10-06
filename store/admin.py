from django.contrib import admin
from .models import (
    SkinType, UsageType, Category, Product, ProductActiveIngredient,
    ProductImage, BeforeAfter, Review, SpecialOffer, ProductVideo, 
    ContactMessage, Order, OrderItem, Cart, CartItem, Payment, Wishlist, WishlistItem,
    Coupon, Wilaya
)


# ==========================================
# 1. INLINES (COMPOSANTS IMBRIQUÉS)
# ==========================================

class ProductActiveIngredientInline(admin.TabularInline):
    model = ProductActiveIngredient
    extra = 1
    verbose_name = "Principe Actif & Action"
    verbose_name_plural = "Principes Actifs & Méthodes de Réparation"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2
    fields = ['image', 'alt_text']


class BeforeAfterInline(admin.StackedInline):
    model = BeforeAfter
    extra = 1
    max_num = 1


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'price', 'quantity', 'get_cost']
    readonly_fields = ['get_cost']
    extra = 1
    can_delete = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')

    def get_cost(self, obj):
        if obj.id:
            return f"{obj.get_cost()} DZD"
        return "0 DZD"
    get_cost.short_description = "Sous-total (DZD)"


class CartItemInline(admin.TabularInline):
    model = CartItem
    readonly_fields = ['product', 'quantity', 'get_cost']
    extra = 0
    can_delete = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')

    def get_cost(self, obj):
        if obj.id and obj.product:
            return f"{obj.get_total_price()} DZD"
        return "0 DZD"
    get_cost.short_description = "Sous-total (DZD)"


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at', 'paid_at', 'raw_response']
    can_delete = False


# ==========================================
# 2. CONFIGURATION DE L'ADMINISTRATION
# ==========================================

@admin.register(SkinType)
class SkinTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(UsageType)
class UsageTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'discount_price', 'stock', 'sales_count', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured', 'category', 'skin_types', 'usage_types']
    list_editable = ['price', 'discount_price', 'stock', 'is_active', 'is_featured']
    search_fields = ['name', 'description', 'ingredients']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['skin_types', 'usage_types']
    
    inlines = [ProductActiveIngredientInline, ProductImageInline, BeforeAfterInline]
    
    # AJOUT DE 'hover_image' DANS LES FIELDSETS CI-DESSOUS
    fieldsets = (
        ("Informations Principales", {
            'fields': ('name', 'slug', 'category', 'skin_types', 'usage_types', 'main_image', 'hover_image')
        }),
        ("Tarification & Stock", {
            'fields': ('price', 'discount_price', 'stock', 'sales_count', 'is_active', 'is_featured')
        }),
        ("Fiche Technique & Composition", {
            'fields': ('short_description', 'description', 'formula', 'ingredients', 'benefits', 'usage_instructions')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'product', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'created_at']
    list_editable = ['is_approved']
    search_fields = ['user_name', 'comment', 'product__name']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


from django.contrib import admin
from .models import SpecialOffer

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'special_price', 'display_products', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    filter_horizontal = ('products',)  # Permet une jolie sélection multiple dans le panneau admin

    # Méthode pour afficher la liste des produits dans le tableau d'administration
    def display_products(self, obj):
        return ", ".join([p.name for p in obj.products.all()])
    display_products.short_description = 'Produits inclus'

@admin.register(ProductVideo)
class ProductVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'product']
    search_fields = ['title', 'product__name']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    list_editable = ['is_read']
    readonly_fields = ['full_name', 'email', 'phone', 'subject', 'message', 'created_at']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'min_order_amount', 'valid_from', 'valid_until', 'used_count', 'is_active']
    list_filter = ['is_active', 'valid_from', 'valid_until']
    search_fields = ['code']
    list_editable = ['is_active']

from django.contrib import admin
from .models import Wilaya

class WilayaAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'desk_price', 'home_price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('code',)
    list_editable = ('is_active', 'desk_price', 'home_price')

admin.site.register(Wilaya, WilayaAdmin)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone', 'wilaya', 'commune', 'get_final_total_display', 'status', 'is_paid', 'payment_method', 'created_at']
    list_filter = ['status', 'is_paid', 'payment_method', 'wilaya', 'created_at']
    list_editable = ['status', 'is_paid']
    search_fields = ['id', 'full_name', 'phone', 'tracking_code', 'address']
    
    readonly_fields = ['total_amount', 'get_final_total_display', 'created_at', 'updated_at']
    inlines = [OrderItemInline, PaymentInline]
    
    fieldsets = (
        ("Client & Adresse de Livraison", {
            'fields': ('user', 'full_name', 'phone', 'wilaya', 'commune', 'address')
        }),
        ("Détails Financiers & Code Promo", {
            'fields': ('total_amount', 'shipping_cost', 'discount_amount', 'coupon', 'get_final_total_display', 'payment_method', 'status', 'is_paid', 'tracking_code')
        }),
        ("Horodatage", {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'coupon')

    def get_final_total_display(self, obj):
        return f"{obj.get_final_total} DZD"
    get_final_total_display.short_description = "Total TTC (DZD)"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_owner', 'session_key', 'get_items_count', 'get_total_amount', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'session_key']
    readonly_fields = ['created_at', 'updated_at', 'get_total_amount']
    inlines = [CartItemInline]

    fieldsets = (
        ("Propriétaire du Panier", {
            'fields': ('user', 'session_key')
        }),
        ("Détails & Horodatage", {
            'fields': ('get_total_amount', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')

    def get_owner(self, obj):
        if obj.user:
            return f"👤 {obj.user.username}"
        return "🕵️ Invité (Session)"
    get_owner.short_description = "Propriétaire"

    def get_items_count(self, obj):
        return sum(item.quantity for item in obj.items.all())
    get_items_count.short_description = "Nb Articles"

    def get_total_amount(self, obj):
        return f"{obj.total_price} DZD"
    get_total_amount.short_description = "Total Panier (DZD)"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'get_item_total']
    list_filter = ['cart__created_at']
    search_fields = ['product__name', 'cart__user__username', 'cart__session_key']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart', 'product')

    def get_item_total(self, obj):
        return f"{obj.get_total_price()} DZD"
    get_item_total.short_description = "Sous-total (DZD)"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'method', 'amount', 'status', 'transaction_id', 'created_at', 'paid_at']
    list_filter = ['method', 'status', 'created_at']
    search_fields = ['order__id', 'transaction_id', 'order__full_name', 'order__phone']
    readonly_fields = ['created_at', 'paid_at', 'raw_response']

    fieldsets = (
        ("Détails de la Commande", {
            'fields': ('order', 'amount')
        }),
        ("Mode & Statut de Paiement", {
            'fields': ('method', 'status', 'transaction_id')
        }),
        ("Dates & Métadonnées", {
            'fields': ('created_at', 'paid_at', 'raw_response')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'get_items_count', 'created_at']
    search_fields = ['user__username', 'user__email']
    inlines = [WishlistItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')

    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = "Nb Produits"