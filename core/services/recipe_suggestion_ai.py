# core/services/recipe_suggestion_ai.py
import openai
import re
import json
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserProfile, UserGoal
from core.models import Recipe, UserPantry, RecipeIngredient, Budget

openai.api_key = settings.OPENAI_API_KEY


def build_ai_recipe_context(user):
    """Build structured user + pantry context for OpenAI recipe generation."""
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = None
        
    pantry_items = UserPantry.objects.filter(
        user=user, 
        status='active',
        expiry_date__gte=timezone.now().date(), 
        quantity__gt=0
    ).order_by('expiry_date')

    expiring_soon = [
        item for item in pantry_items
        if item.expiry_date <= timezone.now().date() + timedelta(days=3)
    ]

    context = {
        "user": {
            "email": user.email,
            "first_name": profile.first_name if profile else "",
            "height": profile.height if profile else "Unknown",
            "weight": profile.weight if profile else "Unknown",
            "goal": getattr(profile, "goal", "Healthy eating") if profile else "Healthy eating",
            "allergies": [a.strip().lower() for a in profile.allergies.split(",")] if profile and profile.allergies else [],
            "preferred_cuisines": [c.strip().lower() for c in profile.preferred_cuisines.split(",")] if profile and profile.preferred_cuisines else [],
        },
        "pantry": [
            {
                "name": item.name,
                "category": item.category,
                "quantity": float(item.quantity),
                "unit": item.unit,
                "expiry_date": str(item.expiry_date),
                "is_expiring_soon": item in expiring_soon,
                "calories": item.calories,
                "protein": item.protein,
                "carbs": item.carbs,
                "fat": item.fat,
            }
            for item in pantry_items
        ],
    }
    return context


def generate_ai_recipe_from_openai(user):
    """
    Generate an AI-powered recipe suggestion based on:
    - Pantry ingredients (use what's available)
    - Dietary requirements (avoid allergies)
    - Goal (lose weight, build muscle, etc.)
    - Budget
    - Preferred cuisine
    - Difficulty, time, and portion size
    """
    try:
        # Get user profile and preferences
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = None
            
        budget = Budget.objects.filter(user=user, active=True).order_by('-start_date').first()
        
        # Get user goal from UserGoal model
        goal = UserGoal.objects.filter(user_profile__user=user, active=True).order_by('priority').first()

        # Get recent recipes to avoid repetition
        recent_recipes = Recipe.objects.filter(
            created_by=user,
            created_at__gte=timezone.now() - timedelta(days=21)
        ).values_list('name', flat=True)

        # Get available pantry items
        pantry_items = UserPantry.objects.filter(
            user=user, 
            status='active',
            expiry_date__gte=timezone.now().date(), 
            quantity__gt=0
        ).order_by('expiry_date')

        expiring_soon = [
            p for p in pantry_items 
            if p.expiry_date <= timezone.now().date() + timedelta(days=3)
        ]

        pantry_data = [
            {
                "name": p.name,
                "category": p.category,
                "quantity": float(p.quantity),
                "unit": p.unit,
                "expiry_date": str(p.expiry_date),
                "is_expiring_soon": p in expiring_soon,
                "calories": p.calories,
                "protein": p.protein,
                "carbs": p.carbs,
                "fat": p.fat,
            }
            for p in pantry_items
        ]

        # Prepare user constraints
        allergies = [a.strip().lower() for a in (profile.allergies.split(",") if profile and profile.allergies else []) if a.strip()]
        cuisines = [c.strip().lower() for c in (profile.preferred_cuisines.split(",") if profile and profile.preferred_cuisines else []) if c.strip()]
        goal_text = goal.goal_type.replace("_", " ") if goal else "general healthy eating"
        budget_text = f"{budget.amount} {budget.currency}" if budget else "reasonable budget"

        # Comprehensive AI Prompt
        prompt = f"""
        You are an expert AI chef and nutritionist creating a personalized, balanced meal.
        
        User Context:
        - Goal: {goal_text}
        - Budget: {budget_text}
        - Allergies (strictly avoid): {allergies}
        - Preferred cuisines: {cuisines or ["any"]}
        - Available pantry ingredients: {json.dumps(pantry_data, indent=2)}
        - Recently cooked recipes: {list(recent_recipes)}

        Your job:
        1. Use pantry ingredients as much as possible (especially those expiring soon).
        2. Avoid ingredients the user is allergic to.
        3. Suggest a recipe suitable for 1-2 servings.
        4. Stay within the user's budget range when suggesting new ingredients.
        5. Choose a cuisine from the user's preferences (or any suitable one if none).
        6. Include difficulty level (easy, medium, hard) and total cooking time (prep + cook).
        7. The recipe must align with the user's goal — e.g., high protein for muscle gain, low carb for weight loss.
        8. Avoid repeating recipes from the recent list.
        9. Provide accurate nutritional information based on ingredients used.

        Return ONLY valid JSON structured as:
        {{
            "name": "Recipe Name",
            "description": "Brief appetizing summary",
            "cuisine": "kenyan | italian | mexican | asian | indian | mediterranean | american | french | thai | chinese | japanese | other",
            "difficulty": "easy | medium | hard",
            "prep_time": number (in minutes),
            "cook_time": number (in minutes),
            "servings": number,
            "ingredients": [
                {{"name": "IngredientName", "quantity": number, "unit": "g/ml/pieces/tbsp/tsp"}}
            ],
            "instructions": "Step 1. Do this...\\nStep 2. Then do that...\\nStep 3. Finally...",
            "total_calories": number,
            "total_protein": number (in grams),
            "total_carbs": number (in grams),
            "total_fat": number (in grams),
            "dietary_tags": "comma-separated tags like vegetarian, gluten-free, high-protein, low-carb"
        }}

        Important: Only use ingredients that exist in standard kitchens or can be easily purchased.
        """

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional AI chef focused on personalized, healthy meal planning. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.55,
        )

        ai_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in AI response")
            
        recipe_json = json.loads(match.group())

        # Create Recipe in DB
        recipe = Recipe.objects.create(
            name=recipe_json.get("name", f"AI Recipe {timezone.now().strftime('%Y%m%d%H%M')}"),
            description=recipe_json.get("description", "A delicious AI-generated recipe"),
            cuisine=recipe_json.get("cuisine", "other"),
            difficulty=recipe_json.get("difficulty", "medium"),
            prep_time=recipe_json.get("prep_time", 15),
            cook_time=recipe_json.get("cook_time", 25),
            servings=recipe_json.get("servings", 2),
            instructions=recipe_json.get("instructions", ""),
            total_calories=recipe_json.get("total_calories", 0),
            total_protein=recipe_json.get("total_protein", 0),
            total_carbs=recipe_json.get("total_carbs", 0),
            total_fat=recipe_json.get("total_fat", 0),
            dietary_tags=recipe_json.get("dietary_tags", ""),
            created_by=user,
            is_ai_generated=True,
        )

        # Link ingredients to recipe through RecipeIngredient
        # Note: For AI-generated recipes, we're creating ingredient references
        # that may not exist in pantry yet. These will be linked when users
        # actually have these items in their pantry.
        for ing_data in recipe_json.get("ingredients", []):
            name = ing_data.get("name", "").strip()
            quantity = ing_data.get("quantity", 0)
            unit = ing_data.get("unit", "g")
            
            if not name:
                continue
                
            # Try to find matching pantry item, or create a reference
            pantry_item = UserPantry.objects.filter(
                user=user,
                name__iexact=name
            ).first()
            
            if not pantry_item:
                # Create a placeholder pantry item for the recipe
                # This won't be added to user's actual pantry
                pantry_item = UserPantry.objects.create(
                    user=user,
                    name=name,
                    category='other',
                    quantity=0,  # Not actually in pantry
                    unit=unit,
                    purchase_date=timezone.now().date(),
                    expiry_date=timezone.now().date() + timedelta(days=30),
                    status='active',
                    detection_source='manual'
                )
            
            # Create RecipeIngredient link
            RecipeIngredient.objects.create(
                recipe=recipe,
                pantry_item=pantry_item,
                quantity=quantity,
                unit=unit,
                optional=False
            )

        # Calculate nutrition based on linked pantry items
        recipe.calculate_nutrition()
        
        return recipe

    except Exception as e:
        print(f"Error generating AI recipe: {e}")
        return None