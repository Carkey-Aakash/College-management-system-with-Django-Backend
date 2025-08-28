# from django.urls import path 
# from .views import EventListCreateView,EventDetailView,approve_reject_event, register_for_event, cancel_registration,  submit_feedback, my_events, EventConflictListView,event_statistics,pending_events_list,cancelled_events_list, completed_events_list,attendance_verify

# urlpatterns = [
#     #Event CRUD operation
#     path('', EventListCreateView.as_view(), name='event-list-create'),
#      # ✅ NEW: clean detail endpoint (/api/v1/events/<id>/)
#     path('<int:pk>/', EventDetailView.as_view(), name='event-detail'),
#     path('<int:pk>/manage/', EventDetailView.as_view(),name='event-manage'),
#     #Event Pending 
#     path('pending/', pending_events_list, name='pending-event-list'),
#     #Event Cancelled 
#     path('cancelled/', cancelled_events_list, name='cancelled-event-list'),
#     #Event Completed
#     path('completed/', completed_events_list, name='completed-event-list'),

#     # Event approval
#     path('<int:event_id>/approve/', approve_reject_event, name='approve-event'),
#     # Event registration
#     path('<int:event_id>/register/', register_for_event, name='register-event'),
#     path('<int:event_id>/cancel-registration/', cancel_registration, name='cancel-registration'),
#     # Attendance and feedback
#     path('attendance/verify/', attendance_verify, name='attendance-verify'),
#     # path('<int:event_id>/mark-attendance/', mark_attendance, name='mark-attendance'),
#     path('<int:event_id>/feedback/', submit_feedback, name='submit-feedback'),
#      # Analytics and reports
#     path('<int:event_id>/statistics/', event_statistics, name='event-statistics'),
    
#     # User-specific events
#     path('my-events/', my_events, name='my-events'),
    
#     # Event conflicts
#     path('conflicts/', EventConflictListView.as_view(), name='event-conflicts'),



    
# ]



from django.urls import path
from .views import (
    EventListCreateView,
    EventDetailView,            # kept for /manage/
    event_detail_or_login,      # wrapper
    approve_reject_event,
    register_for_event,
    cancel_registration,
    submit_feedback,
    my_events,
    EventConflictListView,
    event_statistics,
    pending_events_list,
    cancelled_events_list,
    completed_events_list,
    attendance_verify,
)

urlpatterns = [
    path('', EventListCreateView.as_view(), name='event-list-create'),

    # Clean detail: login form if not authenticated, JSON if authenticated
    path('<int:pk>/', event_detail_or_login, name='event-detail'),

    # DRF view directly (you can keep this admin/organizer-only path if you like)
    path('<int:pk>/manage/', EventDetailView.as_view(), name='event-manage'),

    path('pending/', pending_events_list, name='pending-event-list'),
    path('cancelled/', cancelled_events_list, name='cancelled-event-list'),
    path('completed/', completed_events_list, name='completed-event-list'),

    path('<int:event_id>/approve/', approve_reject_event, name='approve-event'),
    path('<int:event_id>/register/', register_for_event, name='register-event'),
    path('<int:event_id>/cancel-registration/', cancel_registration, name='cancel-registration'),

    path('attendance/verify/', attendance_verify, name='attendance-verify'),
    path('<int:event_id>/feedback/', submit_feedback, name='submit-feedback'),

    path('<int:event_id>/statistics/', event_statistics, name='event-statistics'),
    path('my-events/', my_events, name='my-events'),

    path('conflicts/', EventConflictListView.as_view(), name='event-conflicts'),
]
