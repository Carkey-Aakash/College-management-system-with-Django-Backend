# from celery import shared_task
# from django.utils import timezone
# from django.conf import settings
# from events.models import Event, EventRegistration
# from users.models import User
# from django.db.models import Q
# from notifications.utils import create_notification, send_email_notification
# from notifications.models import ReminderSent  # New import

# # @shared_task
# # def send_registration_closing_reminders():
# #     now = timezone.now()
# #     upcoming_events = Event.objects.filter(
# #         status='approved',
# #         registration_deadline__range=(now, now + timezone.timedelta(hours=1))
# #     )

# #     students = User.objects.filter(role='Student')
# #     for event in upcoming_events:
# #         for student in students:
# #             # Check if reminder already sent
# #             if ReminderSent.objects.filter(
# #                 student=student,
# #                 event=event,
# #                 reminder_type='registration_closing'
# #             ).exists():
# #                 continue  # Skip if already sent

# #             # Send notification & email
# #             create_notification(
# #                 recipient=student,
# #                 title=f"Registration Closing Soon: {event.title}",
# #                 message=f"Registration for '{event.title}' closes within 1 hour. Don't miss it!",
# #                 notification_type='general',
# #                 event=event
# #             )
# #             if student.email:
# #                 send_email_notification(
# #                     student.email,
# #                     f"Registration Closing Soon: {event.title}",
# #                     f"Registration for '{event.title}' closes within 1 hour. Hurry up!"
# #                 )

# #             # Record that reminder has been sent
# #             ReminderSent.objects.create(
# #                 student=student,
# #                 event=event,
# #                 reminder_type='registration_closing'
# #             )


# # @shared_task
# # def send_registration_closing_reminders():
# #     now = timezone.now()
# #     upcoming_events = Event.objects.filter(
# #         status='approved',
# #         registration_deadline__range=(now, now + timezone.timedelta(hours=1))
# #     )

# #     for event in upcoming_events:
# #         # ✅ Recipients based on event scope
# #         if event.event_level == 'college':
# #             students = User.objects.filter(role='Student')
# #         elif event.event_level == 'organization':
# #             students = User.objects.filter(role='Student', organization=event.organizer.organization)
# #         elif event.event_level == 'department':
# #             students = User.objects.filter(role='Student', department=event.organizer.department)
# #         elif event.event_level == 'class':
# #             students = User.objects.filter(
# #                 role='Student',
# #                 profile__class_name=event.class_name,
# #                 profile__year=event.year,
# #                 profile__semester=event.semester
# #             )
# #         else:
# #             students = User.objects.none()

# #         for student in students:
# #             if ReminderSent.objects.filter(
# #                 student=student,
# #                 event=event,
# #                 reminder_type='registration_closing'
# #             ).exists():
# #                 continue  # already reminded

# #             # Send in-app notification
# #             create_notification(
# #                 recipient=student,
# #                 title=f"Registration Closing Soon: {event.title}",
# #                 message=f"Registration for '{event.title}' closes within 1 hour. Don't miss it!",
# #                 notification_type='general',
# #                 event=event
# #             )
# #             # Send email if available
# #             if student.email:
# #                 send_email_notification(
# #                     student.email,
# #                     f"Registration Closing Soon: {event.title}",
# #                     f"Registration for '{event.title}' closes within 1 hour. Hurry up!"
# #                 )
# # #Record that remainder has been sent.

# #             ReminderSent.objects.create(
# #                 student=student,
# #                 event=event,
# #                 reminder_type='registration_closing'
# #             )

# @shared_task
# def send_registration_closing_reminders():
#     now = timezone.now()
#     upcoming_events = Event.objects.filter(
#         status='approved',
#         registration_deadline__range=(now, now + timezone.timedelta(hours=1))
#     )

#     for event in upcoming_events:
#         #  Recipients based on event scope (USE THE SAME LOGIC AS YOUR APPROVAL SYSTEM)
#         if event.event_level == 'college':
#             students = User.objects.filter(role='Student')
        
#         elif event.event_level == 'organization':
#             students = User.objects.filter(
#                 role='Student', 
#                 organization=event.organizer.organization
#             )
        
#         elif event.event_level == 'department':
#             students = User.objects.filter(
#                 role='Student', 
#                 department=event.organizer.department
#             )
        
#         elif event.event_level == 'class':
#             # Convert year and semester to strings to match Profile field types
#             year_str = str(event.year) if event.year is not None else None
#             semester_str = str(event.semester) if event.semester is not None else None
            
#             # Build the base query - must have profile and matching class_name
#             query = Q(role='Student') & Q(profile__isnull=False) & Q(profile__class_name=event.class_name)
            
#             if year_str is not None and semester_str is not None:
#                 # Match (year=year_str AND year IS NOT NULL) OR (semester=semester_str AND semester IS NOT NULL)
#                 query &= (
#                     (Q(profile__year=year_str) & Q(profile__year__isnull=False)) |
#                     (Q(profile__semester=semester_str) & Q(profile__semester__isnull=False))
#                 )
#             elif year_str is not None:
#                 query &= Q(profile__year=year_str) & Q(profile__year__isnull=False)
#             elif semester_str is not None:
#                 query &= Q(profile__semester=semester_str) & Q(profile__semester__isnull=False)
#             else:
#                 # If both year and semester are None, return empty queryset
#                 query = Q(pk__in=[])  # Empty result
            
#             students = User.objects.filter(query)
        
#         else:
#             students = User.objects.none()

#         for student in students:
#             # Check if reminder already sent
#             if ReminderSent.objects.filter(
#                 student=student,
#                 event=event,
#                 reminder_type='registration_closing'
#             ).exists():
#                 continue  # already reminded

#             # Send in-app notification
#             create_notification(
#                 recipient=student,
#                 title=f"Registration Closing Soon: {event.title}",
#                 message=f"Registration for '{event.title}' closes within 1 hour. Don't miss it!",
#                 notification_type='reminder',
#                 event=event
#             )
            
#             # Send email if available
#             if student.email:
#                 send_email_notification(
#                     student.email,
#                     f"Registration Closing Soon: {event.title}",
#                     f"Registration for '{event.title}' closes within 1 hour. Hurry up and register now!"
#                 )
            
#             # Record that reminder has been sent
#             ReminderSent.objects.create(
#                 student=student,
#                 event=event,
#                 reminder_type='registration_closing'
#             )


# @shared_task
# def send_event_start_reminders():
#     now = timezone.now()
#     upcoming_events = Event.objects.filter(
#         status='approved',
#         start_date__range=(now, now + timezone.timedelta(hours=1))
#     )

#     for event in upcoming_events:
#         registrations = EventRegistration.objects.filter(event=event, status='confirmed')
#         for reg in registrations:
#             if ReminderSent.objects.filter(
#                 student=reg.student,
#                 event=event,
#                 reminder_type='event_start'
#             ).exists():
#                 continue  # Skip if already sent

#             create_notification(
#                 recipient=reg.student,
#                 title=f"Event Starting Soon: {event.title}",
#                 message=f"The event '{event.title}' starts within 1 hour. Be prepared!",
#                 notification_type='general',
#                 event=event
#             )
#             if reg.student.email:
#                 send_email_notification(
#                     reg.student.email,
#                     f"Event Starting Soon: {event.title}",
#                     f"The event '{event.title}' starts within 1 hour. Get ready!"
#                 )

#             ReminderSent.objects.create(
#                 student=reg.student,
#                 event=event,
#                 reminder_type='event_start'
#             )



# from celery import shared_task
# from django.utils import timezone
# from django.conf import settings
# from django.db.models import Q
# from events.models import Event, EventRegistration
# from users.models import User
# from notifications.utils import create_notification, send_email_notification
# from notifications.models import ReminderSent  # New import

# def _fmt_dt(dt):
#     if not dt:
#         return ""
#     dt_local = timezone.localtime(dt)
#     return dt_local.strftime("%b %d, %Y • %I:%M %p")

# def _event_register_url(event_id: int) -> str:
#     base = f"http://{getattr(settings, 'SITE_DOMAIN', 'localhost:8000')}".rstrip("/")
#     return f"{base}/api/v1/events/{event_id}/register/"

# @shared_task
# def send_registration_closing_reminders():
#     now = timezone.now()
#     upcoming_events = Event.objects.filter(
#         status='approved',
#         registration_deadline__range=(now, now + timezone.timedelta(hours=1))
#     )

#     for event in upcoming_events:
#         if event.event_level == 'college':
#             students = User.objects.filter(role='Student')
#         elif event.event_level == 'organization':
#             students = User.objects.filter(role='Student', organization=event.organizer.organization)
#         elif event.event_level == 'department':
#             students = User.objects.filter(role='Student', department=event.organizer.department)
#         elif event.event_level == 'class':
#             year_str = str(event.year) if event.year is not None else None
#             semester_str = str(event.semester) if event.semester is not None else None
#             query = Q(role='Student') & Q(profile__isnull=False) & Q(profile__class_name=event.class_name)
#             if year_str is not None and semester_str is not None:
#                 query &= (
#                     (Q(profile__year=year_str) & Q(profile__year__isnull=False)) |
#                     (Q(profile__semester=semester_str) & Q(profile__semester__isnull=False))
#                 )
#             elif year_str is not None:
#                 query &= Q(profile__year=year_str) & Q(profile__year__isnull=False)
#             elif semester_str is not None:
#                 query &= Q(profile__semester=semester_str) & Q(profile__semester__isnull=False)
#             else:
#                 query = Q(pk__in=[])
#             students = User.objects.filter(query)
#         else:
#             students = User.objects.none()

#         for student in students:
#             if ReminderSent.objects.filter(
#                 student=student,
#                 event=event,
#                 reminder_type='registration_closing'
#             ).exists():
#                 continue  # already reminded

#             start = _fmt_dt(event.start_date)
#             end = _fmt_dt(event.end_date)
#             title = f"⏰ Registration Closing Soon: {event.title}"
#             message = (
#                 f"Registration for **{event.title}** closes within 1 hour.\n\n"
#                 f"📍 Venue: {event.venue}\n"
#                 f"🕒 Time: {start} → {end}\n\n"
#                 f"Register here: {_event_register_url(event.id)}"
#             )

#             create_notification(
#                 recipient=student,
#                 title=title,
#                 message=message,
#                 notification_type='reminder',
#                 event=event
#             )
#             if student.email:
#                 send_email_notification(
#                     student.email,
#                     title,
#                     message
#                 )
#             ReminderSent.objects.create(
#                 student=student,
#                 event=event,
#                 reminder_type='registration_closing'
#             )

# @shared_task
# def send_event_start_reminders():
#     now = timezone.now()
#     upcoming_events = Event.objects.filter(
#         status='approved',
#         start_date__range=(now, now + timezone.timedelta(hours=1))
#     )

#     for event in upcoming_events:
#         registrations = EventRegistration.objects.filter(event=event, status='confirmed')
#         for reg in registrations:
#             if ReminderSent.objects.filter(
#                 student=reg.student,
#                 event=event,
#                 reminder_type='event_start'
#             ).exists():
#                 continue  # Skip if already sent

#             start = _fmt_dt(event.start_date)
#             end = _fmt_dt(event.end_date)
#             title = f"🚀 Starting Soon: {event.title}"
#             message = (
#                 f"The event **{event.title}** starts within 1 hour.\n\n"
#                 f"📍 Venue: {event.venue}\n"
#                 f"🕒 Time: {start} → {end}\n\n"
               
#             )

#             create_notification(
#                 recipient=reg.student,
#                 title=title,
#                 message=message,
#                 notification_type='reminder',
#                 event=event
#             )
#             if reg.student.email:
#                 send_email_notification(
#                     reg.student.email,
#                     title,
#                     message
#                 )

#             ReminderSent.objects.create(
#                 student=reg.student,
#                 event=event,
#                 reminder_type='event_start'
#             )


# notifications/tasks.py
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from events.models import Event, EventRegistration
from users.models import User
from notifications.utils import create_notification, send_email_notification
from notifications.models import ReminderSent


LEAD_MINUTES = 60            # send 1 hour before
TOLERANCE_MINUTES = 1        # ±1 minute window (with beat every minute)

def _fmt_dt(dt):
    if not dt:
        return ""
    dt_local = timezone.localtime(dt)
    return dt_local.strftime("%b %d, %Y • %I:%M %p")

def _event_register_url(event_id: int) -> str:
    base = f"http://{getattr(settings, 'SITE_DOMAIN', 'localhost:8000')}".rstrip("/")
    return f"{base}/api/v1/events/{event_id}/register/"

def _eligible_students_for_event(event: Event):
    """Replicates your audience scope rules."""
    if event.event_level == 'college':
        return User.objects.filter(role='Student')

    if event.event_level == 'organization':
        return User.objects.filter(role='Student', organization=event.organizer.organization)

    if event.event_level == 'department':
        return User.objects.filter(role='Student', department=event.organizer.department)

    if event.event_level == 'class':
        year_str = str(event.year) if event.year is not None else None
        semester_str = str(event.semester) if event.semester is not None else None
        q = Q(role='Student') & Q(profile__isnull=False) & Q(profile__class_name=event.class_name)
        if year_str is not None and semester_str is not None:
            q &= ((Q(profile__year=year_str) & Q(profile__year__isnull=False)) |
                  (Q(profile__semester=semester_str) & Q(profile__semester__isnull=False)))
        elif year_str is not None:
            q &= Q(profile__year=year_str) & Q(profile__year__isnull=False)
        elif semester_str is not None:
            q &= Q(profile__semester=semester_str) & Q(profile__semester__isnull=False)
        else:
            q = Q(pk__in=[])  # empty
        return User.objects.filter(q)

    return User.objects.none()


@shared_task
def send_registration_closing_reminders():
    now = timezone.now()
    window_start = now + timedelta(minutes=LEAD_MINUTES)
    window_end = window_start + timedelta(minutes=TOLERANCE_MINUTES)

    # Only approved events whose registration deadline is ~60 minutes from now
    events = Event.objects.filter(
        status='approved',
        registration_deadline__gte=window_start,
        registration_deadline__lt=window_end,
    )

    for event in events:
        students = _eligible_students_for_event(event)

        for student in students:
            # de-dup
            if ReminderSent.objects.filter(
                student=student,
                event=event,
                reminder_type='registration_closing'
            ).exists():
                continue

            start = _fmt_dt(event.start_date)
            end = _fmt_dt(event.end_date)
            title = f"⏰ Registration Closing Soon: {event.title}"
            message = (
                f"Registration for **{event.title}** closes in ~1 hour.\n\n"
                f"📍 Venue: {event.venue}\n"
                f"🕒 Time: {start} → {end}\n\n"
                f"Register here: {_event_register_url(event.id)}"
            )

            create_notification(
                recipient=student,
                title=title,
                message=message,
                notification_type='reminder',
                event=event,
            )

            if student.email:
                send_email_notification(student.email, title, message)

            ReminderSent.objects.create(
                student=student,
                event=event,
                reminder_type='registration_closing'
            )


@shared_task
def send_event_start_reminders():
    now = timezone.now()
    window_start = now + timedelta(minutes=LEAD_MINUTES)
    window_end = window_start + timedelta(minutes=TOLERANCE_MINUTES)

    # Only approved events whose start is ~60 minutes from now
    events = Event.objects.filter(
        status='approved',
        start_date__gte=window_start,
        start_date__lt=window_end,
    )

    for event in events:
        regs = EventRegistration.objects.filter(event=event, status='confirmed').select_related('student')
        for reg in regs:
            # de-dup
            if ReminderSent.objects.filter(
                student=reg.student,
                event=event,
                reminder_type='event_start'
            ).exists():
                continue

            start = _fmt_dt(event.start_date)
            end = _fmt_dt(event.end_date)
            title = f"🚀 Starting in ~1 hour: {event.title}"
            message = (
                f"The event **{event.title}** starts in ~1 hour.\n\n"
                f"📍 Venue: {event.venue}\n"
                f"🕒 Time: {start} → {end}\n\n"
            )

            create_notification(
                recipient=reg.student,
                title=title,
                message=message,
                notification_type='reminder',
                event=event,
            )

            if reg.student.email:
                send_email_notification(reg.student.email, title, message)

            ReminderSent.objects.create(
                student=reg.student,
                event=event,
                reminder_type='event_start'
            )
