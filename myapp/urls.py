from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/profile/browse_courses', views.api_data_search, name='api_data_search'),
    path('accounts/profile/shopping_cart', views.shoppingCart, name="shoppingCart"),
    path('accounts/addToCart/<int:pk>/', views.addToCart, name = 'addToCart'),
    path('accounts/removeFromCart/<int:pk>/', views.removeFromCart, name = 'removeFromCart'),
    path('accounts/profile/calendar', views.calendar, name='calendar'),
    path('accounts/addToSchedule/<int:pk>/', views.addToSchedule, name = 'addToSchedule'),
    path('accounts/removeFromSchedule/<int:pk>/', views.removeFromSchedule, name = 'removeFromSchedule'),
    path('accounts/createAdmin', views.createAdmin, name = 'createAdmin'),
    path('accounts/createSchedule/<int:pk>/', views.createSchedule, name = 'createSchedule'),
    path('accounts/approveSchedule/', views.approveSchedule, name = 'approveSchedule'),


]

