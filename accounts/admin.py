from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'nickname', 'email', 'user_type', 'grade_level', 'is_staff', 'is_active')
    list_filter = ('user_type', 'grade_level', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'nickname', 'email')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('nickname', 'email', 'birth_date', 'grade_level', 'user_type')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'nickname', 'birth_date', 'grade_level', 'user_type'),
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')
