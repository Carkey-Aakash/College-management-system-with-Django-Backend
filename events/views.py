

from django.shortcuts import render, redirect
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models  import Q, Count, Avg
from django.utils import timezone
from .models import Event, EventRegistration, EventFeedback, EventConflict
from .serializers import EventSerializer, EventCreateSerializer, EventRegistrationSerializer, EventFeedbackSerializer, EventApprovalSerializer, EventConflictSerializer
from rest_framework.exceptions import PermissionDenied
from .permissions import IsEventManagerOrReadOnly
from users.models import CollegeStudent

from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from django.utils.decorators import method_decorator

from users.models import User
from .utils import detect_event_conflicts  #, send_event_notification
from notifications.utils import create_notification, send_email_notification

from rest_framework.exceptions import PermissionDenied


# ---------- Helpers for notifications/links/formatting ----------

def _base_url() -> str:
    """Absolute base URL from settings.SITE_DOMAIN (e.g., 192.168.1.81:8000)"""
    return f"http://{getattr(settings, 'SITE_DOMAIN', 'localhost:8000')}".rstrip("/")

def _event_api_url(event_id: int) -> str:
    """Mobile-safe absolute API URL for event details"""
    return f"{_base_url()}/api/v1/events/{event_id}/"

def _event_register_url(event_id: int) -> str:
    """Absolute URL used in notifications for 1-click register (HTML flow)"""
    return f"{_base_url()}/api/v1/events/{event_id}/register/"

def _fmt_dt(dt):
    """Pretty datetime for notifications (example: Aug 28, 2025 • 08:45 PM)"""
    if not dt:
        return ""
    # You already use TIME_ZONE = 'Asia/Kathmandu' with USE_TZ = True
    local = timezone.localtime(dt)
    return local.strftime("%b %d, %Y • %I:%M %p")


class EventListCreateView(generics.ListCreateAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Event.objects.all()

        # Auto-update event status
        now = timezone.now()
        for event in queryset:
            if event.end_date and event.end_date < now and event.status == 'approved':
                event.status = 'completed'
                event.completion_notified= True
                event.save()
                admins = User.objects.filter(role='Admin')
                for admin in admins:
                    create_notification(
                        recipient=admin,
                        title=f"✅ Event Completed: {event.title}",
                        message=(
                            f"The event **{event.title}** has been marked as *completed*.\n\n"
                            f"🕒 Time: {_fmt_dt(event.start_date)} → {_fmt_dt(event.end_date)}\n"
                            f"📍 Venue: {event.venue}\n\n"
                            f"Details: {_event_api_url(event.id)}"
                        ),
                        notification_type='event_completed',
                        event=event
                    )

        # Filter based on user role
        if user.is_student():
            queryset = queryset.filter(status='approved')
        elif user.is_department():
            queryset = queryset.filter(Q(organizer=user) | Q(status='approved'))
        elif user.is_organization():
            queryset = queryset.filter(Q(organizer=user) | Q(status='approved'))

        # Filter by event level, type, status
        event_level = self.request.query_params.get('level', None)
        event_type = self.request.query_params.get('type', None)
        status_filter = self.request.query_params.get('status', None)

        if event_level:
            queryset = queryset.filter(event_level=event_level)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EventCreateSerializer
        return EventSerializer

    def perform_create(self, serializer):
        user = self.request.user

        #  Allow Only Faculty, Organization to Create Events
        if not (user.is_department() or user.is_organization() ):
            raise PermissionDenied("Only Department, organizations can create events.")

        event = serializer.save()

        # Check for conflicts
        conflicts = detect_event_conflicts(event)
        if conflicts:
            for conflict_event in conflicts:
                EventConflict.objects.create(
                    event1=event,
                    event2=conflict_event,
                    description=f"Venue and time overlap detected between {event.title} and {conflict_event.title}"
                )

        # Auto-approve class level events for faculty department  or organization
        if event.event_level == 'class' and (event.organizer.is_department() or event.organizer.is_organization()):
            event.status = 'approved'
            event.save()

        # Notify audience
        if event.event_level == 'class':
            # Convert year and semester to strings to match Profile field types
            year_str = str(event.year) if event.year is not None else None
            semester_str = str(event.semester) if event.semester is not None else None

            # Build the base query - must have profile and EXACT matching class_name
            query = Q(role='Student') & Q(profile__isnull=False) & Q(profile__class_name=event.class_name)

            if year_str is not None and semester_str is not None:
                query = query & (
                    (Q(profile__year=year_str) & Q(profile__year__isnull=False)) |
                    (Q(profile__semester=semester_str) & Q(profile__semester__isnull=False))
                )
            elif year_str is not None:
                query = query & Q(profile__year=year_str) & Q(profile__year__isnull=False)
            elif semester_str is not None:
                query = query & Q(profile__semester=semester_str) & Q(profile__semester__isnull=False)
            else:
                # If both year and semester are None, return empty queryset
                query = Q(pk__in=[])  # Empty result

            students = User.objects.filter(query)

            # DEBUG: Print the students who will receive notifications
            print(f"[DEBUG] Class-level event targeting: {students.count()} students")
            for student in students:
                profile = student.profile
                print(f"  - {student.username}: class={profile.class_name}, year={profile.year}, semester={profile.semester}")

            # Notify only the targeted students (richer message + working link)
            for student in students:
                title = f"📢 New Class Event: {event.title}"
                message = (
                    f"A new *{event.get_event_type_display().lower()}* event **{event.title}** has been scheduled for your class.\n\n"
                    f"📍 Venue: {event.venue}\n"
                    f"🕒 Time: {_fmt_dt(event.start_date)} → {_fmt_dt(event.end_date)}\n"
                    f"👥 Slots: {event.get_available_slots()} / {event.max_participants}\n\n"
                    f"For further details  see the event page:\n{_event_api_url(event.id)} , and for registration see this link:\n{_event_register_url(event.id)}"
                )
                create_notification(
                    recipient=student,
                    title=title,
                    message=message,
                    notification_type='event_created',
                    event=event
                )
                if student.email:
                    send_email_notification(
                        student.email,
                        title,
                        message
                    )

        else:
            # Notify Campus Chief with in-app and email
            campus_chief = User.objects.filter(role="Campus-cheif").first()
            if campus_chief:
                title = f"📝 New Event Submitted: {event.title}"
                message = (
                    f"A new event **{event.title}** has been submitted for approval.\n\n"
                    f"📍 Venue: {event.venue}\n"
                    f"🕒 Time: {_fmt_dt(event.start_date)} → {_fmt_dt(event.end_date)}\n\n"
                    f"Details: {_event_api_url(event.id)}"
                )
                create_notification(
                    recipient=campus_chief,
                    title=title,
                    message=message,
                    notification_type='event_created',
                    event=event
                )
                if campus_chief.email:
                    send_email_notification(
                        campus_chief.email,
                        title,
                        message
                    )

    #  Override list() method to show "No events available yet" message
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if not queryset.exists():
            return Response({"message": "No events available yet."})

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



@csrf_exempt
def event_detail_or_login(request, pk):
    """
    - If unauthenticated: show login form (GET) or process it (POST).
    - If authenticated: delegate to EventDetailView to return JSON.
    """
    if not request.user.is_authenticated:
        if request.method == 'POST':
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                return redirect(request.path)  # comes back authenticated → JSON
            else:
                return render(
                    request,
                    'events/attendance_login.html',
                    {'form': form, 'next': request.get_full_path(), 'errors': form.errors}
                )
        else:
            form = AuthenticationForm()
            return render(
                request,
                'events/attendance_login.html',
                {'form': form, 'next': request.get_full_path()}
            )

    view = EventDetailView.as_view()
    return view(request, pk=pk)

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET:
      - If NOT authenticated: renders login form (re-uses attendance_login.html)
      - If authenticated: returns event JSON
    POST:
      - If NOT authenticated: accepts AuthenticationForm, logs in, then redirects back to same URL
      - If authenticated: behaves like retrieve
    PUT/PATCH/DELETE:
      - Governed by IsEventManagerOrReadOnly (must be organizer/admin etc.)
    """
    serializer_class = EventSerializer
    # AllowAny here; we'll gate write methods via IsEventManagerOrReadOnly and checks below
    permission_classes = [permissions.AllowAny, IsEventManagerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and (user.is_admin_user() or user.is_chief()):
            return Event.objects.all()
        elif user.is_authenticated and (user.is_department() or user.is_organization()):
            return Event.objects.all()
        else:
            return Event.objects.filter(status='approved')

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            form = AuthenticationForm()
            return render(
                request,
                'events/attendance_login.html',  # your existing template
                {'form': form, 'next': request.get_full_path()}
            )
        # authenticated → JSON
        return self.retrieve(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        # If already authenticated, just show JSON
        if request.user.is_authenticated:
            return self.retrieve(request, *args, **kwargs)

        # Login attempt with AuthenticationForm
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get('next') or request.get_full_path()
            return redirect(next_url)

        return render(
            request,
            'events/attendance_login.html',
            {'form': form, 'next': request.get_full_path(), 'errors': form.errors}
        )

    def update(self, request, *args, **kwargs):
        event = self.get_object()

        # Only organizer can update
        if event.organizer != request.user:
            raise PermissionDenied("You are not event organizer and haven’t authority to change it.")

        old_status = event.status  # Save current status before update

        response = super().update(request, *args, **kwargs)
        event.refresh_from_db()

        # Re-check conflicts after update
        conflicts = detect_event_conflicts(event)

        # Resolve old conflicts if no longer conflicting
        existing_conflicts = EventConflict.objects.filter(
            Q(event1=event) | Q(event2=event),
            status='detected'
        )
        for conflict in existing_conflicts:
            still_conflict = False
            for other_event in conflicts:
                if other_event.id == conflict.event1.id or other_event.id == conflict.event2.id:
                    still_conflict = True
                    break
            if not still_conflict:
                conflict.status = 'resolved'
                conflict.resolved_at = timezone.now()
                conflict.save()

        # ✅ Send Notifications based on status
        if old_status == 'approved' or event.status == 'approved':
            # Notify all students about update
            students = User.objects.filter(role='Student')
            for student in students:
                title = f"✏️ Event Updated: {event.title}"
                message = (
                    f"The event **{event.title}** has been updated.\n\n"
                    f"📍 Venue: {event.venue}\n"
                    f"🕒 Time: {_fmt_dt(event.start_date)} → {_fmt_dt(event.end_date)}\n\n"
                    f"Details: {_event_api_url(event.id)}"
                )
                create_notification(
                    recipient=student,
                    title=title,
                    message=message,
                    notification_type='event_update',
                    event=event
                )
                if student.email:
                    send_email_notification(
                        student.email,
                        title,
                        message
                    )

        elif old_status in ['pending', 'cancelled'] or event.status in ['pending', 'cancelled']:
            # Notify Campus Chief about update
            campus_chief = User.objects.filter(role='Campus-cheif').first()
            if campus_chief:
                title = f"🔔 Event Update Request: {event.title}"
                message = (
                    f"The event **{event.title}** has been updated and requires your review.\n\n"
                    f"📍 Venue: {event.venue}\n"
                    f"🕒 Time: {_fmt_dt(event.start_date)} → {_fmt_dt(event.end_date)}\n\n"
                    f"Details: {_event_api_url(event.id)}"
                )
                create_notification(
                    recipient=campus_chief,
                    title=title,
                    message=message,
                    notification_type='event_update',
                    event=event
                )
                if campus_chief.email:
                    send_email_notification(
                        campus_chief.email,
                        title,
                        message
                    )

        return response

    def destroy(self, request, *args, **kwargs):
        event = self.get_object()
        if event.organizer != request.user:
            raise PermissionDenied("You are not event organizer and haven’t authority to change it.")
        return super().destroy(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pending_events_list(request):
    user = request.user

    # Check if user is campus-chief or admin
    if not (user.is_chief() or user.is_admin_user()):
        return Response(
            {'error': 'You are not allowed to see the pending events.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get all events with status 'pending'
    pending_events = Event.objects.filter(status='pending').order_by('-created_at')

    if not pending_events.exists():
        return Response(
            {'message': 'No any pending events.'},
            status=status.HTTP_200_OK
        )

    serializer = EventSerializer(pending_events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def cancelled_events_list(request):
    user = request.user

    # Check if user is campus-chief or admin
    if not (user.is_chief() or user.is_admin_user()):
        return Response(
            {'error': 'You are not allowed to see the cancelled events.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get all events with status 'cancelled'
    cancelled_events = Event.objects.filter(status='cancelled').order_by('-updated_at')

    if not cancelled_events.exists():
        return Response(
            {'message': 'No any cancelled events.'},
            status=status.HTTP_200_OK
        )

    serializer = EventSerializer(cancelled_events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Anyone can access
def completed_events_list(request):
    # Get all events with status 'completed'
    completed_events = Event.objects.filter(status='completed').order_by('-end_date')

    if not completed_events.exists():
        return Response(
            {'message': 'No completed events found.'},
            status=status.HTTP_200_OK
        )

    serializer = EventSerializer(completed_events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_reject_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Only campus-chief can approve/reject/cancel
    if not request.user.is_chief():
        return Response({'error': 'Only campus-chief can approve/reject/cancel events.'},
                        status=status.HTTP_403_FORBIDDEN)

    # Check for already approved events
    if event.status == 'approved':
        return Response({'message': 'Already approved event cannot be approved again.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Validate status field
    status_value = request.data.get('status')
    if not status_value:
        return Response({'error': 'You must provide a status to approve/reject/cancel the event.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # New Conflict Check when trying to approve
    if status_value == 'approved':
        from .utils import detect_event_conflicts
        conflicts = detect_event_conflicts(event)
        if conflicts:
            conflict_titles = [f"{conflict.title}" for conflict in conflicts]
            return Response(
                {
                    'error': f"Event conflict detected with: {', '.join(conflict_titles)}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    serializer = EventApprovalSerializer(event, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save(approved_by=request.user)

        # Notify Event Organizer about decision (in-app + email)
        title_org = f"Your Event '{event.title}' was {event.status}"
        message_org = (
            f"Campus Chief has **{event.status}** your event **{event.title}**.\n\n"
            f"📍 Venue: {event.venue}\n"
            f"🕒 Time: {_fmt_dt(event.start_date)} → {_fmt_dt(event.end_date)}\n\n"
            f"Details: {_event_api_url(event.id)}"
        )
        create_notification(
            recipient=event.organizer,
            title=title_org,
            message=message_org,
            notification_type=f"event_{event.status}",
            event=event
        )
        if event.organizer.email:
            send_email_notification(
                event.organizer.email,
                title_org,
                message_org
            )

        # ⚠️ SKIP NOTIFICATION LOGIC FOR CLASS-LEVEL EVENTS ⚠️
        # They were already notified when created in EventListCreateView.perform_create()
        if event.event_level == 'class':
            return Response({
                'message': f'Class level event is {event.status}. No additional notifications sent.',
                'event': EventSerializer(event).data
            }, status=status.HTTP_200_OK)

        # If approved → notify targeted students (only for non-class events)
        if event.status == 'approved':
            if event.event_level == 'college':
                students = User.objects.filter(role='Student')

            elif event.event_level == 'organization':
                students = User.objects.filter(
                    role='Student',
                    organization=event.organizer.organization
                )

            elif event.event_level == 'department':
                students = User.objects.filter(
                    role='Student',
                    department=event.organizer.department
                )

            # Send notifications and emails
            for student in students:
                title = f"✅ Event Approved: {event.title}"
                message = (
                    f"The {event.get_event_level_display().replace('_', ' ').title()} event **{event.title}** has been approved and is now open.\n\n"
                    f"📍 Venue: {event.venue}\n"
                    f"🕒 Time: {_fmt_dt(event.start_date)} → {_fmt_dt(event.end_date)}\n"
                    f"👥 Slots: {event.get_available_slots()} / {event.max_participants}\n\n"
                    f"Details: {_event_api_url(event.id)} , and for registration see this link:\n{_event_register_url(event.id)}"
                )
                create_notification(
                    recipient=student,
                    title=title,
                    message=message,
                    notification_type='event_approved',
                    event=event
                )
                if student.email:
                    send_email_notification(
                        student.email,
                        title,
                        message
                    )

        return Response({
            'message': f'Event is {event.status}.',
            'event': EventSerializer(event).data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def register_for_event(request, event_id):
    # Register a student for an event verifying phone and email
    if not request.user.is_student():
        return Response({'error': 'Only students can register for events'},
                       status=status.HTTP_403_FORBIDDEN)

    event = get_object_or_404(Event, id=event_id)

    # Check if registration is open
    if not event.is_registration_open():
        return Response({'error': 'Registration is closed for this event'},
                       status=status.HTTP_400_BAD_REQUEST)

    # Check if already registered
    existing_registration = EventRegistration.objects.filter(event=event, student=request.user).first()
    if existing_registration:
        if existing_registration.status == 'pending':
            return Response({'message': 'Your registration is pending. Please complete the payment.'},
                            status=status.HTTP_400_BAD_REQUEST)
        elif existing_registration.status == 'confirmed':
            return Response({'message': 'You are already registered for this event.'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': f'You have already registered with status: {existing_registration.status}.'},
                            status=status.HTTP_400_BAD_REQUEST)

    # verify student's Email or Phone in college Database
    try:
        college_record = CollegeStudent.objects.get(username=request.user.username)
    except CollegeStudent.DoesNotExist:
        return Response({
            'error': 'Your username does not exist in the college database. Registration denied.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check email or phone number match
    email_match = (college_record.email and college_record.email == request.user.email)
    phone_match = (college_record.phone_number and college_record.phone_number == request.user.phone_number)

    if not (email_match or phone_match):
        return Response({
            'error': 'Your email or phone number does not match the college database. Registration denied.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Register the student
    registration = EventRegistration.objects.create(
        event=event,
        student=request.user,
        status='confirmed' if not event.is_paid_event else 'pending'
    )

    # Notify student (in-app + email)
    title = f"🎟️ Registration Successful: {event.title}"
    message = (
        f"You have successfully registered for **{event.title}**.\n\n"
        f"📍 Venue: {event.venue}\n"
        f"🕒 Time: {_fmt_dt(event.start_date)} → {_fmt_dt(event.end_date)}\n\n"
        f"Details: {_event_api_url(event.id)}"
    )
    create_notification(
        recipient=request.user,
        title=title,
        message=message,
        notification_type='registration_confirmation',
        event=event
    )
    if request.user.email:
        send_email_notification(
            request.user.email,
            title,
            message
        )

    return Response({
        'message': 'Registration successful',
        'registration': EventRegistrationSerializer(registration).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_registration(request, event_id):
    # Cancel event registration
    event = get_object_or_404(Event, id=event_id)

    try:
        registration = EventRegistration.objects.get(event=event, student=request.user)
        registration.status = 'cancelled'
        registration.save()
        return Response({'message': 'Registration cancelled successfully'})
    except EventRegistration.DoesNotExist:
        return Response({'error': 'Registration not found'},
                       status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
@csrf_exempt
def attendance_verify(request):
    event_id = request.GET.get('event_id')
    qr = request.GET.get('qr')

    if not event_id or not qr:
        return Response({'error': 'Invalid attendance link'}, status=400)

    event = get_object_or_404(Event, id=event_id)

    # Check if current time is within event time (valid QR)
    now = timezone.now()
    if not (event.start_date <= now <= event.end_date):
        return HttpResponse("QR code expired or event is not active.", status=400)

    # Check QR data matches stored qr_code_data (optional if you stored it)
    if hasattr(event, 'qr_code_data') and event.qr_code_data != qr:
        return HttpResponse("Invalid QR code.", status=400)

    if request.method == 'GET':
        # If user is not authenticated, show login form
        if not request.user.is_authenticated:
            form = AuthenticationForm()
            return render(request, 'events/attendance_login.html', {'form': form, 'event': event, 'qr': qr})

        # User already logged in → mark attendance
        return mark_attendance_for_user(request.user, event, qr)

    elif request.method == 'POST':
        # Process login form submission
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return mark_attendance_for_user(user, event, qr)
        else:
            return render(request, 'attendance_login.html', {'form': form, 'event': event, 'qr': qr, 'errors': form.errors})


def mark_attendance_for_user(user, event, qr):
    # Verify user is student and registered for event
    if not user.is_student():
        return HttpResponse("Only students can mark attendance.", status=403)

    try:
        registration = EventRegistration.objects.get(event=event, student=user, status='confirmed')
    except EventRegistration.DoesNotExist:
        return HttpResponse("You are not registered or registration not confirmed.", status=403)

    registration.attended = True
    registration.attendance_marked_at = timezone.now()
    registration.save()

    return HttpResponse("Attendance marked successfully! Thank you.", status=200)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_feedback(request, event_id):
    # Submit feedback for an event
    if not request.user.is_student():
        return Response(
            {'error': 'You are not allowed to give feedback. Only students can submit feedback.'},
            status=status.HTTP_403_FORBIDDEN
        )
    event = get_object_or_404(Event, id=event_id)

    try:
        registration = EventRegistration.objects.get(
            event=event,
            student=request.user,
            attended=True
        )

        # Check if feedback already exists
        if hasattr(registration, 'feedback'):
            return Response({'error': 'Feedback already submitted'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Pass extra data via context
        serializer = EventFeedbackSerializer(
            data=request.data,
            context={
                'student': request.user,
                'registration': registration,
                'event': event
            }
        )
        if serializer.is_valid():
            feedback = serializer.save()

            # Mark feedback given
            registration.feedback_given = True
            registration.save()

            return Response({
                'message': 'Feedback submitted successfully',
                'feedback': EventFeedbackSerializer(feedback).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except EventRegistration.DoesNotExist:
        return Response({'error': 'Must attend event to give feedback'},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def event_statistics(request, event_id):
    # Get statistics for an event (Organizer/Admin/Chief only)
    event = get_object_or_404(Event, id=event_id)

    # ✅ Allow organizer, admin, or campus chief
    if not (request.user == event.organizer or request.user.is_admin_user() or request.user.is_chief()):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # Calculate statistics
    total_registrations = event.registrations.count()
    confirmed_registrations = event.registrations.filter(status='confirmed').count()
    attended_count = event.registrations.filter(attended=True).count()
    feedback_count = event.feedbacks.count()

    # Average ratings
    from django.db.models import Avg
    avg_rating = event.feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    avg_content_rating = event.feedbacks.aggregate(Avg('content_quality_rating'))['content_quality_rating__avg'] or 0
    avg_organization_rating = event.feedbacks.aggregate(Avg('organization_rating'))['organization_rating__avg'] or 0

    return Response({
        'event_title': event.title,
        'total_registrations': total_registrations,
        'confirmed_registrations': confirmed_registrations,
        'attended_count': attended_count,
        'attendance_rate': (attended_count / confirmed_registrations * 100) if confirmed_registrations > 0 else 0,
        'feedback_count': feedback_count,
        'feedback_rate': (feedback_count / attended_count * 100) if attended_count > 0 else 0,
        'average_rating': round(avg_rating, 2),
        'average_content_rating': round(avg_content_rating, 2),
        'average_organization_rating': round(avg_organization_rating, 2),
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_events(request):
    user = request.user

    if user.is_student():
        registrations = EventRegistration.objects.filter(student=user).select_related('event')
        events_data = []
        for reg in registrations:
            event_data = EventSerializer(reg.event).data
            event_data['registration_status'] = reg.status
            event_data['attended'] = reg.attended
            event_data['feedback_given'] = reg.feedback_given
            events_data.append(event_data)
        return Response(events_data)

    elif user.is_department():
        events = Event.objects.filter(organizer=user)
        return Response(EventSerializer(events, many=True).data)

    elif user.is_organization():
        events = Event.objects.filter(organizer=user)
        return Response(EventSerializer(events, many=True).data)

    elif user.is_chief():
        # Deny permission for chief
        raise PermissionDenied("Campus Chief is not allowed to access this resource.")

    elif user.is_admin_user():
        events = Event.objects.all()
        return Response(EventSerializer(events, many=True).data)

    return Response([])


class EventConflictListView(generics.ListAPIView):
    # List all event conflicts (Admin/Chief only)
    serializer_class = EventConflictSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user() or user.is_chief():
            return EventConflict.objects.filter(status='detected')
        return EventConflict.objects.none()

    def list(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_admin_user() or user.is_chief()):
            return Response(
                {"error": "You are not authorized to see this URL."},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No conflict event right now."},
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
