from rest_framework import serializers
from .models import Certificate

class CertificateSerializer(serializers.ModelSerializer):
    event_title= serializers.CharField(source='event.title', read_only =True)
    student_name=serializers.CharField(source='student.username', read_only=True)
    certificate_url= serializers.SerializerMethodField()
    

    class Meta:
        model = Certificate
        fields = ['id', 'event', 'event_title', 'student', 'student_name', 'issued_at', 'certificate_url']

    def get_certificate_url(self, obj):
        request = self.context.get('request')
        if obj.certificate_file and request:
            return request.build_absolute_uri(obj.certificate_file.url)
        return None 