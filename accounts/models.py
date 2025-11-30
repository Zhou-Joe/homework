from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """扩展的用户模型"""
    USER_TYPE_CHOICES = [
        ('student', '学生'),
        ('admin', '管理员'),
    ]

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student', verbose_name='用户类型')
    nickname = models.CharField(max_length=50, verbose_name='昵称')
    birth_date = models.DateField(verbose_name='出生年月')
    grade_level = models.CharField(max_length=10, verbose_name='当前年级', choices=[
        ('小学1年级', '小学1年级'), ('小学2年级', '小学2年级'), ('小学3年级', '小学3年级'),
        ('小学4年级', '小学4年级'), ('小学5年级', '小学5年级'), ('小学6年级', '小学6年级'),
        ('初一', '初一'), ('初二', '初二'), ('初三', '初三'),
        ('高一', '高一'), ('高二', '高二'), ('高三', '高三'),
    ])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return f"{self.nickname} ({self.username})"
