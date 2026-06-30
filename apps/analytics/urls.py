from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reports/', views.reports, name='reports'),
    path('charts/borrows-per-day/', views.chart_borrows_per_day, name='chart_borrows_per_day'),
    path('charts/top-books/', views.chart_top_books, name='chart_top_books'),
    path('charts/genres/', views.chart_genre_distribution, name='chart_genres'),
]