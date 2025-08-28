from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'event', 'issued_at', 'sent_via_email')
    list_filter = ('sent_via_email', 'event__event_type')
    search_fields = ('student__username', 'event__title')