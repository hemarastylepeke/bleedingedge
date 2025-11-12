# core/services/ai_shopping_service.py
import openai
import json
import re
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F

from accounts.models import UserProfile, UserGoal
from core.models import (
    UserPantry, ShoppingList, ShoppingListItem, Budget,
    Recipe, RecipeIngredient, FoodWasteRecord
)


# Food Waste Detection Logic
def detect_and_record_food_waste(user):
    """
    Detect food waste from UserPantry and create FoodWasteRecord entries.
    Criteria:
    - Items expired before being used => reason='expired'
    - Items with excessive remaining qty => reason='over_purchased'
    """
    today = timezone.now().date()
    pantry_items = UserPantry.objects.filter(user=user)

    for item in pantry_items:
        try:
            if item.status != 'active':
                continue

            # Expired and not used
            if item.expiry_date and item.expiry_date < today and item.quantity > 0:
                FoodWasteRecord.objects.create(
                    user=user,
                    pantry_item=item,
                    original_quantity=item.quantity,
                    quantity_wasted=item.quantity,
                    unit=item.unit,
                    cost=(item.price or Decimal("0.00")),
                    reason='expired',
                    reason_details="Item expired before being used",
                    purchase_date=item.purchase_date or today,
                    expiry_date=item.expiry_date or today,
                )
                item.status = 'expired'
                item.save()

            # check items in pantry for too long (> 21 days)
            elif item.purchase_date and (today - item.purchase_date).days > 21 and item.quantity > 0:
                FoodWasteRecord.objects.create(
                    user=user,
                    pantry_item=item,
                    original_quantity=item.quantity,
                    quantity_wasted=item.quantity * 0.5,  # assume half wasted
                    unit=item.unit,
                    cost=(item.price or Decimal("0.00")) * Decimal("0.5"),
                    reason='over_purchased',
                    reason_details="Item remained unused for 3+ weeks",
                    purchase_date=item.purchase_date or today,
                    expiry_date=item.expiry_date or today,
                )
                # reduce pantry stock
                item.quantity *= 0.5
                item.save()

        except Exception as e:
            print(f"Error detecting food waste for {item.name}: {e}")


# AI Shopping List Generation Logic
def generate_ai_shopping_list(user, model="gpt-4o-mini", temperature=0.5):
    try:
        profile = UserProfile.objects.filter(user=user).first()
        budget = Budget.objects.filter(user=user, active=True).order_by('-start_date').first()
        if not budget:
            raise ValueError("No active budget found for user.")

        # Get current pantry with detailed information
        pantry = UserPantry.objects.filter(user=user, quantity__gt=0, status='active')
        expiring_soon = [
            p for p in pantry if p.expiry_date and p.expiry_date <= timezone.now().date() + timedelta(days=3)
        ]

        # Get user's recipes
        recipes = Recipe.objects.filter(created_by=user, is_ai_generated=True).order_by('-created_at')[:3]
        
        # Analyze pantry against recipes to find missing ingredients
        truly_missing_ingredients = []
        pantry_usage_suggestions = []
        
        for recipe in recipes:
            print(f"Recipe: {recipe.name}")
            
            for ri in RecipeIngredient.objects.filter(recipe=recipe).select_related("pantry_item"):
                recipe_ingredient_name = ri.pantry_item.name.lower()
                recipe_quantity_needed = ri.quantity
                recipe_unit = ri.unit
                
                print(f"Needs: {recipe_ingredient_name} - {recipe_quantity_needed} {recipe_unit}")
                
                # Check pantry for this ingredient
                pantry_items = [p for p in pantry if p.name.lower() == recipe_ingredient_name]
                
                if not pantry_items:
                    # Item not in pantry at all
                    truly_missing_ingredients.append({
                        "name": ri.pantry_item.name,
                        "quantity": float(ri.quantity),
                        "unit": ri.unit,
                        "reason": f"Missing for recipe: {recipe.name}",
                        "recipe": recipe.name,
                        "priority": "high"
                    })
                    
                else:
                    # Item exists in pantry - check quantity and quality
                    total_available = sum(p.quantity for p in pantry_items)
                    
                    if total_available >= recipe_quantity_needed:
                        # Sufficient quantity available
                        pantry_usage_suggestions.append({
                            "ingredient": ri.pantry_item.name,
                            "use_quantity": float(recipe_quantity_needed),
                            "available_quantity": float(total_available),
                            "unit": ri.unit,
                            "reason": f"Use from pantry for {recipe.name}",
                            "recipe": recipe.name
                        })
                        
                    else:
                        # Insufficient quantity - calculate how much to buy
                        quantity_to_buy = recipe_quantity_needed - total_available
                        truly_missing_ingredients.append({
                            "name": ri.pantry_item.name,
                            "quantity": float(quantity_to_buy),
                            "unit": ri.unit,
                            "reason": f"Insufficient for {recipe.name} (have {total_available}, need {recipe_quantity_needed})",
                            "recipe": recipe.name,
                            "priority": "high"
                        })
                        print(f"INSUFFICIENT: have {total_available}, need {recipe_quantity_needed} - buy {quantity_to_buy}")
        
        # Get expiring items that should be used
        expiring_items_to_use = []
        for item in expiring_soon:
            expiring_items_to_use.append({
                "name": item.name,
                "quantity": float(item.quantity),
                "unit": item.unit,
                "expiry_date": str(item.expiry_date),
                "reason": "Use soon to avoid waste"
            })

        allergies = [a.strip().lower() for a in (profile.allergies or "").split(",") if a.strip()]
        goal = UserGoal.objects.filter(user_profile__user=user, active=True).first()
        goal_text = goal.goal_type.replace("_", " ") if goal else "healthy eating"

        # Prepare data for AI
        pantry_json = json.dumps([
            {
                "name": p.name, 
                "quantity": float(p.quantity), 
                "unit": p.unit,
                "expiry_date": str(p.expiry_date) if p.expiry_date else None
            } for p in pantry
        ])
        
        expiring_json = json.dumps(expiring_items_to_use)
        missing_json = json.dumps(truly_missing_ingredients)
        allergies_json = json.dumps(allergies)

        # AI prompt
        prompt = (
            f"You are an AI grocery planner optimizing budget and minimizing food waste.\n\n"
            f"USER CONTEXT:\n"
            f"- Budget: {budget.amount} {budget.currency} (DO NOT EXCEED THIS)\n"
            f"- Allergies to AVOID: {allergies_json}\n"
            f"- Health/Fitness Goal: {goal_text}\n\n"
            f"CURRENT PANTRY INVENTORY (DO NOT SUGGEST THESE ITEMS):\n"
            f"{pantry_json}\n\n"
            f"ITEMS EXPIRING SOON (prioritize using these):\n"
            f"{expiring_json}\n\n"
            f"TRULY MISSING INGREDIENTS (MUST INCLUDE THESE FIRST):\n"
            f"{missing_json}\n\n"
            f"CRITICAL SHOPPING RULES:\n"
            f"1. MUST include ALL items from 'Truly Missing Ingredients' list\n"
            f"2. NEVER suggest items already in 'Current Pantry Inventory'\n" 
            f"3. Suggest complementary ingredients that help use 'Items Expiring Soon'\n"
            f"4. Only add additional staples if budget allows AFTER covering missing ingredients\n"
            f"5. Stay strictly below budget limit of {budget.amount} {budget.currency}\n"
            f"6. Avoid all allergens: {allergies_json}\n"
            f"7. Align with user's goal: {goal_text}\n\n"
            f"RESPONSE FORMAT (JSON only):\n"
            f'{{"list_name": "Shopping List Name", "total_estimated_cost": 50.00, "items": [{{"item_name": "Item Name", "quantity": 2, "unit": "kg", "estimated_price": 5.00, "priority": "high", "reason": "Missing for recipe X"}}]}}'
        )

        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )

        ai_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        ai_json = {}
        try:
            ai_json = json.loads(ai_text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if match:
                ai_json = json.loads(match.group())
            else:
                raise ValueError("No valid JSON found in AI response")

        with transaction.atomic():
            # Create the shopping list
            sl = ShoppingList.objects.create(
                user=user,
                name=ai_json.get("list_name", "AI Smart Shopping List"),
                status="generated",
                budget_limit=Decimal(str(budget.amount)),
                total_estimated_cost=Decimal(str(ai_json.get("total_estimated_cost", 0))),
                total_actual_cost=None,
                pantry_utilization=0.0,
                goal_alignment=0.0,
                waste_reduction_score=0.0,
                week_number=timezone.now().isocalendar()[1],
                month=timezone.now().month,
                year=timezone.now().year,
            )

            # Create shopping list items with validation
            items_created = 0
            for item in ai_json.get("items", []):
                name = item.get("item_name")
                if not name:
                    continue
                
                # Double-check this isn't in pantry
                pantry_item_exists = any(
                    p.name.lower() == name.lower() 
                    for p in pantry
                )
                
                if pantry_item_exists:
                    continue
                    
                # Create shopping list item
                ShoppingListItem.objects.create(
                    shopping_list=sl,
                    item_name=name,
                    category='other',  # Default category, can be improved
                    quantity=item.get("quantity", 0),
                    unit=item.get("unit", "g"),
                    estimated_price=Decimal(str(item.get("estimated_price", 0))),
                    priority=item.get("priority", "medium"),
                    notes=item.get("reason", ""),
                    purchased=False,
                )
                items_created += 1
                print(f"Added: {name}")

        return sl

    except Exception as e:
        print(f"Error generating AI shopping list: {e}")
        return None

# Confirm Shopping List (includes waste detection)
def confirm_shopping_list(user, shopping_list_id, purchased_items_payload, total_actual_cost=None):
    try:
        sl = ShoppingList.objects.select_for_update().get(id=shopping_list_id, user=user)
        if sl.status not in ("generated", "draft"):
            raise ValueError("Shopping list is not in a confirmable state.")

        with transaction.atomic():
            total_spent = Decimal("0.00")
            
            # Process only the purchased items from the payload
            for p in purchased_items_payload:
                sli = None
                if p.get("shopping_list_item_id"):
                    sli = ShoppingListItem.objects.filter(
                        id=p["shopping_list_item_id"], 
                        shopping_list=sl
                    ).first()

                if sli:
                    # Mark as purchased and update with actual data
                    sli.purchased = True
                    if p.get("actual_price") is not None:
                        sli.actual_price = Decimal(str(p["actual_price"]))
                    if p.get("purchased_quantity") is not None:
                        sli.quantity = p["purchased_quantity"]
                    sli.save()

                    # Use actual price if provided, otherwise use estimated
                    actual_price = sli.actual_price if sli.actual_price is not None else sli.estimated_price
                    total_spent += actual_price or Decimal("0.00")
                    purchase_qty = sli.quantity or 0

                    # Parse expiry date
                    expiry_date = None
                    if p.get("expiry_date"):
                        try:
                            expiry_date = timezone.datetime.strptime(p["expiry_date"], "%Y-%m-%d").date()
                        except Exception:
                            expiry_date = None

                    # Add to pantry only if purchased
                    UserPantry.objects.create(
                        user=user,
                        name=sli.item_name,
                        category=sli.category,
                        quantity=purchase_qty,
                        unit=sli.unit,
                        purchase_date=timezone.now().date(),
                        expiry_date=expiry_date if expiry_date else None,
                        price=actual_price or None,
                        status='active',
                        detection_source='manual'
                    )

            # Update shopping list status and actual cost
            sl.status = "confirmed"
            sl.total_actual_cost = Decimal(str(total_actual_cost)) if total_actual_cost else total_spent
            sl.completed_at = timezone.now()
            sl.save()

            # Update budget with the actual spent amount
            today = timezone.now().date()
            active_budget = Budget.objects.filter(
                user=user,
                active=True,
                start_date__lte=today,
                end_date__gte=today
            ).first()
            
            if active_budget:
                # Add the spent amount to the budget
                active_budget.amount_spent += total_spent
                active_budget.save()
                print(f"Updated budget: {active_budget.amount_spent} spent of {active_budget.amount}")

        return sl

    except Exception as e:
        print(f"Error confirming shopping list: {e}")
        import traceback
        traceback.print_exc()
        return None