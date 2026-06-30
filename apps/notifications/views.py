from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()[:50]
    # Mark all as read when viewed
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_read(request, pk):
    """AJAX endpoint to mark a single notification as read."""
    if request.method == 'POST':
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)