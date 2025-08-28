from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Profile
from django.contrib.auth.password_validation import validate_password

class UserRegistrationSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password1 = serializers.CharField(write_only=True, required=True)
    user_id=serializers.ReadOnlyField(source='id')
    class Meta:
        model =User
        fields=['user_id','username','email','password','password1','department','organization','gender','student_id','phone_number','profile_picture']


    def validate(self,attrs):
        if attrs['password'] != attrs['password1']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
            
    def create(self, validated_data):
            # Remove password1 as it's not a model field
        validated_data.pop('password1')
        password = validated_data.pop('password')
        # Force role to be 'Student'
        validated_data['role'] = 'Student'  #  Force it here to role student
            # Create user instance without password first
        user = User(**validated_data)
        user.set_password(password)  # This handles password hashing
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    username=serializers.CharField()
    password= serializers.CharField(write_only=True)

    def validate(self, attrs):
        username=attrs.get('username')
        password= attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'department','organization', 'profile']
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'bio': profile.bio,
                'class_name': profile.class_name,
                'year': profile.year,
                'semester': profile.semester,
                'address': profile.address,
                'interests': profile.interests.split(',') if profile.interests else []
            }
        except Profile.DoesNotExist:
            return None
        
        


            


