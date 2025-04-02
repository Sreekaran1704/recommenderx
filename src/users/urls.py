from django.urls import path
from .views import UserCreateView, UserProfileView

urlpatterns = [
    path('create/', UserCreateView.as_view(), name='user-create'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]