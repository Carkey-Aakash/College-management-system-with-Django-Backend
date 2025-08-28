from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User, Profile, CollegeStudent
from import_export.admin import ImportExportModelAdmin

class CustomUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['role', 'username', 'phone_number', 'email', 'department']:
            if field in self.fields:
                self.fields[field].disabled = True  # Make fields readonly in admin

        if 'password' in self.fields:
            self.fields['password'].help_text = (
                "You have not accessed to this password field. "
            )
            # ✅ Hide reset password by making password field readonly (no reset link)
            self.fields['password'].widget = forms.PasswordInput(render_value=True, attrs={'readonly': True})

class CustomUserAdmin(BaseUserAdmin):
    model = User
    add_form = UserCreationForm
    form = CustomUserChangeForm  # ✅ Use custom change form

    list_display = ('username', 'email', 'role', 'gender', 'phone_number', 'is_active', 'department','organization')
    list_filter = ('role', 'is_staff', 'is_active', 'department')

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional Info", {
            "fields": ('role', 'phone_number', 'department', 'student_id', 'profile_picture', 'is_email_verified')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'phone_number', 'department', 'student_id'),
        }),
    )

    search_fields = ('username', 'email', 'phone_number')
    ordering = ('username',)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # ✅ Hide "Change Password" button in admin header
        extra_context = extra_context or {}
        extra_context['show_change_password'] = False
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'address', 'semester', 'bio', 'interests','class_name','year')
    search_fields = ('user__username',)

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

@admin.register(CollegeStudent)
class CollegeStudentAdmin(ImportExportModelAdmin):
    list_display = ('name', 'username', 'email', 'phone_number', 'department', 'role')
    search_fields = ('name', 'email', 'phone_number', 'username')

# ✅ Register User model properly
admin.site.register(User, CustomUserAdmin)
