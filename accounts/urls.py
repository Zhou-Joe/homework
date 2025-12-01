from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('unified-login/', views.unified_login, name='unified_login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('user-info/', views.user_info, name='user-info'),
    # 微信小程序登录
    path('wechat/login/', views.wechat_login, name='wechat_login'),
    path('wechat/bind/', views.wechat_bind, name='wechat_bind'),
    path('wechat/unbind/', views.wechat_unbind, name='wechat_unbind'),
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
]