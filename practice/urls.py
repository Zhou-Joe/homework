from django.urls import path
from . import views

app_name = 'practice'

urlpatterns = [
    path('sessions/', views.PracticeSessionListView.as_view(), name='session-list'),
    path('sessions/start/', views.start_practice_session, name='start-session'),
    path('sessions/end/', views.end_practice_session, name='end-session'),
    path('sessions/<int:session_id>/', views.get_practice_session, name='session-detail'),
    path('sessions/<int:session_id>/analysis-status/', views.get_analysis_status, name='analysis-status'),
    path('sessions/<int:session_id>/complete/', views.complete_practice_session, name='complete-session'),
    path('records/', views.get_practice_records, name='records-list'),
    path('knowledge-points/', views.get_session_knowledge_points, name='knowledge-points-list'),
    path('submit-answer/', views.submit_practice_answer, name='submit-answer'),
    path('submit-answer-async/', views.submit_practice_answer_async, name='submit-answer-async'),
    path('recommended/', views.get_recommended_exercises, name='recommended-exercises'),
    path('mastery/', views.KnowledgePointMasteryListView.as_view(), name='mastery-list'),
    path('vllm-config/', views.vllm_config, name='vllm-config'),
    path('vllm-config/test/', views.test_vllm_connection, name='test-vllm-connection'),
    path('debug/vllm-config/', views.debug_vllm_config, name='debug-vllm-config'),
]
