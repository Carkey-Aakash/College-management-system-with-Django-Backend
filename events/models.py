from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
import uuid
from django.conf import settings
# Create your models here.

User =get_user_model()
class Event(models.Model):
    EVENT_LEVEL_CHOICES = [
        ('class', 'Class Level'),
        ('department','Department_Level'),
        ('organization', 'Organization_Level'),
        ('college', 'College_Level'),
    ]

    EVENT_TYPE_CHOICES = [
        ('technical', 'Technical'),
        ('non_technical', 'Non-Technical'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('competition', 'Competition'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('others','others')
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Basic event information
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_level = models.CharField(max_length=20, choices=EVENT_LEVEL_CHOICES)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    completion_notified = models.BooleanField(default=False)
    class_name = models.CharField(max_length=100, null=True, blank=True)
    year = models.CharField(null=True, blank=True)
    semester = models.CharField(null=True, blank=True)

    #Event schudeling 

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.CharField(max_length=200)

    # Event management
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_events')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Registration settings
    max_participants = models.IntegerField(default=100)
    registration_deadline = models.DateTimeField()
    is_paid_event = models.BooleanField(default=False)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Event resources
    poster = models.ImageField(upload_to='event_posters/', blank=True, null=True)

    # QR Code for attendance
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_code_data = models.CharField(max_length=50, blank=True, null=True, help_text="Unique QR code string for attendance verification")
    #Status like with reason 
    status_comments = models.TextField(blank=True, help_text="Optional comments related to the current status.")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError('Start date must be before end date')
            
        if self.registration_deadline and self.start_date:
            if self.registration_deadline >= self.start_date:
                raise ValidationError('Registration deadline must be before event start date')
    
    
    def save(self, *args, **kwargs):
        # Generate QR code when event is approved
        if self.status == 'approved' and not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)


    # def generate_qr_code(self):
    #     # Use your local IP and port here — change if needed
    #     base_url = 'http://192.168.1.81:8000'  
    #     qr_value = f"eventify_attendance_{self.id}_{uuid.uuid4().hex[:8]}"
    #     attendance_url = f"{base_url}/api/v1/events/attendance/verify/?event_id={self.id}&qr={qr_value}"

    #     qr = qrcode.QRCode(version=1, box_size=10, border=5)
    #     qr.add_data(attendance_url)
    #     qr.make(fit=True)

    #     img = qr.make_image(fill_color="black", back_color="white")
    #     buffer = BytesIO()
    #     img.save(buffer, format='PNG')
    #     buffer.seek(0)

    #     filename = f'qr_event_{self.id}.png'
    #     self.qr_code.save(filename, File(buffer), save=False)

    #     # Store the generated QR string (not URL) for later verification (optional)
    #     self.qr_code_data = qr_value  # You might want to add this field in your model


    def generate_qr_code(self):
        # Build base URL from settings (works on LAN or prod)
        base_url = f"http://{settings.SITE_DOMAIN}".rstrip("/")

        qr_value = f"eventify_attendance_{self.id}_{uuid.uuid4().hex[:8]}"
        attendance_url = f"{base_url}/api/v1/events/attendance/verify/?event_id={self.id}&qr={qr_value}"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(attendance_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        filename = f'qr_event_{self.id}.png'
        self.qr_code.save(filename, File(buffer), save=False)

        # store short token to verify later
        self.qr_code_data = qr_value

    def is_registration_open(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'approved' and
            self.registration_deadline and now <= self.registration_deadline
        )
    def get_registered_count(self):
        
        return self.registrations.filter(status='confirmed').count()
    
    def get_available_slots(self):
        
        return max(0, self.max_participants - self.get_registered_count())
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    class Meta:
        db_table = 'events_event'
        ordering = ['-created_at']

class EventRegistration(models.Model):
    
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    
    # Registration details
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment details (for paid events)
    payment_status = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    
    # Attendance tracking
    attended = models.BooleanField(default=False)
    attendance_marked_at = models.DateTimeField(null=True, blank=True)
    
    # Feedback
    feedback_given = models.BooleanField(default=False)
    
    def clean(self):
        
        if not self.student.is_student():
            raise ValidationError('Only students can register for events')
        
        if not self.event.is_registration_open():
            raise ValidationError('Registration is closed for this event')
    
    def __str__(self):
        return f"{self.student.username} - {self.event.title}"
    
    class Meta:
        db_table = 'events_registration'
        unique_together = ['event', 'student']  # Prevent duplicate registrations


class EventFeedback(models.Model):
    
    
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedbacks')
    Student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_feedbacks')
    registration = models.OneToOneField(EventRegistration, on_delete=models.CASCADE, related_name='feedback')
    
    # Feedback content
    rating = models.IntegerField(choices=RATING_CHOICES)
    content_quality_rating = models.IntegerField(choices=RATING_CHOICES)
    organization_rating = models.IntegerField(choices=RATING_CHOICES)
    
    comments = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)
    
    # Recommendation
    would_recommend = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        
        if not self.registration.attended:
            raise ValidationError('Feedback can only be given by attendees')
        
        if self.event.status != 'completed':
            raise ValidationError('Feedback can only be given after event completion')
    
    def __str__(self):
        return f"Feedback for {self.event.title} by {self.Student.username}"
    
    class Meta:
        db_table = 'events_feedback'
        unique_together = ['event', 'Student']

class EventConflict(models.Model):
    
    # Model to track and resolve event scheduling conflicts
    
    
    STATUS_CHOICES = [
        ('detected', 'Detected'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    ]
    
    event1 = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='conflicts_as_event1')
    event2 = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='conflicts_as_event2')
    
    conflict_type = models.CharField(max_length=50, default='venue_time_overlap')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Conflict: {self.event1.title} vs {self.event2.title}"