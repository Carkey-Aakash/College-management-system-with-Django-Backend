from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    event_title=serializers.CharField(source='event.title',read_only=True)

    class Meta:
        model=Notification
        fields=['id', 'recipient', 'title', 'message', 'notification_type', 'event', 'event_title', 'created_at', 'is_read']
        
