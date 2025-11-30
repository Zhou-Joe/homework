from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json


def login_view(request):
    """登录页面"""
    if request.user.is_authenticated:
        return redirect('web:dashboard')
    return render(request, 'accounts/login.html')


def register_view(request):
    """注册页面"""
    if request.user.is_authenticated:
        return redirect('web:dashboard')
    return render(request, 'accounts/register.html')


@login_required
def dashboard_view(request):
    """首页/仪表板"""
    return render(request, 'web/dashboard.html')


@login_required
def profile_view(request):
    """个人资料页面"""
    return render(request, 'web/profile.html')


@login_required
def exercise_upload_view(request):
    """错题上传页面"""
    return render(request, 'web/exercise_upload.html')


@login_required
def practice_view(request):
    """强化训练页面"""
    return render(request, 'web/practice.html')


@login_required
def settings_view(request):
    """设置页面"""
    if request.user.user_type != 'admin':
        messages.error(request, '只有管理员可以访问设置页面')
        return redirect('dashboard')
    return render(request, 'web/settings.html')


def logout_view(request):
    """登出页面"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, '已成功登出')
    return redirect('web:login')


def api_root_view(request):
    """首页"""
    # 如果用户已登录，直接显示仪表板
    if request.user.is_authenticated:
        return render(request, 'web/dashboard.html')

    # 如果未登录，显示欢迎页面并重定向到登录
    return render(request, 'web/welcome.html')


@login_required
def answer_exercise_view(request, student_exercise_id):
    """答题页面"""
    return render(request, 'web/answer_exercise.html', {
        'student_exercise_id': student_exercise_id
    })


@login_required
def test_math_view(request):
    """数学公式测试页面"""
    return render(request, 'web/test_math.html')


@login_required
def practice_result_view(request):
    """练习结果页面"""
    return render(request, 'web/practice_result.html')


@login_required
def mistake_library_view(request):
    """错题宝库页面"""
    from exercises.models import StudentExercise, Exercise, Subject
    from django.db.models import Count, Q
    
    # 获取当前用户的所有错题（使用is_mistake字段而不是status）
    student_exercises = StudentExercise.objects.filter(
        student=request.user,
        is_mistake=True  # 使用is_mistake字段
    ).select_related('exercise', 'exercise__subject').order_by('-upload_time')
    
    # 调试信息
    print(f"用户 {request.user.username} 的错题查询:")
    print(f"  - 查询条件: student={request.user.id}, is_mistake=True")
    print(f"  - 找到 {student_exercises.count()} 道错题")
    for se in student_exercises:
        print(f"    ID: {se.id}, 习题: {se.exercise.title if se.exercise else '无'}, is_mistake: {se.is_mistake}")
    
    # 统计数据
    total_mistakes = student_exercises.count()
    mastered_count = StudentExercise.objects.filter(
        student=request.user,
        status='correct'
    ).count()
    pending_count = total_mistakes  # 错题数就是待攻克数
    
    # 计算掌握率
    total_exercises = StudentExercise.objects.filter(student=request.user).count()
    mastery_rate = 0
    if total_exercises > 0:
        mastery_rate = int((mastered_count / total_exercises) * 100)
    
    # 按学科分组统计
    subject_stats = student_exercises.values(
        'exercise__subject__name'
    ).annotate(
        mistake_count=Count('id')
    ).order_by('-mistake_count')
    
    # 为每个学科添加图标
    subject_icons = {
        '数学': 'calculator',
        '语文': 'book',
        '英语': 'language',
        '物理': 'atom',
        '化学': 'flask',
        '生物': 'dna',
        '历史': 'landmark',
        '地理': 'globe',
        '政治': 'balance-scale',
    }
    
    subjects = []
    for stat in subject_stats:
        subject_name = stat['exercise__subject__name'] or '其他'
        subjects.append({
            'name': subject_name,
            'mistake_count': stat['mistake_count'],
            'icon': subject_icons.get(subject_name, 'book')
        })
    
    # 如果没有错题，也提供所有学科选项
    if not subjects:
        for subject in Subject.objects.all():
            subjects.append({
                'name': subject.name,
                'mistake_count': 0,
                'icon': subject_icons.get(subject.name, 'book')
            })
    
    context = {
        'total_mistakes': total_mistakes,
        'mastered_count': mastered_count,
        'pending_count': pending_count,
        'mastery_rate': mastery_rate,
        'subjects': subjects,
    }
    
    return render(request, 'web/mistake_library.html', context)
