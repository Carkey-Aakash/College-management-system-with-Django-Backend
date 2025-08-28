from django.db.models import Q
from django.utils import timezone
from .models import Event, EventConflict

def detect_event_conflicts(event):
    #Detect scheduling conflicts with other events
    # Implementation of Event Conflict Detection Algorithm
    conflicts= []
    # find overlapping events at the same venue
    overlapping_events= Event.objects.filter(
        venue=event.venue,
        status__in=['approved','pending']
    ).exclude(id=event.id)

    for other_event in overlapping_events:
        # check time overlap using interval overlap detection

        if(event.start_date < other_event.end_date and
           other_event.start_date < event.end_date):
            conflicts.append(other_event)

    return conflicts

# def send_event_notification(event, notification_type, recipients):
#     from notifications.utils import create_notification

#     # Create notification based on type
#     if notification_type == 'approval_status':
#         message = f"Your event '{event.title}' has been {event.status}"
#     elif notification_type == 'registration_confirmation':
#         message = f"You have successfully registered for '{event.title}'"
#     elif notification_type == 'event_reminder':
#         message = f"Reminder: '{event.title}' is starting soon"
#     elif notification_type == 'event_cancelled':
#         message = f"Event '{event.title}' has been cancelled"
#     else:
#         message = f"Update for event '{event.title}'"
    
#     for recipient in recipients:
#         create_notification(
#             recipient=recipient,
#             title=f"Event Update: {event.title}",
#             message=message,
#             event=event
#         )

def get_upcoming_events(user, days=7):
    
    # Get upcoming events for a user based on their role
   
    from datetime import timedelta
    
    end_date = timezone.now() + timedelta(days=days)
    
    if user.is_student():
        # Get events the student is registered for
        from .models import EventRegistration
        registrations = EventRegistration.objects.filter(
            student=user,
            status='confirmed',
            event__start_date__gte=timezone.now(),
            event__start_date__lte=end_date
        ).select_related('event')
        return [reg.event for reg in registrations]
    
    elif user.is_department():
        # Get events organized by faculty
        return Event.objects.filter(
            organizer=user,
            start_date__gte=timezone.now(),
            start_date__lte=end_date
        )
    elif user.is_organization():
        # Get events organized by faculty
        return Event.objects.filter(
            organizer=user,
            start_date__gte=timezone.now(),
            start_date__lte=end_date
        )
    
    elif user.is_chief() or user.is_admin_user():
        # Get all upcoming events
        return Event.objects.filter(
            status='approved',
            start_date__gte=timezone.now(),
            start_date__lte=end_date
        )
    
    return []


