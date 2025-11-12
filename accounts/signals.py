from django.db.models.signals import post_save
from .models import UserAccount, UserProfile
from django.dispatch import receiver

# Create user profile whenever a new user account is created.
@receiver(post_save, sender=UserAccount)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)