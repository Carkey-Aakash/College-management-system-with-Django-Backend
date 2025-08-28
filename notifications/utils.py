# from django.core.mail import send_mail
# from django.conf import settings
# from .models import Notification


# # def create_notification(recipient,title,message,notification_type='general',event=None):
# #     Notification.objects.create(
# #         recipient=recipient,
# #         title=title,
# #         message=message,
# #         notification_type=notification_type,
# #         event=event
# #     )

# def create_notification(recipient, title, message, notification_type, event=None):
#     print(f"[DEBUG] Creating notification for {recipient} with title: {title}")
#     notification = Notification.objects.create(
#         recipient=recipient,
#         title=title,
#         message=message,
#         notification_type=notification_type,
#         event=event
#     )
#     print(f"[DEBUG] Notification created with id: {notification.id}")
#     return notification

# def send_email_notification(recipient_email, subject, message):
#     send_mail(
#         subject,
#         message,
#         settings.DEFAULT_FROM_EMAIL,
#         [recipient_email],
#         fail_silently=False,
#     )




from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from .models import Notification

def create_notification(recipient, title, message, notification_type, event=None):
    print(f"[DEBUG] Creating notification for {recipient} with title: {title}")
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        event=event
    )
    print(f"[DEBUG] Notification created with id: {notification.id}")
    return notification

def send_email_notification(recipient_email, subject, message):
    # """
    # Keeps your signature the same, but improves the "from" behavior:
    # - uses DEFAULT_FROM_EMAIL if set
    # - else falls back to EMAIL_HOST_USER
    # """
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None) or "no-reply@example.com"

    # Plain text is fine. If you later want HTML, you can upgrade here safely.
    try:
        email = EmailMultiAlternatives(subject, message, from_email, [recipient_email])
        email.send(fail_silently=False)
    except Exception:
        # fall back to simple send_mail
        send_mail(
            subject,
            message,
            from_email,
            [recipient_email],
            fail_silently=False,
        )