from django.shortcuts import render
from rest_framework import generics, permissions
from.serializers import CertificateSerializer
from .models import Certificate
class StudentCertificateListView(generics.ListAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Certificate.objects.filter(student=self.request.user)
