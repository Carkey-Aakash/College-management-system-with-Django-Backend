from django.urls import path
from .views import StudentCertificateListView

urlpatterns = [
    path('my-certificates/', StudentCertificateListView.as_view(), name='student-certificates'),
]