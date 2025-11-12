from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page_view, name='home'),
    # Pantry management
    path('pantry/', views.pantry_dashboard_view, name='pantry_dashboard'),

    # Pantry item operations
    path('pantry/list/', views.pantry_list_view, name='pantry_list'),
    path('pantry/add/', views.add_pantry_item_view, name='add_pantry_item'),
    path('pantry/edit/<int:item_id>/', views.edit_pantry_item_view, name='edit_pantry_item'),
    path('pantry/delete/<int:item_id>/', views.delete_pantry_item_view, name='delete_pantry_item'),

    # Budget management URLs
    path('budgets/', views.budget_list_view, name='budget_list'),
    path('budgets/add/', views.create_budget_view, name='create_budget'),
    path('budgets/<int:budget_id>/', views.budget_detail_view, name='budget_detail'),
    path('budgets/<int:budget_id>/edit/', views.edit_budget_view, name='edit_budget'),
    path('budgets/<int:budget_id>/delete/', views.delete_budget_view, name='delete_budget'),
    path('budgets/<int:budget_id>/toggle-active/', views.toggle_budget_active_view, name='toggle_budget_active'),
    path('budgets/analytics/', views.budget_analytics_view, name='budget_analytics'),

    # Shopping list URLs
    path('shopping_lists/', views.shopping_list_list_view, name='shopping_list_list'),
    path('shopping_lists/<int:list_id>/', views.shopping_list_detail_view, name='shopping_list_detail'),
    path('shopping_lists/add/', views.create_shopping_list_view, name='create_shopping_list'),
   # path('shopping_lists/<int:list_id>/edit/', views.edit_shopping_list_view, name='edit_shopping_list'),
    path('shopping_lists/<int:list_id>/delete/', views.delete_shopping_list_view, name='delete_shopping_list'),

    # Recipe URLs
    path('recipes/', views.recipe_list_view, name='recipe_list'),
    path('recipes/my/', views.my_recipes_view, name='my_recipes'),
    path('recipes/add/', views.create_recipe_view, name='create_recipe'),
    path('recipes/<int:recipe_id>/', views.recipe_detail_view, name='recipe_detail'),
    path('recipes/<int:recipe_id>/edit/', views.edit_recipe_view, name='edit_recipe'),
    path('recipes/<int:recipe_id>/delete/', views.delete_recipe_view, name='delete_recipe'),

    path('analytics/food_waste/', views.food_waste_analytics_view, name='food_waste_analytics'),
    
]