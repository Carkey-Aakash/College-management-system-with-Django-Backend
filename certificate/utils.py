# import io
# from datetime import date
# from django.core.files.base import ContentFile
# from django.core.mail import EmailMessage
# from reportlab.lib.pagesizes import landscape, A4
# from reportlab.pdfgen import canvas
# from reportlab.lib.units import cm
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import Paragraph, Frame
# from notifications.utils import create_notification 


# def generate_certificate_pdf(student_name, event_title, event_date, organizer_name):
#     buffer = io.BytesIO()
#     width, height = landscape(A4)
#     c = canvas.Canvas(buffer, pagesize=(width, height))

#     # Background color
#     c.setFillColorRGB(0.95, 0.95, 0.95)
#     c.rect(0, 0, width, height, fill=1)

#     # Border
#     c.setStrokeColor(colors.HexColor('#003366'))
#     c.setLineWidth(4)
#     c.rect(1*cm, 1*cm, width - 2*cm, height - 2*cm, stroke=1, fill=0)

#     # Title
#     c.setFont("Helvetica-Bold", 36)
#     c.setFillColor(colors.HexColor('#003366'))
#     c.drawCentredString(width/2, height - 4*cm, "Certificate of Completion")

#     # Subtitle text
#     c.setFont("Helvetica", 16)
#     c.drawCentredString(width/2, height - 6*cm, "This is to certify that")

#     # Student name
#     c.setFont("Helvetica-Bold", 28)
#     c.setFillColor(colors.black)
#     c.drawCentredString(width/2, height - 9*cm, student_name)

#     # Description text
#     styles = getSampleStyleSheet()
#     style = styles["Normal"]
#     style.fontName = 'Helvetica'
#     style.fontSize = 18
#     style.leading = 22
#     style.alignment = 1  # center

#     text = f"has successfully completed the workshop <b>{event_title}</b> held on {event_date.strftime('%B %d, %Y')}."

#     para = Paragraph(text, style)
#     frame = Frame(3*cm, height - 12*cm, width - 6*cm, 3*cm, showBoundary=0)
#     frame.addFromList([para], c)

#     # Signature line
#     c.setFont("Helvetica", 14)
#     c.drawString(4*cm, 3*cm, f"{organizer_name}")
#     c.line(4*cm, 2.7*cm, 10*cm, 2.7*cm)

#     # Date issued
#     c.drawRightString(width - 4*cm, 3*cm, f"Issued on {date.today().strftime('%B %d, %Y')}")

#     c.showPage()
#     c.save()
#     pdf = buffer.getvalue()
#     buffer.close()
#     return pdf


# def create_and_send_certificate(event_registration):
    
#     # Generate PDF certificate, save it, email to student,
#     # and create a notification.
    
#     student = event_registration.student
#     event = event_registration.event

#     # Only for workshop and attended students
#     if event.event_type != 'workshop' or not event_registration.attended:
#         return None

#     from .models import Certificate
#     certificate, created = Certificate.objects.get_or_create(event=event, student=student)
#     if not created:
#         return certificate  # Already issued

#     organizer_name = event.organizer.username  # Or event.organizer.get_full_name()
#     pdf_content = generate_certificate_pdf(student.username, event.title, event.start_date, organizer_name)

#     filename = f"certificate_event_{event.id}_{student.username}.pdf"

#     certificate.certificate_file.save(filename, ContentFile(pdf_content))
#     certificate.save()

#     # Email sending
#     email_subject = f"Your Workshop Completion Certificate: {event.title}"
#     email_body = (
#         f"Dear {student.username},\n\n"
#         f"Congratulations on successfully completing the workshop '{event.title}'. "
#         f"Your certificate is attached.\n\nBest regards,\nEventify Team"
#     )

#     email = EmailMessage(
#         subject=email_subject,
#         body=email_body,
#         to=[student.email],
#     )
#     email.attach(filename, pdf_content, 'application/pdf')
#     email.send()

#     certificate.sent_via_email = True
#     certificate.save()

#     # Create notification via your notifications app
#     create_notification(
#         recipient=student,
#         title=f"Certificate Issued: {event.title}",
#         message=f"Your certificate for the workshop '{event.title}' has been issued and emailed to you.",
#         notification_type='event_completed',
#         event=event
#     )

#     return certificate


import io
from datetime import date
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Frame
from notifications.utils import create_notification
from reportlab.lib.units import cm, mm

NAVY = colors.HexColor("#0b2a3a")
GOLD = colors.HexColor("#f4c542")
MUTED = colors.HexColor("#6b7b8a")
BORDER = colors.HexColor("#e6ecf2")


def _draw_corner_stripes(c, x, y, w=110*mm, h=14*mm, angle=45):
    """
    Draws a diagonal striped bar similar to your reference image.
    Coordinates x,y are bottom-left of the bar's axis-aligned box before rotation.
    """
    from reportlab.lib.units import mm
    c.saveState()
    c.translate(x, y)
    c.rotate(angle)
    c.setFillColor(NAVY)
    # draw repeating stripes (8 mm navy, 8 mm white)
    stripe_w = 8 * mm
    total_w = w
    n = int(total_w // (2 * stripe_w)) + 2
    for i in range(n):
        # navy stripe
        c.rect(i * 2 * stripe_w, 0, stripe_w, h, stroke=0, fill=1)
    c.restoreState()


def generate_certificate_pdf(student_name, event_title, event_date, organizer_name):
    """
    Improved visual design; if student_name is falsy we draw two blank lines
    so the recipient can hand-write First/Last name.
    """
    buffer = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    # --- background ---
    c.setFillColorRGB(0.99, 0.99, 0.995)  # very light background
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # --- outer navy border ---
    c.setStrokeColor(NAVY)
    c.setLineWidth(6)
    c.rect(1.1 * cm, 1.1 * cm, width - 2.2 * cm, height - 2.2 * cm, stroke=1, fill=0)

    # --- decorative corner stripes (top-right and bottom-left) ---
    # dimensions in mm helper
    from reportlab.lib.units import mm
    _draw_corner_stripes(c, width - 120*mm, height - 24*mm, w=110*mm, h=14*mm, angle=0)  # top-right
    c.saveState()
    c.translate(10*mm, 10*mm)
    c.rotate(180)
    _draw_corner_stripes(c, 0, 0, w=110*mm, h=14*mm, angle=0)  # bottom-left mirrored
    c.restoreState()

    # --- badge (navy circle with gold ring + star) ---
    c.saveState()
    cx, cy, r = 55 * mm, height - 32 * mm, 14 * mm
    c.setFillColor(NAVY)
    c.circle(cx, cy, r, stroke=0, fill=1)
    c.setStrokeColor(GOLD)
    c.setLineWidth(4)
    c.circle(cx, cy, r + 4, stroke=1, fill=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(cx, cy - 6, "★")
    c.restoreState()

    # --- title ---
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(width / 2, height - 4.0 * cm, "CERTIFICATE")
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 5.1 * cm, "of completion")

    # --- lead text ---
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 7.0 * cm, "This certificate is proudly presented to")

    # --- name or blank lines ---
    name_y = height - 9.5 * cm
    c.setFillColor(colors.black)
    if student_name:  # print the name, styled like gold
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(width / 2, name_y, student_name.upper())
    else:
        # two long underlines for First / Last
        line_w = 70 * mm
        gap = 12 * mm
        cx = width / 2
        y = name_y - 2  # a tiny offset
        c.setStrokeColor(NAVY)
        c.setLineWidth(2)
        # first name line
        c.line(cx - gap/2 - line_w, y, cx - gap/2, y)
        # last name line
        c.line(cx + gap/2, y, cx + gap/2 + line_w, y)
        c.setFont("Helvetica", 10)
        c.setFillColor(MUTED)
        c.drawCentredString(cx - gap/2 - line_w/2, y - 12, "First Name")
        c.drawCentredString(cx + gap/2 + line_w/2, y - 12, "Last Name")

    # --- description paragraph (center) ---
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "Helvetica"
    style.fontSize = 13
    style.leading = 18
    style.textColor = MUTED
    style.alignment = 1  # center
    text = (
        f"This is to certify that the above named participant has successfully "
        f"completed the workshop <b>{event_title}</b> held on "
        f"{event_date.strftime('%B %d, %Y')}."
    )
    frame = Frame(3 * cm, height - 13.5 * cm, width - 6 * cm, 3.5 * cm, showBoundary=0)
    Paragraph(text, style).wrapOn(c, frame._width, frame._height)
    frame.addFromList([Paragraph(text, style)], c)

    # --- divider line ---
    c.setFillColor(BORDER)
    c.rect((width - 140*mm) / 2, height - 15.2*cm, 140*mm, 1.6, stroke=0, fill=1)

    # --- footer: date & signature ---
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)

    # left block (date)
    left_x = 5 * cm
    c.line(left_x, 3.2 * cm, left_x + 6 * cm, 3.2 * cm)
    c.setFillColor(MUTED)
    c.drawString(left_x, 2.4 * cm, f"Date: {date.today().strftime('%B %d, %Y')}")

    # right block (signature)
    right_x = width - (11 * cm)
    c.setFillColor(colors.black)
    c.line(right_x, 3.2 * cm, right_x + 6 * cm, 3.2 * cm)
    c.setFillColor(MUTED)
    c.drawString(right_x, 2.4 * cm, "Signature")

    # organizer name above left line (optional)
    if organizer_name:
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(left_x, 3.6 * cm, organizer_name)

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def create_and_send_certificate(event_registration):
    """
    Generate PDF certificate, save it, email to student, and create a notification.
    Only for workshop events and students who actually attended.
    """
    student = event_registration.student
    event = event_registration.event

    if event.event_type != 'workshop' or not event_registration.attended:
        return None

    from .models import Certificate
    certificate, created = Certificate.objects.get_or_create(event=event, student=student)
    if not created:
        return certificate  # already issued

    # build display name; leave blank if first/last missing
    first = (getattr(student, "first_name", "") or "").strip()
    last = (getattr(student, "last_name", "") or "").strip()
    display_name = f"{first} {last}".strip()
    if not display_name:
        display_name = None  # trigger blank lines

    organizer_name = None
    if getattr(event, "organizer", None):
        organizer_name = getattr(event.organizer, "get_full_name", lambda: "")() or getattr(event.organizer, "username", "")

    pdf_content = generate_certificate_pdf(
        display_name,
        event.title,
        getattr(event, "start_date", date.today()),
        organizer_name or ""
    )

    filename = f"certificate_event_{event.id}_{getattr(student, 'username', 'student')}.pdf"
    certificate.certificate_file.save(filename, ContentFile(pdf_content))
    certificate.save()

    # Email sending
    email_subject = f"Your Workshop Completion Certificate: {event.title}"
    email_body = (
        f"Dear {getattr(student, 'username', 'Student')},\n\n"
        f"Congratulations on successfully completing the workshop '{event.title}'. "
        f"Your certificate is attached.\n\n"
        f"If your name area is blank, please print and hand-write your First and Last name.\n\n"
        f"Best regards,\nEventify Team"
    )

    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        to=[getattr(student, "email", None)],
    )
    email.attach(filename, pdf_content, 'application/pdf')
    email.send()

    certificate.sent_via_email = True
    certificate.save()

    # Notification
    create_notification(
        recipient=student,
        title=f"Certificate Issued: {event.title}",
        message=f"Your certificate for the workshop '{event.title}' has been issued and emailed to you.",
        notification_type='event_completed',
        event=event
    )

    return certificate