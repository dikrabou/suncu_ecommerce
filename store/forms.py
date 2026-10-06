from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['full_name', 'email', 'phone', 'message'] # Ajout de 'phone' (le sujet utilise une valeur par défaut ou peut être ajouté)
        widgets = {
            'full_name': forms.TextInput(attrs={'id': 'name', 'placeholder': 'Name'}),
            'email': forms.EmailInput(attrs={'id': 'email', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'id': 'phone', 'placeholder': 'Téléphone'}), # Champ téléphone
            'message': forms.Textarea(attrs={'id': 'message', 'placeholder': 'Message'}),
        }