from django.db import models
from django.contrib.auth import get_user_model
User=get_user_model()
# Create your models here.

class Notification(models.Model):
    NOTIFICATION_TYPES=[
        ('event_created','Event Created'),
        ('event_approved','Event Approved'),
        ('event_rejected', 'Event Rejected'),
        ('event_cancelled', 'Event Cancelled'),
        ('registration_confirmation', 'Registration Confirmation'),
        ('event_update', 'Event Update'),
        ('event_completed', 'Event Completed'),
        ('reminder', 'Reminder'),
        ('general', 'General'),
    ]
    
    recipient=models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    event=models.ForeignKey('events.Event', on_delete=models.CASCADE,null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} for {self.recipient.username}"
    
from django.conf import settings
from events.models import Event

class ReminderSent(models.Model):
    REMINDER_TYPE_CHOICES = [
        ('registration_closing', 'Registration Closing'),
        ('event_start', 'Event Start'),
    ]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=50, choices=REMINDER_TYPE_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'event', 'reminder_type')