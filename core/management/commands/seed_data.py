from django.core.management.base import BaseCommand
from core.models import User, TokenPlan


class Command(BaseCommand):
    help = 'Seed database with default accounts and token plans'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(email='admin@gmail.com').exists():
            admin = User(name='Admin', email='admin@gmail.com', is_admin=True)
            admin.set_password('121212')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin@gmail.com'))
        else:
            self.stdout.write('admin@gmail.com already exists')

        if not User.objects.filter(email='abdurahmon@gmail.com').exists():
            user = User(name='Abdurahmon', email='abdurahmon@gmail.com', tokens=200)
            user.set_password('abdurahmon123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created abdurahmon@gmail.com with 200 tokens'))
        else:
            self.stdout.write('abdurahmon@gmail.com already exists')

        plans = [
            {'name': 'Starter', 'price_usd': 25, 'tokens': 100},
            {'name': 'Standard', 'price_usd': 45, 'tokens': 200},
            {'name': 'Premium', 'price_usd': 65, 'tokens': 300},
        ]
        for plan_data in plans:
            obj, created = TokenPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults={'price_usd': plan_data['price_usd'], 'tokens': plan_data['tokens']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created plan: {obj.name}'))

        self.stdout.write(self.style.SUCCESS('\nSeed complete!'))
