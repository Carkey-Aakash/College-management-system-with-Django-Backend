# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from events.models import Event
# from .tasks import send_certificates_for_workshop_event


# @receiver(post_save, sender=Event)
# def event_completion_handler(sender, instance, **kwargs):
#     if instance.status == 'completed' and instance.event_type == 'workshop':
#         send_certificates_for_workshop_event.delay(instance.id)


from django.db.models.signals import post_save
from django.dispatch import receiver
from events.models import Event
from .tasks import send_certificates_for_workshop_event

@receiver(post_save, sender=Event)
def event_completion_handler(sender, instance: Event, created, **kwargs):
    # """
    # Fire when an event is saved as completed & is a workshop.
    # Values saved in DB are lowercase (completed/workshop).
    # """
    try:
        status = (instance.status or "").lower()
        etype = (instance.event_type or "").lower()
    except Exception:
        return

    if status == "completed" and etype == "workshop":
        # Optional: don’t spam Celery if nothing to do
        # (we’ll let the task dedupe by get_or_create anyway)
        # Kick off async issuance
        send_certificates_for_workshop_event.delay(instance.id)