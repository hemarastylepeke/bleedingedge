from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserProfile, UserGoal
from .forms import (
    UserProfileForm, 
    DietaryRequirementsForm, 
    PreferencesForm, 
    CompleteUserProfileForm, 
    UserGoalFormSet, UserGoalForm
)

# Create profile view
@login_required
def create_profile_view(request):
    # Check if user already has a profile
    if hasattr(request.user, 'userprofile'):
        messages.info(request, 'You already have a profile.')
        return redirect('edit_profile')
    
    if request.method == 'POST':
        form = CompleteUserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile created successfully!')
            return redirect('create_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CompleteUserProfileForm()
    
    # Create empty instances for the tabbed interface
    profile_form = CompleteUserProfileForm()
    dietary_form = DietaryRequirementsForm()
    preferences_form = PreferencesForm()
    goal_form = UserGoalForm()
    
    context = {
        'form': form,
        'profile_form': profile_form,
        'dietary_form': dietary_form,
        'preferences_form': preferences_form,
        'goal_form': goal_form,
        'profile': None,  # No profile exists yet
    }
    return render(request, 'account/create_profile.html', context)

# View and update profile
@login_required(login_url='account_login')
def profile_page_view(request):
    """
    Display user profile with goals
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please create your profile first.')
        return redirect('create_profile')
   
    # Get user goals
    user_goals = UserGoal.objects.filter(user_profile=profile).order_by('-created_at')
    
    # Calculate statistics ,progress_percentage is a property, not a database field
    active_goals_count = user_goals.filter(active=True).count()
    
    # Calculate completed goals by checking the property in Python
    completed_goals_count = 0
    total_progress = 0
    goals_with_progress_count = 0
    
    for goal in user_goals:
        if goal.progress_percentage >= 100:
            completed_goals_count += 1
        
        # Calculate average progress for goals that have target values
        if goal.target_value and goal.target_value != 0 and goal.current_value is not None:
            total_progress += goal.progress_percentage
            goals_with_progress_count += 1
    
    # Calculate average progress
    average_progress = total_progress / goals_with_progress_count if goals_with_progress_count > 0 else 0

    context = {
        'profile': profile,
        'user_goals': user_goals,
        'active_goals_count': active_goals_count,
        'completed_goals_count': completed_goals_count,
        'average_progress': round(average_progress, 1),
    }
    
    return render(request, 'account/profile.html', context)

@login_required(login_url='account_login')
def edit_profile_view(request):
    """
    Edit profile view that handles all profile fields and user goals.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Please create your profile first.')
        return redirect('create_profile')

    # Get or create goal record linked to the profile
    user_goal, created = UserGoal.objects.get_or_create(
        user_profile=profile, 
        defaults={
            'goal_type': 'maintain_weight',
            'priority': 1,
            'active': True
        }
    )

    # Initialize forms at the beginning so they're always available
    profile_form = UserProfileForm(instance=profile)
    goal_form = UserGoalForm(instance=user_goal)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Personal information updated successfully!')
                return redirect('edit_profile')
            else:
                messages.error(request, 'Please correct the errors in the personal information form.')

        elif form_type == 'dietary':
            profile.allergies = request.POST.get('allergies', '')
            profile.dietary_restrictions = request.POST.get('dietary_restrictions', '')
            profile.disliked_ingredients = request.POST.get('disliked_ingredients', '')
            profile.save()
            messages.success(request, 'Dietary requirements updated successfully!')
            return redirect('edit_profile')

        elif form_type == 'preferences':
            profile.preferred_cuisines = request.POST.get('preferred_cuisines', '')
            profile.save()
            messages.success(request, 'Preferences updated successfully!')
            return redirect('edit_profile')

        elif form_type == 'goals':
            goal_form = UserGoalForm(request.POST, instance=user_goal)
            if goal_form.is_valid():
                # Ensure goal is always linked to profile before saving
                goal = goal_form.save(commit=False)
                goal.user_profile = profile
                goal.save()
                messages.success(request, 'Goals updated successfully!')
                return redirect('profile_page')
            else:
                messages.error(request, 'Please correct the errors in the goals form.')

    # Context is always available with both forms
    context = {
        'profile': profile,
        'profile_form': profile_form,
        'goal_form': goal_form,
    }

    return render(request, 'account/edit_profile.html', context)

# Delete A profile
@login_required(login_url='account_login')
def delete_profile_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        profile.delete()
        messages.success(request, 'Your profile has been deleted.')
        return redirect('account_logout')

    return render(request, 'account/delete_profile.html', {'profile': profile})