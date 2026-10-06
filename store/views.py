from django.db.models import F
from django.shortcuts import render
from .models import Product, ProductVideo, Review, SpecialOffer, UsageType

from django.db.models import F
from django.shortcuts import render
from .models import Product, SpecialOffer, UsageType, ProductVideo, Review


def home_view(request):
    # 1. Produits essentiels (Correction du slice + exists)
    essential_products = Product.objects.filter(
        is_active=True, is_featured=True
    )
    
    # On vérifie l'existence AVANT de faire le slice [:8]
    if not essential_products.exists():
        essential_products = Product.objects.filter(is_active=True).order_by(
            '-sales_count', '-created_at'
        )
    essential_products = essential_products[:8]

    # 2. Produits en promotion
    promo_products = (
        Product.objects.filter(
            is_active=True,
            discount_price__isnull=False,
            discount_price__lt=F('price'),
        )
        .select_related('category')
        .prefetch_related('videos')[:4]
    )

    # 3. Offre spéciale (Dernière offre active + chargement des produits liés)
    special_offer = (
        SpecialOffer.objects.filter(is_active=True)
        .prefetch_related('products')
        .last()
    )

    # 4. Types d'usage et vidéos
    usage_types = UsageType.objects.all()
    product_videos = ProductVideo.objects.select_related('product').order_by(
        'order', 'id'
    )[:5]

    # 5. Photos des avis clients
    review_images = (
        Review.objects.filter(is_approved=True, image__isnull=False)
        .exclude(image='')
        .select_related('product')[:8]
    )

    context = {
        'essential_products': essential_products,
        'promo_products': promo_products,
        'special_offer': special_offer,
        'usage_types': usage_types,
        'product_videos': product_videos,
        'review_images': review_images,
    }
    return render(request, 'store/index.html', context)
from django.shortcuts import render, get_object_or_404
from .models import UsageType, Product, BeforeAfter

def catalog_view(request, usage_slug=None):
    # Récupère l'objet UsageType ou renvoie une erreur 404
    current_usage = get_object_or_404(UsageType, slug=usage_slug)
    
    # Récupère tous les produits actifs associés à cet usage_type
    products = Product.objects.filter(
        usage_types=current_usage,
        is_active=True
    ).distinct()
    
    # Récupère le premier BeforeAfter associé à l'un des produits de cet UsageType
    before_after = BeforeAfter.objects.filter(product__usage_types=current_usage).first()
    
    return render(request, 'store/catalog.html', {
        'current_usage': current_usage,
        'products': products,
        'before_after': before_after,
    })


from django.shortcuts import render, get_object_or_404
from .models import Product, BeforeAfter  # Assure-toi d'importer BeforeAfter

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    # On récupère le BeforeAfter lié à ce produit (s'il existe)
    # Si le modèle a une relation OneToOne, tu peux aussi faire : getattr(product, 'before_after', None)
    before_after = BeforeAfter.objects.filter(product=product).first()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'before_after': before_after,
    })

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Product

def _get_cart_data(session):
    """Fonction utilitaire pour calculer le contenu et le total du panier."""
    cart = session.get('cart', {})
    items = []
    subtotal = 0.0
    total_count = 0

    # 1. Filtrer uniquement les clés numériques
    numeric_product_ids = [
        key for key in cart.keys() 
        if str(key).isdigit()
    ]

    # 2. Requête en base de données
    products = Product.objects.filter(id__in=numeric_product_ids)
    
    for product in products:
        qty = cart.get(str(product.id)) or cart.get(product.id, 0)
        if qty <= 0:
            continue

        price = float(product.price)
        item_total = price * qty
        subtotal += item_total
        total_count += qty
        
        # 3. Récupération ultra-sécurisée de l'image
        image_url = '/static/images/default-product.png'
        try:
            if bool(product.main_image) and hasattr(product.main_image, 'url'):
                image_url = product.main_image.url
        except ValueError:
            # Gère le cas où l'ImageField est vide sans fichier associé
            pass

        items.append({
            'id': product.id,
            'name': product.name,
            'price': price,
            'quantity': qty,
            'item_total': item_total,
            'image_url': image_url
        })

    return {
        'items': items,
        'subtotal': round(subtotal, 2),
        'total_count': total_count
    }


def add_to_cart(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                quantity = 1
        except (ValueError, TypeError):
            quantity = 1

        cart = request.session.get('cart', {})
        str_id = str(product_id)
        cart[str_id] = cart.get(str_id, 0) + quantity
        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({'status': 'success', 'cart': _get_cart_data(request.session)})

    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=400)


def get_cart_json(request):
    """Renvoie le panier actuel au format JSON."""
    return JsonResponse({'cart': _get_cart_data(request.session)})


def update_cart_qty(request, product_id):
    """Met à jour la quantité d'un produit (+/-)."""
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = request.session.get('cart', {})
        str_id = str(product_id)

        if str_id in cart:
            if action == 'increase':
                cart[str_id] += 1
            elif action == 'decrease':
                cart[str_id] -= 1
                if cart[str_id] <= 0:
                    del cart[str_id]

            request.session['cart'] = cart
            request.session.modified = True

        return JsonResponse({'status': 'success', 'cart': _get_cart_data(request.session)})

    return JsonResponse({'status': 'error', 'message': 'Action invalide'}, status=400)


def remove_from_cart(request, product_id):
    """Supprime complètement un produit du panier."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        str_id = str(product_id)

        if str_id in cart:
            del cart[str_id]
            request.session['cart'] = cart
            request.session.modified = True

        return JsonResponse({'status': 'success', 'cart': _get_cart_data(request.session)})

    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=400)
from django.shortcuts import render, redirect
from .models import Product
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import Product, Order, OrderItem, Coupon
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import Product, Order, OrderItem
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import Product, Order, OrderItem, Wilaya
import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import Product, Order, OrderItem, Wilaya

def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Votre panier est vide.")
        return redirect('home')

    items = []
    subtotal = Decimal('0.00')

    for product_id_str, quantity in cart.items():
        try:
            product_id = int(product_id_str)
            product = Product.objects.get(id=product_id, is_active=True)
            unit_price = product.get_final_price
            qty = int(quantity)
            total_item_price = unit_price * qty
            subtotal += total_item_price
            
            items.append({
                'product': product,
                'quantity': qty,
                'unit_price': unit_price,
                'total_price': total_item_price,
            })
        except (Product.DoesNotExist, ValueError):
            continue

    if not items:
        messages.error(request, "Impossible de charger votre panier.")
        return redirect('home')

    wilayas = Wilaya.objects.filter(is_active=True)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip() or "Client Anonyme"
        
        phone = request.POST.get('phone', '').strip() or request.POST.get('contact_info', '').strip() or "Non spécifié"
        commune = request.POST.get('commune', '').strip() or "Non spécifiée"
        address_text = request.POST.get('address', '').strip() or "Non spécifiée"
        
        wilaya_id = request.POST.get('wilaya_id')
        delivery_type = request.POST.get('shipping_method', 'stop_desk')

        shipping_cost = Decimal('0.00')
        wilaya_obj = None

        if wilaya_id:
            try:
                wilaya_obj = Wilaya.objects.get(id=wilaya_id, is_active=True)
                if delivery_type == 'home':
                    shipping_cost = Decimal(str(wilaya_obj.home_price))
                else:
                    shipping_cost = Decimal(str(wilaya_obj.desk_price))
            except Wilaya.DoesNotExist:
                messages.error(request, "Wilaya sélectionnée invalide.")

        total_amount = subtotal + shipping_cost

        try:
            with transaction.atomic():
                # Nom de la wilaya ou instance selon le type du champ de votre modèle
                wilaya_value = wilaya_obj.name if wilaya_obj else "Non spécifiée"

                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    full_name=full_name,
                    phone=phone,
                    wilaya=wilaya_value,
                    commune=commune,
                    address=address_text,
                    total_amount=total_amount,
                    shipping_cost=shipping_cost,
                    discount_amount=Decimal('0.00'),
                    status='pending',
                    payment_method='cod'
                )

                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        price=item['unit_price'],
                        quantity=item['quantity']
                    )

                # Vider le panier en session
                request.session['cart'] = {}
                request.session.modified = True

                # IMPORTANT : Redirection directe vers la page de succès
                return redirect('order_success', order_id=order.id)

        except Exception as e:
            # Pour repérer précisément l'erreur qui forçait le retour à l'accueil
            print(f"[ERROR CHECKOUT DETAIL]: {e}")
            messages.error(request, f"Erreur lors de l'enregistrement de la commande : {e}")

    context = {
        'items': items,
        'subtotal': subtotal,
        'wilayas': wilayas,
    }
    return render(request, 'store/checkout.html', context)
from django.shortcuts import get_object_or_404, redirect

def buy_now_view(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))

        # Récupération ou initialisation du panier en session
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)

        # On ajoute ou met à jour la quantité du produit
        cart[product_id_str] = cart.get(product_id_str, 0) + quantity

        request.session['cart'] = cart
        request.session.modified = True

        # Redirection directe vers le Checkout
        return redirect('checkout')

    return redirect('product_detail', product_id=product_id);
def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Calcul du sous-total exact à partir des articles de la commande
    subtotal = sum(item.price * item.quantity for item in order.items.all())

    context = {
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'store/order_success.html', context)
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Product  # تأكدي من اسم الموديل لديك

def promo_products_list(request):
    # جلب جميع المنتجات التي تحتوي على تخفيض
    promo_products_qs = Product.objects.filter(
        discount_price__isnull=False
    ).exclude(discount_price=0).order_by('-id')
    
    # تقسيم المنتجات: 12 منتج في كل صفحة
    paginator = Paginator(promo_products_qs, 12)
    page_number = request.GET.get('page')
    promo_products = paginator.get_page(page_number)

    context = {
        'promo_products': promo_products,
        'total_count': promo_products_qs.count(),
    }
    return render(request, 'store/promo_products_list.html', context)
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from .models import Product, UsageType

def search_api(request):
    query = request.GET.get('q', '').strip()

    # 1. Retourner la liste des UsageTypes quand il n'y a pas de recherche
    if not query:
        categories = []
        for usage in UsageType.objects.all():
            categories.append({
                'id': usage.id,
                'name': usage.name,
                'slug': usage.slug,
                # URL vers la page boutique/catalogue filtrée
                'catalog_url': f"/shop/?usage={usage.slug}" 
            })
        return JsonResponse({'categories': categories, 'products': []})

    # 2. Filtrer les produits si une recherche est saisie
    products_qs = Product.objects.filter(
        Q(is_active=True) & (
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(usage_types__name__icontains=query)
        )
    ).distinct()[:8]

    products_data = []
    for product in products_qs:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': f"{product.get_final_price} DZD",
            'image': product.main_image.url if product.main_image else '/static/images/default.jpg',
            # URL vers la page de détail du produit
            'url': reverse('product_detail', kwargs={'slug': product.slug}),  
        })

    return JsonResponse({'products': products_data})



from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from .models import Review  # Assure-toi d'importer le modèle Review

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if not contact_message.subject:
                contact_message.subject = "Message depuis le formulaire de contact"
            contact_message.save()
            
            messages.success(request, "Votre message a bien été envoyé avec succès !")
            return redirect('contact') 
    else:
        form = ContactForm()

    # Récupération des images d'avis pour la section "Follow us"
    review_images = (
        Review.objects.filter(is_approved=True, image__isnull=False)
        .exclude(image='')
        .select_related('product')[:8]
    )

    context = {
        'form': form,
        'review_images': review_images,  # <-- Ajouté ici pour que la section s'affiche !
    }

    return render(request, 'store/contact.html', context)
def about_view(request):
    return render(request, 'store/about.html')

import json
from django.http import JsonResponse
from .models import Review, Product

def store_review(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = Product.objects.filter(id=product_id).first() if product_id else None
        
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        user_name = f"{first_name} {last_name}".strip()
        
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '')
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        
        # Enregistrement fel Base de Données
        Review.objects.create(
            product=product,
            user_name=user_name,
            rating=rating,
            comment=comment,
            image=image,
            video=video,
            is_approved=False # Kaybqa makhfi hta ywafeq 3lih l'admin
        )
        
        return JsonResponse({'status': 'success', 'message': 'Avis enregistré'})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)