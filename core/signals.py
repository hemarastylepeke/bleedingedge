# core/signals.py - UPDATED VERSION
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, Count
from .models import UserPantry, FoodWasteRecord


def detect_and_process_all_expired_items(user):
    """
    Detects ALL expired items by comparing today's date with expiry_date
    Uses the existing mark_as_expired() method from UserPantry model
    """
    today = timezone.now().date()
    newly_expired_count = 0
    
    # Find all active items that have expired
    expired_items = UserPantry.objects.filter(
        user=user,
        status='active',
        expiry_date__lt=today,  # expiry date is BEFORE today = EXPIRED
        quantity__gt=0
    )
    
    # Process each expired item using the existing model method
    for item in expired_items:
        try:
            
            if item.mark_as_expired():
                newly_expired_count += 1
                
        except Exception as e:
            # Log error but continue with other items
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing expired item {item.id} ({item.name}): {e}")
            continue
    
    return newly_expired_count

def get_expiring_soon_items(user, days=3):
    """
    Get items that will expire within the next X days
    """
    today = timezone.now().date()
    
    return UserPantry.objects.filter(
        user=user,
        status='active',
        expiry_date__gte=today,  # Not expired yet
        expiry_date__lte=today + timezone.timedelta(days=days),
        quantity__gt=0
    ).order_by('expiry_date')