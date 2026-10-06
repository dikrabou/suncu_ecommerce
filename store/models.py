from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Case, When
import uuid

User = get_user_model()


# ==========================================
# 1. CATALOGUE PRODUITS
# ==========================================

class SkinType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Type de peau")
    slug = models.SlugField(unique=True, max_length=120)

    class Meta:
        verbose_name = "Type de peau"
        verbose_name_plural = "Types de peau"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UsageType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Type d'utilisation")
    slug = models.SlugField(unique=True, max_length=120)

    class Meta:
        verbose_name = "Type d'utilisation"
        verbose_name_plural = "Types d'utilisation"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Catégorie")
    slug = models.SlugField(unique=True, max_length=120)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

import uuid
from django.db import models
from django.db.models import Avg
from django.utils.text import slugify


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom du produit")
    slug = models.SlugField(unique=True, max_length=220)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Catégorie")
    skin_types = models.ManyToManyField(SkinType, blank=True, related_name='products', verbose_name="Types de peau")
    usage_types = models.ManyToManyField(UsageType, blank=True, related_name='products', verbose_name="Types d'utilisation")
    
    main_image = models.ImageField(upload_to='products/', verbose_name="Image principale")
    hover_image = models.ImageField(upload_to='products/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (DZD)")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix promo (DZD)")
    stock = models.PositiveIntegerField(default=0, verbose_name="Quantité en stock")
    sales_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de ventes")
    
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_featured = models.BooleanField(default=False, verbose_name="Mettre en avant")
    
    short_description = models.TextField(blank=True, verbose_name="Courte description")
    description = models.TextField(verbose_name="Description détaillée")
    formula = models.TextField(blank=True, verbose_name="Formule / Composition globale")
    ingredients = models.TextField(blank=True, verbose_name="Liste INCI des ingrédients")
    benefits = models.TextField(blank=True, verbose_name="Bénéfices")
    usage_instructions = models.TextField(blank=True, verbose_name="Conseils d'utilisation")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    @property
    def get_final_price(self):
        """Retourne le prix effectif (prix réduit si disponible)."""
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def average_rating(self):
        """Calcule la moyenne des avis clients approuvés pour ce produit."""
        avg = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg) if avg else 5  # Retourne 5 par défaut si aucun avis n'existe

    @property
    def reviews_count(self):
        """Nombre d'avis approuvés."""
        return self.reviews.filter(is_approved=True).count()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            if not base_slug:
                base_slug = f"product-{uuid.uuid4().hex[:8]}"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    @property
    def highlights_list(self):
        """Retourne la liste des lignes saisies dans la description courte."""
        if not self.short_description:
           return []
        return [line.strip() for line in self.short_description.splitlines() if line.strip()]
    @property
    def active_offer(self):
        """Retourne la première offre spéciale active liée à ce produit."""
        return self.special_offers.filter(is_active=True).first()

    @property
    def other_offer_products(self):
        """Retourne les autres produits du pack sans le produit actuel."""
        offer = self.active_offer
        if offer:
            return offer.products.exclude(id=self.id)
        return []
    @property
    def active_ingredients_display(self):
        """
        Retourne les noms des principes actifs séparés par ' + '.
        Exemple: 'Acide Hyaluronique + Vitamine C'
        """
        ingredients = self.active_ingredients_list.values_list('name', flat=True)
        return " + ".join(ingredients) if ingredients else ""
    @property
    def discount_percentage(self):
        if self.price and self.discount_price and self.price > self.discount_price:
            return round(((self.price - self.discount_price) / self.price) * 100)
        return 0
class ProductActiveIngredient(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='active_ingredients_list', verbose_name="Produit")
    name = models.CharField(max_length=200, verbose_name="Nom du principe actif")
    repair_method = models.TextField(verbose_name="Méthode de réparation / Action")
    image = models.ImageField(upload_to='ingredients/', blank=True, null=True, verbose_name="Image de l'ingrédient")

    class Meta:
        verbose_name = "Principe Actif"
        verbose_name_plural = "Principes Actifs"

    def __str__(self):
        return f"{self.name} ({self.product.name})"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='secondary_images')
    image = models.ImageField(upload_to='products/secondary/')
    alt_text = models.CharField(max_length=150, blank=True, help_text="Texte alternatif SEO")

    class Meta:
        verbose_name = "Image secondaire"  
        verbose_name_plural = "Images secondaires"

    def __str__(self):
        return f"Image secondaire de {self.product.name}"


class BeforeAfter(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='before_after')
    title = models.CharField(max_length=200, default="Résultats Avant / Après")
    before_image = models.ImageField(upload_to='before_after/', verbose_name="Photo Avant")
    after_image = models.ImageField(upload_to='before_after/', verbose_name="Photo Après")
    short_description = models.CharField(max_length=255, help_text="Ex: Résultats constatés après 3 semaines d'utilisation quotidienne.")

    class Meta:
        verbose_name = "Avant / Après"
        verbose_name_plural = "Avant / Après"

    def __str__(self):
        return f"Avant/Après - {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Produit", null=True, blank=True)
    user_name = models.CharField(max_length=100, verbose_name="Nom du client")
    rating = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Note /5")
    comment = models.TextField(verbose_name="Avis / Commentaire")
    image = models.ImageField(upload_to='reviews/images/', blank=True, null=True, verbose_name="Photo client")
    video = models.FileField(upload_to='reviews/videos/', blank=True, null=True, verbose_name="Vidéo client")
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé par l'admin")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Avis Client"
        verbose_name_plural = "Avis Clients"

    def __str__(self):
        product_name = self.product.name if self.product else "Général"
        return f"Avis de {self.user_name} sur {product_name} ({self.rating}/5)"


from django.db import models
from django.db.models import Sum

class SpecialOffer(models.Model):
    title = models.CharField(max_length=150, verbose_name="Titre de l'offre")
    subtitle = models.CharField(max_length=255, blank=True, verbose_name="Sous-titre")
    
    # الصورة الرئيسية الخاصة بالعرض (Pack Image)
    image = models.ImageField(upload_to='offers/', blank=True, null=True, verbose_name="Image de l'offre")
    
    # الصورة العريضة (البانر) - اختيارية
    banner_image = models.ImageField(upload_to='offers/banners/', blank=True, null=True, verbose_name="Bannière (optionnelle)")
    
    # Plusieurs produits dans le même pack
    products = models.ManyToManyField('Product', related_name='special_offers', verbose_name="Produits inclus")
    
    # Prix forfaitaire du pack
    special_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix spécial du pack (DZD)")
    
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Offre spéciale"
        verbose_name_plural = "Offres spéciales"

    def __str__(self):
        return f"{self.title} ({self.special_price} DZD)"

    @property
    def total_original_price(self):
        """مجموع أسعار المنتجات قبل التخفيض"""
        total = self.products.aggregate(total=Sum('price'))['total']
        return total if total else 0

    @property
    def savings(self):
        """قيمة التوفير بالـ DZD"""
        if self.total_original_price > self.special_price:
            return self.total_original_price - self.special_price
        return 0
from django.db import models


class ProductVideo(models.Model):
    title = models.CharField(max_length=150)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='videos'
    )
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_url = models.URLField(
        blank=True,
        null=True,
        help_text="Lien TikTok, Instagram Reel ou YouTube",
    )
    thumbnail = models.ImageField(upload_to='videos/thumbnails/', verbose_name="Miniature", blank=True, null=True)
   
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage (Position)",
        help_text="1 pour la première position, 2 pour la deuxième, etc.",
    )

    class Meta:
        verbose_name = "Vidéo produit"
        verbose_name_plural = "Vidéos produits"
        ordering = ['order', 'id']  # Trie automatiquement par ordre

    def __str__(self):
        return f"Vidéo: {self.title} - {self.product.name}"

class ContactMessage(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False, verbose_name="Lu par l'équipe")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"

    def __str__(self):
        return f"Message de {self.full_name} - {self.subject}"


# ==========================================
# 2. CLIENT, ADRESSES & PROMOTIONS
# ==========================================

from decimal import Decimal
from django.db import models

class Wilaya(models.Model):
    code = models.IntegerField(unique=True)  # ex: 19, 16
    name = models.CharField(max_length=100)  # ex: Sétif, Alger
    home_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Prix Domicile")
    desk_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Prix Stop Desk")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        verbose_name = "Wilaya & Tarif"
        verbose_name_plural = "Wilayas & Tarifs"

    def __str__(self):
        return f"{self.code} - {self.name}"

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Pourcentage de réduction (ex: 10.00 pour 10%)"
    )
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Montant minimum en DZD")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Nombre max d'utilisations totales")
    used_count = models.PositiveIntegerField(default=0, help_text="Nombre d'utilisations actuelles")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Code Promo"
        verbose_name_plural = "Codes Promo"

    def is_valid(self, order_total=0):
        now = timezone.now()
        if not self.is_active:
            return False, "Ce coupon n'est plus actif."
        if now < self.valid_from or now > self.valid_until:
            return False, "Ce coupon a expiré ou n'est pas encore valide."
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Ce coupon a atteint sa limite d'utilisation."
        if order_total < self.min_order_amount:
            return False, f"Le montant minimum pour ce coupon est de {self.min_order_amount} DZD."
        return True, "Coupon valide."

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"


# ==========================================
# 3. PANIER & WISHLIST
# ==========================================

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"

    def __str__(self):
        if self.user:
            return f"Panier de {self.user.username}"
        return f"Panier Invité ({self.session_key})"

    @property
    def total_price(self):
        price_expression = Case(
            When(
                product__discount_price__isnull=False,
                product__discount_price__lt=F('product__price'),
                then=F('product__discount_price')
            ),
            default=F('product__price'),
            output_field=DecimalField()
        )
        
        total = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('quantity') * price_expression,
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )['total']
        
        return total or 0


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Article du panier"
        verbose_name_plural = "Articles du panier"
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product'], name='unique_cart_product')
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        return self.product.get_final_price * self.quantity


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Liste de souhaits"
        verbose_name_plural = "Listes de souhaits"

    def __str__(self):
        return f"Wishlist de {self.user.username}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Article de wishlist"
        verbose_name_plural = "Articles de wishlist"
        constraints = [
            models.UniqueConstraint(fields=['wishlist', 'product'], name='unique_wishlist_product')
        ]

    def __str__(self):
        return f"{self.product.name} - {self.wishlist.user.username}"


# ==========================================
# 4. COMMANDES & PAIEMENT
# ==========================================

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('returned', 'Retournée'),
        ('cancelled', 'Annulée'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Paiement à la livraison (COD)'),
        ('baridimob', 'BaridiMob'),
        ('ccp', 'Virement CCP'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Utilisateur")
    full_name = models.CharField(max_length=150, verbose_name="Nom complet")
    phone = models.CharField(max_length=20, verbose_name="Numéro de téléphone")
    wilaya = models.CharField(max_length=100, verbose_name="Wilaya")
    commune = models.CharField(max_length=100, verbose_name="Commune")
    address = models.TextField(verbose_name="Adresse exacte")

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Montant des produits (DZD)")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Frais de livraison (DZD)")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Montant réduction (DZD)")
    
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Code Promo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut de la commande")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod', verbose_name="Mode de paiement")
    is_paid = models.BooleanField(default=False, verbose_name="Payée")
    tracking_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="Code de suivi (ex. Yalidine)")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"

    def update_subtotal(self, save=True):
        subtotal = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('quantity') * F('price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )['total'] or 0
        
        self.total_amount = subtotal
        if save:
            self.save(update_fields=['total_amount', 'updated_at'])
        return self.total_amount

    @property
    def get_final_total(self):
        subtotal = max(0, self.total_amount - self.discount_amount)
        return subtotal + self.shipping_cost

    def __str__(self):
        return f"Commande #{self.id} - {self.full_name} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"

    def get_cost(self):
        return self.price * self.quantity

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_quantity = 0

        if not is_new:
            old_item = OrderItem.objects.get(pk=self.pk)
            old_quantity = old_item.quantity

        super().save(*args, **kwargs)

        # Ajustement atomique du stock et des ventes
        if self.product:
            quantity_diff = self.quantity - old_quantity
            Product.objects.filter(pk=self.product.pk).update(
                stock=Case(
                    When(stock__gte=quantity_diff, then=F('stock') - quantity_diff),
                    default=0
                ),
                sales_count=Case(
                    When(sales_count__gte=-quantity_diff, then=F('sales_count') + quantity_diff),
                    default=0
                )
            )

        self.order.update_subtotal()

    @transaction.atomic
    def delete(self, *args, **kwargs):
        product = self.product
        quantity = self.quantity
        order = self.order

        super().delete(*args, **kwargs)

        # Restituer le stock si l'élément est supprimé
        if product:
            Product.objects.filter(pk=product.pk).update(
                stock=F('stock') + quantity,
                sales_count=Case(
                    When(sales_count__gte=quantity, then=F('sales_count') - quantity),
                    default=0
                )
            )

        order.update_subtotal()

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Produit supprimé'}"


class Payment(models.Model):
    PAYMENT_METHODS = (
        ('cod', 'Paiement à la livraison'),
        ('edahabia', 'Carte Edahabia'),
        ('cib', 'Carte CIB'),
        ('baridimob', 'Virement BaridiMob'),
    )

    PAYMENT_STATUS = (
        ('pending', 'En attente'),
        ('paid', 'Payée'),
        ('failed', 'Échouée'),
        ('refunded', 'Remboursée'),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cod')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Montant payé en DZD")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True, db_index=True, help_text="ID de transaction passerelle (ex: Chargily)")
    raw_response = models.JSONField(blank=True, null=True, help_text="Réponse JSON brute du Webhook")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement {self.get_status_display()} - Commande #{self.order.id} ({self.amount} DZD)"

    def save(self, *args, **kwargs):
        if self.status == 'paid' and not self.paid_at:
            self.paid_at = timezone.now()
            
        super().save(*args, **kwargs)
        
        is_order_paid = (self.status == 'paid')
        if self.order.is_paid != is_order_paid:
            self.order.is_paid = is_order_paid
            self.order.save(update_fields=['is_paid', 'updated_at'])