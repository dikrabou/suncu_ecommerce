from django.urls import path
from .views import home_view
from .views import catalog_view,product_detail,add_to_cart,store_review,about_view,remove_from_cart,search_api,contact_view, update_cart_qty,get_cart_json,checkout_view,buy_now_view,order_success_view,promo_products_list
urlpatterns = [
 path('', home_view, name='home'),
    path('catalog/<slug:usage_slug>/', catalog_view, name='catalog'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    
    # API Panier AJAX
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/get/', get_cart_json, name='get_cart_json'),
    path('cart/update/<int:product_id>/', update_cart_qty, name='update_cart_qty'),
    path('cart/remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout_view, name='checkout'),
    path('buy-now/<int:product_id>/', buy_now_view, name='buy_now'),
    path('order-confirmation/<int:order_id>/',order_success_view, name='order_success'),
    path('promotions/', promo_products_list, name='promo_products_list'),
    path('api/search/', search_api, name='search_api'),
    path('contact/', contact_view, name='contact'),
    path('about/', about_view, name='about'),
    path('api/reviews/store/', store_review, name='store_review'),
]