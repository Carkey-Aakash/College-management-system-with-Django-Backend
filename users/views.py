from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from .models import User, Profile
from rest_framework.response import Response
from.serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer
from rest_framework import generics,status 
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets,permissions
from rest_framework.viewsets import ModelViewSet
from django.views.decorators.csrf import csrf_exempt
from events.models import Event
# Create your views here.

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes= [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer= self.get_serializer(data=request.data)
        if serializer.is_valid():
            user=serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user_id': user.id,
                'username': user.username,
                'role': user.role
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'message': 'Login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'department': user.department,
                'full_name': f"{user.first_name} {user.last_name}"
            }
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
    except:
        pass
    return Response({
        'message': 'Logout successful'
    }, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def post(self, request):
        user = request.user
        data = request.data

        if hasattr(user, 'profile'):
            return Response({'error': 'Profile already exists. Use /profile/update/ to modify.'}, status=400)

        required_fields = ['first_name', 'last_name']

        if user.is_student():
            required_fields.append('class_name')
            if not (data.get('semester') or data.get('year')):
                return Response(
                    {'error': 'For students, either semester or year must be provided along with class_name.'},
                    status=400
                )

        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response({'error': f'Missing required fields: {", ".join(missing_fields)}'}, status=400)

        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.save()

        # ===== Validate choices =====
        class_name = data.get('class_name')
        year = data.get('year')
        semester = data.get('semester')

        if user.is_student():
            valid_classes = [choice[0] for choice in Profile.CLASS_CHOICES]
            if class_name not in valid_classes:
                return Response({'error': f'Invalid class_name. Must be one of: {", ".join(valid_classes)}'}, status=400)

            valid_years = [choice[0] for choice in Profile.YEAR_CHOICES]
            valid_semesters = [choice[0] for choice in Profile.SEMESTER_CHOICES]

            if year and year not in valid_years:
                return Response({'error': f'Invalid year. Must be one of: {", ".join(valid_years)}'}, status=400)
            if semester and semester not in valid_semesters:
                return Response({'error': f'Invalid semester. Must be one of: {", ".join(valid_semesters)}'}, status=400)

            if not (year or semester):
                return Response({'error': 'For students, either semester or year must be provided along with class_name.'}, status=400)
        # ===== End validation =====

        profile = Profile.objects.create(
            user=user,
            class_name=class_name,
            year=year,
            semester=semester,
            bio=data.get('bio', ''),
            address=data.get('address', ''),
            interests=','.join(data.get('interests', [])) if isinstance(data.get('interests'), list) else data.get('interests', '')
        )

        serializer = self.get_serializer(user)
        return Response({'message': 'Profile created successfully.', 'profile': serializer.data}, status=201)


# @api_view(['PUT', 'PATCH'])
# @permission_classes([permissions.IsAuthenticated])
# def update_profile(request):
#     user = request.user
#     data = request.data

#     allowed_fields = [
#         'first_name', 'last_name', 'phone_number', 'email','department',
#         'bio', 'semester', 'year', 'class_name', 'address', 'interests'
#     ]

#     invalid_fields = [field for field in data.keys() if field not in allowed_fields]
#     if invalid_fields:
#         return Response({
#             "message": f"Only allowed fields can be updated: {', '.join(allowed_fields)}"
#         }, status=status.HTTP_400_BAD_REQUEST)

#     # Update User fields
#     user.first_name = data.get('first_name', user.first_name)
#     user.last_name = data.get('last_name', user.last_name)
#     user.phone_number = data.get('phone_number', user.phone_number)
#     user.email = data.get('email', user.email)
#     user.save()

#     try:
#         profile = user.profile
#     except Profile.DoesNotExist:
#         return Response({'error': 'Profile does not exist. Please create it first using POST /profile/.'}, status=404)

#     # ===== Validate class_name =====
#     if 'class_name' in data:
#         valid_classes = [choice[0] for choice in Profile.CLASS_CHOICES]
#         if data['class_name'] not in valid_classes:
#             return Response({'error': f'Invalid class_name. Must be one of: {", ".join(valid_classes)}'}, status=400)
#         profile.class_name = data['class_name']

#     # ===== Validate year =====
#     if 'year' in data:
#         valid_years = [choice[0] for choice in Profile.YEAR_CHOICES]
#         if data['year'] and data['year'] not in valid_years:
#             return Response({'error': f'Invalid year. Must be one of: {", ".join(valid_years)}'}, status=400)
#         profile.year = data['year']

#     # ===== Validate semester =====
#     if 'semester' in data:
#         valid_semesters = [choice[0] for choice in Profile.SEMESTER_CHOICES]
#         if data['semester'] and data['semester'] not in valid_semesters:
#             return Response({'error': f'Invalid semester. Must be one of: {", ".join(valid_semesters)}'}, status=400)
#         profile.semester = data['semester']

#     # Ensure at least one of year or semester for students
#     if user.is_student() and not (profile.year or profile.semester):
#         return Response({'error': 'For students, either semester or year must be provided along with class_name.'}, status=400)

#     # Update remaining fields
#     profile.bio = data.get('bio', profile.bio)
#     profile.address = data.get('address', profile.address)

#     interests = data.get('interests')
#     if interests:
#         profile.interests = ','.join(interests) if isinstance(interests, list) else interests

#     profile.save()

#     return Response({
#         'message': 'Profile updated successfully.',
#         'profile': UserProfileSerializer(user).data
#     }, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    user = request.user
    data = request.data

    allowed_fields = [
        'first_name', 'last_name', 'phone_number', 'email','department','organization',
        'bio', 'semester', 'year', 'class_name', 'address', 'interests'
    ]

    # Check for invalid fields
    invalid_fields = [field for field in data.keys() if field not in allowed_fields]
    if invalid_fields:
        return Response({
            "message": f"Only allowed fields can be updated: {', '.join(allowed_fields)}"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Update User fields
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.phone_number = data.get('phone_number', user.phone_number)
    user.email = data.get('email', user.email)
    user.save()

    # Update Profile
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return Response(
            {'error': 'Profile does not exist. Please create it first using POST /profile/.'},
            status=404
        )

    # Validate class_name
    class_name = data.get('class_name', profile.class_name)
    if user.is_student() and class_name not in dict(Profile.CLASS_CHOICES):
        return Response({'error': f'Invalid class_name. Must be one of: {", ".join(dict(Profile.CLASS_CHOICES).keys())}'}, status=400)
    profile.class_name = class_name

    # Validate year and semester
    year = data.get('year', profile.year)
    semester = data.get('semester', profile.semester)

    if year and year not in dict(Profile.YEAR_CHOICES):
        return Response({'error': f'Invalid year. Must be one of: {", ".join(dict(Profile.YEAR_CHOICES).keys())}'}, status=400)
    if semester and semester not in dict(Profile.SEMESTER_CHOICES):
        return Response({'error': f'Invalid semester. Must be one of: {", ".join(dict(Profile.SEMESTER_CHOICES).keys())}'}, status=400)

    profile.year = year
    profile.semester = semester

    # Ensure either year or semester is provided
    if user.is_student() and not (profile.year or profile.semester):
        return Response(
            {'error': 'For students, either semester or year must be provided along with class_name.'},
            status=400
        )

    # Update remaining fields
    profile.bio = data.get('bio', profile.bio)
    profile.address = data.get('address', profile.address)
    
    interests = data.get('interests')
    if interests:
        profile.interests = ','.join(interests) if isinstance(interests, list) else interests

    profile.save()

    return Response({
        'message': 'Profile updated successfully.',
        'profile': UserProfileSerializer(user).data
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    stats = {}

    if user.is_admin_user():
        stats = {
            'total_users': User.objects.count(),
            'total_students': User.objects.filter(role='Student').count(),
            'total_departments': User.objects.exclude(department__isnull=True).exclude(department='').values('department').distinct().count(),
            'total_organization': User.objects.exclude(organization__isnull=True).exclude(organization='').values('organization').distinct().count(),
            'total_events': Event.objects.count(),
            'approved_approvals': Event.objects.filter(status='approved').count(),
            'pending_approvals': Event.objects.filter(status='pending').count(),
            'cancelled_approvals': Event.objects.filter(status='cancelled').count(),
            'completed_events': Event.objects.filter(status='completed').count(),
        }

    elif user.is_student():
        from events.models import EventRegistration  # avoid circular import
        stats = {
            'registered_events': EventRegistration.objects.filter(student=user).count(),
            'upcoming_events': EventRegistration.objects.filter(student=user, event__status='approved').count(),
            'certificates_earned': 0,  # To be filled from certificates app later
        }

    elif user.is_department() or user.is_organization():
        stats = {
            'created_events': Event.objects.filter(organizer=user).count(),
            'pending_events': Event.objects.filter(organizer=user, status='pending').count(),
            'approved_events': Event.objects.filter(organizer=user, status='approved').count(),
            'cancelled_events': Event.objects.filter(organizer=user, status='cancelled').count(),
            'completed_events': Event.objects.filter(organizer=user, status='completed').count(),
        }

    elif user.is_chief():
        stats = {
            'pending_approvals': Event.objects.filter(status='pending').count(),
            'approved_events': Event.objects.filter(status='approved').count(),
            'rejected_events': Event.objects.filter(status='rejected').count(),
            'cancelled_events': Event.objects.filter(status='cancelled').count(),
            'completed_events': Event.objects.filter( status='completed').count(),
            'total_users': User.objects.count(),
            'total_students': User.objects.filter(role='Student').count(),
            'total_departments': User.objects.exclude(department__isnull=True).exclude(department='').values('department').distinct().count(),
            'total_organization': User.objects.exclude(organization__isnull=True).exclude(organization='').values('organization').distinct().count(),
            'total_events': Event.objects.count(),

        }

    else:
        stats = {'message': 'No dashboard available for your role.'}

    return Response(stats, status=status.HTTP_200_OK)


    


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes=[permissions.IsAdminUser]