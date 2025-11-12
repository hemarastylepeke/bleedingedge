from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate
from allauth.account.forms import LoginForm
from allauth.exceptions import ImmediateHttpResponse
from .models import UserProfile, UserGoal
from django.forms import inlineformset_factory

class CustomLoginForm(LoginForm):
    def login(self, request, redirect_url=None):
        try:
            self.request = request
            login_field = self.cleaned_data.get("login")
            password = self.cleaned_data.get("password")

            if login_field and password:
                user = authenticate(request, username=login_field, password=password)
                if user is None:
                    messages.error(request, "Invalid login credentials. Please try again.")
                elif not user.is_active:
                    messages.error(request, "Your account is inactive. Please contact support.")

            ret = super().login(request, redirect_url)
            messages.success(request, f"Welcome back, {self.user.email}!")
            return ret

        except ImmediateHttpResponse:
            if hasattr(self, 'user') and self.user and not self.user.is_active:
                messages.error(request, "Your account is not active.")
            elif not getattr(self, 'user', None):
                messages.error(request, "Invalid login credentials.")
            else:
                messages.error(request, "Login failed. Please try again.")
            raise

        except Exception:
            messages.error(request, "An unexpected error occurred during login. Please try again.")
            raise

    def clean(self):
        try:
            cleaned_data = super().clean()
            return cleaned_data
        except forms.ValidationError:
            if hasattr(self, 'request'):
                messages.error(self.request, "Authentication failed, please try again!")
            raise

class CompleteUserProfileForm(forms.ModelForm):
    """Complete form with all UserProfile fields for profile creation"""
    class Meta:
        model = UserProfile
        fields = [
            'profile_image',
            'first_name',
            'last_name',
            'height',
            'weight',
            'age',
            'gender',
            'activity_level',
            'allergies',
            'dietary_restrictions',
            'disliked_ingredients',
            'preferred_cuisines',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'height': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'Height (cm)'}),
            'weight': forms.NumberInput(attrs={'step': '0.1', 'placeholder': 'Weight (kg)'}),
            'age': forms.NumberInput(attrs={'min': '1', 'placeholder': 'Age'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
            'allergies': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'List any allergies (e.g., peanuts, dairy, shellfish)...'
            }),
            'dietary_restrictions': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Any dietary restrictions (e.g., vegan, vegetarian, halal, kosher, gluten-free)...'
            }),
            'disliked_ingredients': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Ingredients you prefer to avoid (e.g., cilantro, mushrooms, spicy foods)...'
            }),
            'preferred_cuisines': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'List your favorite cuisines (e.g., Italian, Kenyan, Thai, Mexican, Indian)...'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'height': 'Height (cm)',
            'weight': 'Weight (kg)',
            'age': 'Age',
            'gender': 'Gender',
            'activity_level': 'Activity Level',
            'allergies': 'Allergies',
            'dietary_restrictions': 'Dietary Restrictions',
            'disliked_ingredients': 'Disliked Ingredients',
            'preferred_cuisines': 'Preferred Cuisines',
        }
        help_texts = {
            'height': 'Your height in centimeters',
            'weight': 'Your weight in kilograms',
            'activity_level': 'How active you are on a daily basis',
            'allergies': 'Any food allergies you have',
            'dietary_restrictions': 'Any dietary restrictions or preferences',
            'disliked_ingredients': 'Ingredients you don\'t like or want to avoid',
            'preferred_cuisines': 'Your favorite types of cuisine',
        }

# Forms for editing specific sections of the UserProfile
class UserProfileForm(forms.ModelForm):
    """Handles general profile information such as name, image, and physical data."""
    class Meta:
        model = UserProfile
        fields = [
            'profile_image',
            'first_name',
            'last_name',
            'height',
            'weight',
            'age',
            'gender',
            'activity_level',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Height (cm)'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Weight (kg)'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Age'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
        }

class DietaryRequirementsForm(forms.ModelForm):
    """Handles dietary-related information."""
    class Meta:
        model = UserProfile
        fields = [
            'allergies',
            'dietary_restrictions',
            'disliked_ingredients',
        ]
        widgets = {
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List any allergies (e.g., peanuts, dairy)...'
            }),
            'dietary_restrictions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any dietary restrictions (e.g., vegan, halal)...'
            }),
            'disliked_ingredients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ingredients you prefer to avoid...'
            }),
        }

class PreferencesForm(forms.ModelForm):
    """Handles user taste preferences and cuisines."""
    class Meta:
        model = UserProfile
        fields = ['preferred_cuisines']
        widgets = {
            'preferred_cuisines': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List your favorite cuisines (e.g., Italian, Kenyan, Thai)...'
            }),
        }

class UserGoalForm(forms.ModelForm):
    class Meta:
        model = UserGoal
        fields = ['goal_type', 'current_value', 'target_value', 'target_date', 'priority', 'active']
        widgets = {
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Target value'}),
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'priority': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'goal_type': 'Goal Type',
            'target_value': 'Target Value',
            'target_date': 'Target Date',
            'priority': 'Priority',
            'active': 'Is Active?',
        }

# Inline formset to allow multiple goals linked to a single UserProfile
UserGoalFormSet = inlineformset_factory(
    UserProfile,  # parent model
    UserGoal,     # child model
    form=UserGoalForm,
    extra=1,      # at least one empty form
    can_delete=True
)