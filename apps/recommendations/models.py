from django.db import models


class BookRecommendation(models.Model):
    """
    Cached recommendations per user — refreshed nightly by Celery.
    """
    user = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE, related_name='recommendations'
    )
    book = models.ForeignKey(
        'books.Book', on_delete=models.CASCADE, related_name='recommended_to'
    )
    score = models.FloatField(default=0.0)  # hybrid recommendation score 0-1
    reason = models.CharField(max_length=100, blank=True)  # e.g. "Based on your reading history"
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score']
        unique_together = ('user', 'book')

    def __str__(self):
        return f"Recommend {self.book.title} to {self.user.username} (score: {self.score:.2f})"