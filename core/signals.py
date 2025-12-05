# core/signals.py
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, Count
from .models import UserPantry, FoodWasteRecord


def detect_and_process_all_expired_items(user):
    """
    Detects ALL expired items by comparing today's date with expiry_date
    Creates waste records with actual quantities
    """
    today = timezone.now().date()
    newly_expired_count = 0
    
    # Find all active items that have expired
    expired_items = UserPantry.objects.filter(
        user=user,
        status='active',
        expiry_date__lt=today,
        quantity__gt=0
    )
    
    # Process each expired item
    for item in expired_items:
        try:
            with transaction.atomic():
                # Get the current quantity
                current_quantity = item.quantity
                
                # Check if waste record already exists for TODAY
                existing_waste_record = FoodWasteRecord.objects.filter(
                    pantry_item=item,
                    reason='expired',
                    waste_date=today
                ).exists()
                
                # Only create waste record if it doesn't exist
                if not existing_waste_record:
                    # Create the waste record with actual quantity
                    FoodWasteRecord.objects.create(
                        user=user,
                        pantry_item=item,
                        original_quantity=current_quantity,
                        quantity_wasted=current_quantity,  # All of it expired
                        unit=item.unit,
                        cost=item.price or Decimal('0.00'),
                        reason='expired',
                        reason_details=f"Item expired on {item.expiry_date}",
                        purchase_date=item.purchase_date,
                        expiry_date=item.expiry_date,
                        waste_date=today
                    )
                
                # Mark the pantry item as expired (doesn't change quantity)
                item.mark_as_expired()
                
                newly_expired_count += 1
                
        except Exception as e:
            print(f"Error processing expired item {item.id} ({item.name}): {e}")
            continue
    
    return newly_expired_count
