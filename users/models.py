from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    USER_ROLES = [
        ('Student', 'Student'),
        ('Department', 'Department'),
        ('Organization', 'Organization'),
        ('Campus-cheif', 'Campus-cheif'),
        ('Admin', 'Admin'),
    ]

    DEPARTMENTS = [
        ('physics', 'Department of Physics'),
        ('biology', 'Department of Biology'),
        ('chemistry', 'Department of Chemistry'),
        ('compulsory', 'Department of Compulsory Subjects'),
        ('food_tech', 'Department of Food Technology'),
        ('food_qc', 'Department of Food Quality Control'),
        ('microbiology', 'Department of Microbiology'),
        ('nutrition', 'Department of Nutrition and Dietetics'),
        ('geology', 'Department of Geology'),
        ('it', 'Department of Information Technology'),
    ]

    ORGANIZATIONS = [
        ('csit_union', 'Union of CSIT Students'),
        ('it_alliance', 'Information Technology Alliance'),
        ('physics_society', 'Physics Society'),
        ('biology_club', 'Biology Club'),
        ('chemistry_assoc', 'Chemistry Association'),
        ('food_tech_forum', 'Food Technology Forum'),
        ('nutrition_group', 'Nutrition and Dietetics Group'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    role = models.CharField(max_length=20, choices=USER_ROLES, default='Student')
    department = models.CharField(max_length=50, choices=DEPARTMENTS, null=True, blank=True)
    organization = models.CharField(max_length=50, choices=ORGANIZATIONS, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=False, blank=False, unique=True)
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -------- role helpers --------
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_student(self):
        return self.role == 'Student'

    def is_organization(self):
        return self.role == 'Organization'

    def is_department(self):
        return self.role == 'Department'

    def is_chief(self):
        return self.role == 'Campus-cheif'

    def is_admin_user(self):
        return self.role == 'Admin'

    # -------- optional: model-level validation for dept/org by role --------
    def clean(self):
        # """
        # Enforce high-level business rules at the model layer:
        #   - Student: may have department and/or organization (both optional)
        #   - Department: department required; organization must be empty
        #   - Organization: organization required; department must be empty
        #   - Campus-cheif/Admin: both optional
        # """
        # Normalize empties:
        dept = (self.department or None)
        org = (self.organization or None)

        if self.is_department():
            if not dept:
                raise ValidationError({'department': "For role 'Department', 'department' is required."})
            if org:
                raise ValidationError({'organization': "For role 'Department', 'organization' must be empty."})

        elif self.is_organization():
            if not org:
                raise ValidationError({'organization': "For role 'Organization', 'organization' is required."})
            if dept:
                raise ValidationError({'department': "For role 'Organization', 'department' must be empty."})

        # Student / Campus-cheif / Admin: no special constraint here.


class CollegeStudent(models.Model):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    department = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.department})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)

    CLASS_CHOICES = [
        ('BSc.CSIT', 'BSc.CSIT'),
        ('BBA', 'BBA'),
        ('BCA', 'BCA'),
        ('MSc.CSIT', 'MSc.CSIT'),
        ('BSc.IT', 'BSc.IT'),
        ('BSc.Micro', 'BSc.Micro'),
        ('BSc.BioTech', 'BSc.BioTech'),
        ('MSc.IT', 'MSc.IT'),
        ('MBA', 'MBA'),
        ('BPharma', 'BPharma'),
    ]

    YEAR_CHOICES = [(str(i), f'{i} Year') for i in range(1, 5)]      # 1..4
    SEMESTER_CHOICES = [(str(i), f'{i} Semester') for i in range(1, 9)]  # 1..8

    class_name = models.CharField(max_length=50, choices=CLASS_CHOICES, blank=True, null=True)
    year = models.CharField(max_length=2, choices=YEAR_CHOICES, blank=True, null=True)
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES, blank=True, null=True)

    address = models.TextField(blank=True)
    interests = models.TextField(blank=True, help_text="Comma-separated interests")

    def clean(self):
        # """
        # Only Students must provide academic fields:
        #   - class_name required
        #   - at least one of (year, semester) required
        # Non-students can keep these fields empty.
        # """
        # Ensure we have a user and can check role
        if getattr(self, 'user', None) and hasattr(self.user, 'is_student') and self.user.is_student():
            if not self.class_name:
                raise ValidationError({'class_name': "class_name is required for students."})

            if not self.year and not self.semester:
                # Use __all__ if you want a non-field error (as in your previous response)
                raise ValidationError({'__all__': "Either semester or year must be provided for students."})

    def __str__(self):
        return f"{self.user.username}'s Profile"
