from celery import shared_task
from events.models import EventRegistration
from .utils import create_and_send_certificate

@shared_task

def send_certificates_for_workshop_event(event_id):
    registrations=EventRegistration.objects.filter(event_id=event_id,attended=True)
    for reg in registrations:
        create_and_send_certificate(reg)