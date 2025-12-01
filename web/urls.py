from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    # 认证相关
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # 主要页面
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('upload/', views.exercise_upload_view, name='exercise_upload'),
    path('practice/', views.practice_view, name='practice_home'),
    path('answer/<int:student_exercise_id>/', views.answer_exercise_view, name='answer_exercise'),
    path('settings/', views.settings_view, name='settings'),
    path('mistakes/', views.mistake_library_view, name='mistake_library'),

    # 批量上传功能
    path('batch-upload/', views.batch_upload_view, name='batch_upload'),
    path('batch-upload-advanced/', views.batch_upload_advanced_view, name='batch_upload_advanced'),
    path('api/analyze-batch-exercise/', views.analyze_batch_exercise, name='analyze_batch_exercise'),
    path('api/save-batch-exercise/', views.save_batch_exercise, name='save_batch_exercise'),
    path('api/get-unsolved-exercises/', views.get_unsolved_exercises, name='get_unsolved_exercises'),
    path('api/solve-exercise-batch/', views.solve_exercise_batch, name='solve_exercise_batch'),
    
    # 高级批量上传功能（新函数）
    path('api/analyze-batch-exercise-advanced/', views.analyze_batch_exercise_advanced, name='analyze_batch_exercise_advanced'),
    path('api/save-batch-exercise-advanced/', views.save_batch_exercise_advanced, name='save_batch_exercise_advanced'),
    path('api/solve-exercise-batch-advanced/', views.solve_exercise_batch_advanced, name='solve_exercise_batch_advanced'),

    # 测试页面
    path('test-math/', views.test_math_view, name='test_math'),
    path('test-batch/', views.test_batch_page, name='test_batch'),
    path('batch-upload-fixed/', views.batch_upload_fixed, name='batch_upload_fixed'),
    path('api/test-vlm/', views.test_vlm_api, name='test_vlm_api'),

    # 练习结果页面
    path('practice-result/', views.practice_result_view, name='practice_result'),

    # API根页面
    path('', views.api_root_view, name='api_root'),
]
