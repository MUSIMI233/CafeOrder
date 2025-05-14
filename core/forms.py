from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Business

User = get_user_model()

class BusinessUserCreationForm(UserCreationForm):
    business_name = forms.CharField(max_length=100, required=True, label='Business Name')
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ('username', 'business_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if Business.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email