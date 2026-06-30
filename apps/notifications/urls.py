from django.urls import path
from . import views as nviews

app_name = 'notifications'

urlpatterns = [
    path('', nviews.notification_list, name='list'),
    path('<int:pk>/mark-read/', nviews.mark_read, name='mark_read'),
]