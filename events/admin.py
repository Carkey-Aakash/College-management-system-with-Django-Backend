from django.contrib import admin
from .models import Event, EventRegistration, EventFeedback, EventConflict

# Register your models here.
class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    readonly_fields = ['registration_date', 'attendance_marked_at']

class EventFeedbackInline(admin.TabularInline):
    model = EventFeedback
    extra = 0
    readonly_fields = ['created_at']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'event_level', 'status', 'get_organizer', 'start_date','end_date', 'venue']
    list_filter = ['status', 'event_type', 'event_level', 'created_at']
    search_fields = ['title', 'description', 'organizer__username']
    readonly_fields = ['created_at', 'updated_at', 'qr_code']
    inlines = [EventRegistrationInline, EventFeedbackInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'event_type', 'event_level')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date', 'venue', 'registration_deadline')
        }),
        ('Registration', {
            'fields': ('max_participants', 'is_paid_event', 'registration_fee')
        }),
        ('Management', {
            'fields': ('organizer', 'status', 'approved_by', 'status_comments')
        }),
        ('Resources', {
            'fields': ('poster', 'qr_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_organizer(self, obj):
        return obj.organizer.username if obj.organizer else None
    get_organizer.short_description = 'Organizer'

    # Disable add permission for admin panel
    def has_add_permission(self, request):
        return False

    # Disable change/edit permission for admin panel
    def has_change_permission(self, request, obj=None):
        return False

    # Disable delete permission for admin panel
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'event', 'status', 'attended', 'registration_date']
    list_filter = ['status', 'attended', 'payment_status', 'registration_date']
    search_fields = ['student__username', 'event__title']
    readonly_fields = ['registration_date', 'attendance_marked_at']


@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'event', 'rating', 'would_recommend', 'created_at','comments','suggestions']
    list_filter = ['rating', 'would_recommend', 'created_at']
    search_fields = ['student__username', 'event__title']
    readonly_fields = ['created_at']

    def get_student(self, obj):
        return obj.Student.username if obj.Student else None
    get_student.short_description = 'Student'


@admin.register(EventConflict)
class EventConflictAdmin(admin.ModelAdmin):
    list_display = ['event1', 'event2', 'status', 'detected_at']
    list_filter = ['status', 'detected_at']
    readonly_fields = ['detected_at']
