from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User


class Command(BaseCommand):
    help = '创建默认管理员用户'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                nickname='管理员',
                birth_date=timezone.now().date(),
                grade_level=12,
                user_type='admin'
            )
            self.stdout.write(self.style.SUCCESS('管理员用户创建成功: admin/admin123'))
        else:
            self.stdout.write(self.style.WARNING('管理员用户已存在'))