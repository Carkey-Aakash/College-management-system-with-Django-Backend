from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
from django.core.exceptions import ValidationError

class User(AbstractUser):
    USER_ROLES=[
        ('Student', 'Student'),
        ('Department','Department'),
        ('Organization', 'Organization'),
        ('Campus-cheif', 'Campus-cheif'),
        ('Admin', 'Admin'),
    ]
    
    DEPARTMENTS=[
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

    role=models.CharField(max_length=20, choices=USER_ROLES,default='student')
    department=models.CharField(max_length=50, choices=DEPARTMENTS, null=True, blank=True)
    organization=models.CharField(max_length=50, choices=ORGANIZATIONS, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=False, blank=False, unique=True)
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.username} ({self.get_role_display()})" 
    
    def is_student(self):
        return self.role == 'Student'

    # def is_faculty(self):
    #     return self.role == 'Faculty'

    def is_organization(self):
        return self.role == 'Organization'
    
    def is_department(self):
        return self.role == 'Department'

    def is_chief(self):
        return self.role == 'Campus-cheif'

    def is_admin_user(self):
        return self.role == 'Admin'

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
    
    YEAR_CHOICES = [(str(i), f'{i} Year') for i in range(1, 5)]  # 1 to 4
    SEMESTER_CHOICES = [(str(i), f'{i} Semester') for i in range(1, 9)]  # 1 to 8
    
    class_name = models.CharField(max_length=50, choices=CLASS_CHOICES)
    year = models.CharField(max_length=2, choices=YEAR_CHOICES, blank=True, null=True)
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES, blank=True, null=True)

    address = models.TextField(blank=True)
    interests = models.TextField(blank=True, help_text="Comma-separated interests")

    def clean(self):
        if not self.semester and not self.year:
            raise ValidationError("Either semester or year must be provided.")

    def __str__(self):
        return f"{self.user.username}'s Profile"



