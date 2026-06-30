from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='list'),
    path('books/<int:pk>/', views.book_detail, name='detail'),
    path('books/add/', views.book_add, name='add'),
    path('books/<int:pk>/edit/', views.book_edit, name='edit'),
    path('books/<int:pk>/delete/', views.book_delete, name='delete'),
]