# from django.urls import path,include
# from .views import UserViewSet, UserRegistrationView,login_view, logout_view,UserProfileView, dashboard_stats,update_profile
# from rest_framework import routers
# from rest_framework.routers import DefaultRouter
# from .import views
# from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
# from django.conf import settings

# # class CustomPasswordResetView(PasswordResetView):
# #     def get_email_context(self):
# #         context = super().get_email_context()
# #         context['domain'] = settings.EMAIL_RESET_DOMAIN   # Your LAN IP
# #         context['protocol'] = 'http'  # since you’re not using https locally
# #         context['site_name'] = 'Eventify System'
# #         return context

# # class CustomPasswordResetView(PasswordResetView):
# #     def get_email_context(self):
# #         context = super().get_email_context()
# #         context['domain'] = getattr(settings, "SITE_DOMAIN", "127.0.0.1:8000")  # use your LAN IP
# #         context['protocol'] = 'http'  # since we are testing locally
# #         context['site_name'] = 'Eventify System'
# #         return context

# class CustomPasswordResetView(PasswordResetView):
#     # Use your LAN IP for password reset links
#     def get_email_options(self):
#         # """
#         # Overrides the email options to set domain_override.
#         # """
#         return {
#             "domain_override": getattr(settings, "SITE_DOMAIN", "127.0.0.1:8000"),
#             "use_https": False,  # True if you are using https
#             "extra_email_context": {
#                 "site_name": "Eventify System"
#             }
#         }





# router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

# urlpatterns=[
#     path('', include(router.urls)),
#     path('register/',UserRegistrationView.as_view(),name='register' ),
#     path('login/', login_view, name='login'),
#     path('logout/', logout_view, name='logout'),
#     path('profile/', UserProfileView.as_view(), name='profile'),
#     path('profile/update/',update_profile,name='profile-update'),
#     path('dashboard-stats/',dashboard_stats, name='dashboard_stats'),
#     path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
#     path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
#     path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
#     path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    
# ]


from django.urls import path, include
from .views import UserViewSet, UserRegistrationView, login_view, logout_view, UserProfileView, dashboard_stats, update_profile
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from . import views
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.conf import settings

class CustomPasswordResetView(PasswordResetView):
    def get_context_data(self, **kwargs):
        # Get the default context from the parent class
        context = super().get_context_data(**kwargs)
        
        # Override the protocol and domain to use your LAN IP
        protocol = 'http'
        domain = settings.SITE_DOMAIN  # This is '192.168.18.12:8000' from your settings
        
        # Update the context with your custom values
        context['protocol'] = protocol
        context['domain'] = domain
        
        return context

    # Optional: Keep this if you need to customize email options for other reasons
    def get_email_options(self):
        return {
            "domain_override": getattr(settings, "SITE_DOMAIN", "127.0.0.1:8000"),
            "use_https": False,
            "extra_email_context": {
                "site_name": "Eventify System"
            }
        }

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/update/', update_profile, name='profile-update'),
    path('dashboard-stats/', dashboard_stats, name='dashboard_stats'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]