from django.db import models
from django.conf import settings
from events.models import Event

# Create your models here.

class Certificate(models.Model):
    event=models.ForeignKey(Event, on_delete=models.CASCADE, related_name='certificates')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    issued_at= models.DateTimeField(auto_now_add=True)
    certificate_file= models.FileField(upload_to='certificates/')
    sent_via_email = models.BooleanField(default=False)
    
class Meta:
    unique_together= ('event','student')

def __str__(self):
    return f"Certificate for {self.student.username} - {self.event.title}"
