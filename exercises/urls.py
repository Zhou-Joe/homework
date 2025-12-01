from django.urls import path
from . import views

app_name = 'exercises'

urlpatterns = [
    path('subjects/', views.SubjectListView.as_view(), name='subject-list'),
    path('knowledge-points/', views.KnowledgePointListView.as_view(), name='knowledge-point-list'),
    path('exam-points/', views.ExamPointListView.as_view(), name='exam-point-list'),
    path('exercises/', views.ExerciseListView.as_view(), name='exercise-list'),
    path('student-exercises/', views.StudentExerciseListView.as_view(), name='student-exercise-list'),
    path('student-exercises/<int:pk>/', views.StudentExerciseDetailView.as_view(), name='student-exercise-detail'),
    path('exercises/<int:pk>/', views.ExerciseDetailView.as_view(), name='exercise-detail'),
    path('mistakes/', views.student_mistakes, name='student-mistakes'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('dashboard/subject-stats/', views.dashboard_subject_stats, name='dashboard-subject-stats'),
    path('dashboard/weak-knowledge-points/', views.dashboard_weak_knowledge_points, name='dashboard-weak-knowledge-points'),
    path('dashboard/recent-mistakes/', views.dashboard_recent_mistakes, name='dashboard-recent-mistakes'),
    path('upload/', views.upload_exercise, name='upload-exercise'),
    path('analyze-answer/', views.analyze_student_answer, name='analyze-answer'),
    path('analyze-text-answer/', views.analyze_text_answer, name='analyze-text-answer'),
]
