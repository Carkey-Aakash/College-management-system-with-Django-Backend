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
from django.core.exceptions import ValidationError
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

# ---------------- helpers ----------------
def normalize_nullable(value):
    # """Convert 'null'/'None'/'' to None."""
    if value in ("null", "None", "", None):
        return None
    return value

def choice_keys(choices):
    return set(k for k, _ in choices)

def validate_dept_org_choices(dept, org):
    # """Validate department/organization values (if provided) against model choices."""
    if dept:
        valid_depts = choice_keys(User.DEPARTMENTS)
        if dept not in valid_depts:
            return Response(
                {'error': f"Invalid department. Must be one of: {', '.join(sorted(valid_depts))}"},
                status=400
            )
    if org:
        valid_orgs = choice_keys(User.ORGANIZATIONS)
        if org not in valid_orgs:
            return Response(
                {'error': f"Invalid organization. Must be one of: {', '.join(sorted(valid_orgs))}"},
                status=400
            )
    return None

def validate_dept_org_for_role(user, dept, org):
    # """
    # Role-based rules:
    #   - Student: both allowed (optional)
    #   - Department: department required; organization must be empty
    #   - Organization: organization required; department must be empty
    #   - Campus-cheif/Admin: both optional
    # """
    if user.is_department():
        if not dept:
            return Response({'error': "For role 'Department', 'department' is required."}, status=400)
        return (dept, None)
    elif user.is_organization():
        if not org:
            return Response({'error': "For role 'Organization', 'organization' is required."}, status=400)
        return (None, org)
    else:
        # Student / Campus-cheif / Admin
        return (dept, org)

def validate_student_academics(user, class_name, year, semester):
    # """Students: class_name required; at least one of year/semester; validate choices."""
    if not user.is_student():
        return None

    if not class_name:
        return Response({'error': "For students, 'class_name' is required."}, status=400)

    valid_classes = choice_keys(Profile.CLASS_CHOICES)
    if class_name not in valid_classes:
        return Response(
            {'error': f"Invalid class_name. Must be one of: {', '.join(sorted(valid_classes))}"},
            status=400
        )

    if not (year or semester):
        return Response({'error': "For students, either 'semester' or 'year' must be provided."}, status=400)

    if year:
        valid_years = choice_keys(Profile.YEAR_CHOICES)
        if year not in valid_years:
            return Response(
                {'error': f"Invalid year. Must be one of: {', '.join(sorted(valid_years))}"},
                status=400
            )
    if semester:
        valid_sems = choice_keys(Profile.SEMESTER_CHOICES)
        if semester not in valid_sems:
            return Response(
                {'error': f"Invalid semester. Must be one of: {', '.join(sorted(valid_sems))}"},
                status=400
            )
    return None
# -------------- end helpers --------------


class UserProfileView(generics.GenericAPIView):
    # """
    # GET  /profile/         -> retrieve current user's profile
    # POST /profile/         -> create profile (once) with role-based rules
    # """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(self.get_serializer(request.user).data)

    def post(self, request):
        user = request.user
        data = request.data

        if hasattr(user, 'profile'):
            return Response({'error': 'Profile already exists. Use /profile/update/ to modify.'}, status=400)

        # required for everyone
        for f in ('first_name', 'last_name'):
            if not data.get(f):
                return Response({'error': f"Missing required field: {f}"}, status=400)

        # dept/org (normalize + validate choices + role rules)
        dept = normalize_nullable(data.get('department'))
        org  = normalize_nullable(data.get('organization'))

        err = validate_dept_org_choices(dept, org)
        if err:
            return err

        res = validate_dept_org_for_role(user, dept, org)
        if isinstance(res, Response):
            return res
        dept, org = res

        # academic fields
        class_name = normalize_nullable(data.get('class_name'))
        year       = normalize_nullable(data.get('year'))
        semester   = normalize_nullable(data.get('semester'))

        stud_err = validate_student_academics(user, class_name, year, semester)
        if stud_err:
            return stud_err

        # non-students must have academics empty
        if not user.is_student():
            class_name, year, semester = None, None, None

        # save user
        user.first_name   = data.get('first_name', user.first_name)
        user.last_name    = data.get('last_name', user.last_name)
        user.department   = dept
        user.organization = org
        user.save()

        # create profile
        interests_raw = data.get('interests', '')
        interests = ','.join(interests_raw) if isinstance(interests_raw, list) else interests_raw

        profile = Profile(
            user=user,
            class_name=class_name,
            year=year,
            semester=semester,
            bio=data.get('bio', ''),
            address=data.get('address', ''),
            interests=interests or ''
        )

        try:
            profile.full_clean()  # run model-level validation
        except ValidationError as e:
            return Response({'error': e.message_dict if hasattr(e, 'message_dict') else e.messages}, status=400)

        profile.save()

        return Response(
            {'message': 'Profile created successfully.', 'profile': self.get_serializer(user).data},
            status=201
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    # """
    # PUT/PATCH /profile/update/
    # Updates user + profile with the same role-based rules.
    # """
    user = request.user
    data = request.data

    allowed_fields = [
        'first_name', 'last_name', 'phone_number', 'email',
        'department', 'organization',
        'bio', 'semester', 'year', 'class_name', 'address', 'interests'
    ]
    invalid_fields = [f for f in data.keys() if f not in allowed_fields]
    if invalid_fields:
        return Response(
            {"message": f"Only allowed fields can be updated: {', '.join(allowed_fields)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # update user basics
    user.first_name   = data.get('first_name', user.first_name)
    user.last_name    = data.get('last_name', user.last_name)
    user.phone_number = data.get('phone_number', user.phone_number)
    user.email        = data.get('email', user.email)

    # dept/org normalize + choices + role rules
    dept = normalize_nullable(data.get('department', user.department))
    org  = normalize_nullable(data.get('organization', user.organization))

    err = validate_dept_org_choices(dept, org)
    if err:
        return err

    res = validate_dept_org_for_role(user, dept, org)
    if isinstance(res, Response):
        return res
    dept, org = res

    user.department   = dept
    user.organization = org
    user.save()

    # profile
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return Response({'error': 'Profile does not exist. Please create it first using POST /profile/.'}, status=404)

    class_name = normalize_nullable(data.get('class_name', profile.class_name))
    year       = normalize_nullable(data.get('year', profile.year))
    semester   = normalize_nullable(data.get('semester', profile.semester))

    stud_err = validate_student_academics(user, class_name, year, semester)
    if stud_err:
        return stud_err

    if not user.is_student():
        class_name, year, semester = None, None, None

    profile.class_name = class_name
    profile.year       = year
    profile.semester   = semester
    profile.bio        = data.get('bio', profile.bio)
    profile.address    = data.get('address', profile.address)

    interests = data.get('interests')
    if interests is not None:
        profile.interests = ','.join(interests) if isinstance(interests, list) else (interests or '')

    try:
        profile.full_clean()
    except ValidationError as e:
        return Response({'error': e.message_dict if hasattr(e, 'message_dict') else e.messages}, status=400)

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