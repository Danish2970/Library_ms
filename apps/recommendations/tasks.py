from celery import shared_task


@shared_task
def retrain_recommendation_model():
    from .engine import train_all, refresh_recommendations_for_user
    from apps.users.models import CustomUser

    train_all()

    students = CustomUser.objects.filter(
        role='STUDENT', is_active=True
    ).values_list('id', flat=True)

    for user_id in students:
        refresh_recommendations_for_user(user_id)

    return f"Retrained and refreshed for {len(students)} students."