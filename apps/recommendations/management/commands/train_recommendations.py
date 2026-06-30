"""
Usage: python manage.py train_recommendations
Trains the ML model and refreshes all user recommendations.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train the AI recommendation model from borrowing history'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='Refresh for a specific user only')

    def handle(self, *args, **options):
        from apps.recommendations.engine import train_all, refresh_recommendations_for_user
        from apps.users.models import CustomUser

        self.stdout.write("Training recommendation model...")
        train_all()
        self.stdout.write(self.style.SUCCESS("Model trained!"))

        user_id = options.get('user_id')
        if user_id:
            refresh_recommendations_for_user(user_id)
            self.stdout.write(self.style.SUCCESS(f"Refreshed recommendations for user {user_id}."))
        else:
            students = CustomUser.objects.filter(role='STUDENT', is_active=True)
            for student in students:
                refresh_recommendations_for_user(student.id)
            self.stdout.write(self.style.SUCCESS(f"Refreshed for {students.count()} students."))