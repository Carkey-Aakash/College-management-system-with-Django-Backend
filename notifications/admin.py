from django.contrib import admin
from .models import Notification, ReminderSent

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'notification_type', 'message', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    ordering = ('-created_at',)

@admin.register(ReminderSent)  # Register ReminderSent Model
class ReminderSentAdmin(admin.ModelAdmin):
    list_display = ('student', 'event', 'reminder_type', 'sent_at')
    list_filter = ('reminder_type', 'sent_at')
    search_fields = ('student__username', 'event__title')
    ordering = ('-sent_at',)
# Register your models here.
