from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models

class UserAccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        user = self.create_user(email, password=password, **kwargs)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class UserAccount(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = UserAccountManager()
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    SUBSCRIPTION_PLANS = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('pro', 'Pro'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        upload_to='profile_images/', 
        blank=True, 
        null=True, 
        default='profile_images/default_profile_image.png'
    )
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    subscription_plan = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_PLANS, 
        default='basic'
    )
    
    # Personal information for nutritional calculations
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")  
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(
        max_length=20, 
        choices=GENDER_CHOICES, 
        null=True, 
        blank=True
    )
    activity_level = models.CharField(
        max_length=20, 
        choices=[
            ('sedentary', 'Sedentary'),
            ('light', 'Lightly Active'),
            ('moderate', 'Moderately Active'),
            ('active', 'Very Active'),
            ('athlete', 'Athlete'),
        ],
        null=True, 
        blank=True
    )
    
    allergies = models.TextField(blank=True, null=True)
    dietary_restrictions = models.TextField(blank=True, null=True)
    disliked_ingredients = models.TextField(blank=True, null=True)
    preferred_cuisines = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"

class UserGoal(models.Model):
    GOAL_TYPES = [
        ('lose_weight', 'Lose Weight'),
        ('gain_weight', 'Gain Weight'),
        ('build_muscle', 'Build Muscle'),
        ('maintain_weight', 'Maintain Weight'),
        ('more_fiber', 'More Fiber'),
        ('more_iron', 'More Iron'),
        ('more_veggies', 'More Vegetables'),
        ('reduce_waste', 'Reduce Food Waste'),
        ('budget_friendly', 'Budget Friendly'),
    ]
    
    user_profile = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='goals'
    )
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_value = models.FloatField(null=True, blank=True)
    current_value = models.FloatField(null=True, blank=True)
    start_date = models.DateField(auto_now_add=True)
    target_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    bmi = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority', '-created_at']

    def __str__(self):
        return f"{self.user_profile.user.email} - {self.get_goal_type_display()}"