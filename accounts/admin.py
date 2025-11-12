from .models import UserAccount, UserProfile, UserGoal
from django.contrib import admin

# Register account models
admin.site.register(UserAccount)
admin.site.register(UserProfile)
admin.site.register(UserGoal)
