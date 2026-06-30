
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import BookRecommendation


@login_required
def recommendation_list(request):
    recs = request.user.recommendations.select_related('book', 'book__category').all()[:12]
    return render(request, 'recommendations/list.html', {'recommendations': recs})