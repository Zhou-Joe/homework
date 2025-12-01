from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from exercises.models import Exercise, Subject, KnowledgePoint, ExamPoint
from exercises.vllm_service import VLLMService


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


@login_required
def batch_upload_view(request):
    """批量上传题目页面"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, '只有管理员可以访问批量上传页面')
        return redirect('web:dashboard')
    
    # 获取年级选项
    grade_choices = [
        ('小学1年级', '小学1年级'), ('小学2年级', '小学2年级'), ('小学3年级', '小学3年级'),
        ('小学4年级', '小学4年级'), ('小学5年级', '小学5年级'), ('小学6年级', '小学6年级'),
        ('初一', '初一'), ('初二', '初二'), ('初三', '初三'),
        ('高一', '高一'), ('高二', '高二'), ('高三', '高三'),
    ]
    
    return render(request, 'web/batch_upload.html', {
        'grade_choices': grade_choices
    })


@login_required
def batch_upload_advanced_view(request):
    """高级批量上传题目页面"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, '只有管理员可以访问高级批量上传页面')
        return redirect('web:dashboard')
    
    # 获取年级选项
    grade_choices = [
        ('小学1年级', '小学1年级'), ('小学2年级', '小学2年级'), ('小学3年级', '小学3年级'),
        ('小学4年级', '小学4年级'), ('小学5年级', '小学5年级'), ('小学6年级', '小学6年级'),
        ('初一', '初一'), ('初二', '初二'), ('初三', '初三'),
        ('高一', '高一'), ('高二', '高二'), ('高三', '高三'),
    ]
    
    return render(request, 'web/batch_upload_advanced.html', {
        'grade_choices': grade_choices
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def analyze_batch_exercise(request):
    """分析批量上传的题目"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': '无权限访问'}, status=403)

    try:
        # 获取上传的图片和年级
        image_file = request.FILES.get('image')
        grade_level = request.POST.get('grade_level')

        if not image_file or not grade_level:
            return JsonResponse({'error': '缺少图片或年级信息'}, status=400)
        
        # 调用VLM服务分析题目
        vllm_service = VLLMService()
        analysis_result = vllm_service.analyze_exercise(image_file, grade_level)
        
        # 返回分析结果
        return JsonResponse({
            'success': True,
            'analysis': analysis_result
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'分析失败: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_batch_exercise(request):
    """保存批量上传的题目到数据库"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': '无权限访问'}, status=403)
    
    try:
        data = json.loads(request.body)
        analysis_data = data.get('analysis')
        image_data = data.get('image_data')
        
        if not analysis_data:
            return JsonResponse({'error': '缺少分析数据'}, status=400)
        
        # 验证必要字段
        if not analysis_data.get('question_text'):
            return JsonResponse({'error': '题目内容不能为空'}, status=400)
        
        if not analysis_data.get('subject'):
            return JsonResponse({'error': '学科不能为空'}, status=400)
        
        # 创建题目对象
        exercise = Exercise()
        
        # 保存图片
        if image_data:
            # 解码base64图片数据
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            image_file = ContentFile(base64.b64decode(imgstr), name=f'exercise_{timezone.now().strftime("%Y%m%d%H%M%S")}.{ext}')
            exercise.question_image = image_file
        
        # 设置题目基本信息
        exercise.title = analysis_data.get('title', '批量上传题目')
        exercise.question_text = analysis_data.get('question_text', '')
        exercise.answer_text = ''  # 暂时留空，后续解析
        exercise.answer_steps = ''  # 暂时留空，后续解析
        exercise.grade_level = analysis_data.get('grade_level', '初一')
        exercise.difficulty = analysis_data.get('difficulty', 'medium')
        exercise.visibility = 'public'  # 设置为公共题目
        exercise.created_by = request.user
        exercise.source = 'batch_upload'  # 标记来源为批量上传
        exercise.is_solved = False  # 标记为未解决
        
        # 获取学科
        subject_name = analysis_data.get('subject', '数学')
        subject, created = Subject.objects.get_or_create(name=subject_name)
        exercise.subject = subject

        # 保存题目
        exercise.save()
        
        # 处理知识点
        knowledge_points = analysis_data.get('knowledge_points', [])
        for kp_name in knowledge_points:
            kp, created = KnowledgePoint.objects.get_or_create(
                name=kp_name,
                subject=subject,
                grade_level=exercise.grade_level,
                defaults={'description': f'{kp_name}知识点'}
            )
            exercise.knowledge_points.add(kp)
        
        # 处理考点
        exam_points = analysis_data.get('exam_points', [])
        for ep_name in exam_points:
            # 找到对应的知识点（如果有）
            if exercise.knowledge_points.exists():
                knowledge_point = exercise.knowledge_points.first()
            else:
                # 创建默认知识点
                knowledge_point, created = KnowledgePoint.objects.get_or_create(
                    name='基础知识点',
                    subject=subject,
                    grade_level=exercise.grade_level,
                    defaults={'description': '基础知识点'}
                )
            
            ep, created = ExamPoint.objects.get_or_create(
                name=ep_name,
                knowledge_point=knowledge_point,
                subject=subject,
                grade_level=exercise.grade_level,
                defaults={'description': f'{ep_name}考点'}
            )
            exercise.exam_points.add(ep)
        
        return JsonResponse({
            'success': True,
            'exercise_id': exercise.id,
            'message': '题目保存成功',
            'title': exercise.title,
            'subject': exercise.subject.name,
            'grade_level': exercise.grade_level
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'保存失败: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def analyze_batch_exercise_advanced(request):
    """高级批量分析题目（支持多图片同时分析）"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': '无权限访问'}, status=403)

    try:
        # 获取上传的图片和年级
        image_files = request.FILES.getlist('images')  # 支持多文件上传
        grade_level = request.POST.get('grade_level')

        if not image_files or not grade_level:
            return JsonResponse({'error': '缺少图片或年级信息'}, status=400)

        if len(image_files) > 10:  # 限制一次最多分析10张图片
            return JsonResponse({'error': '一次最多分析10张图片'}, status=400)

        # 调用VLM服务批量分析题目（使用简化模式）
        vllm_service = VLLMService()
        batch_result = vllm_service.analyze_exercise_batch_simple(image_files, grade_level)

        # 返回批量分析结果，使用与前端一致的格式
        return JsonResponse({
            'success': True,
            'total_files': batch_result['total_files'],
            'successful_analyses': batch_result['successful_analyses'],
            'failed_analyses': batch_result['failed_analyses'],
            'results': batch_result['results']
        })

    except Exception as e:
        return JsonResponse({
            'error': f'批量分析失败: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_batch_exercise_advanced(request):
    """高级批量保存题目"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': '无权限访问'}, status=403)

    try:
        data = json.loads(request.body)
        batch_analysis_results = data.get('batch_analysis', {})

        if not batch_analysis_results:
            return JsonResponse({'error': '缺少分析结果'}, status=400)

        saved_exercises = []
        failed_exercises = []

        # 遍历所有分析结果
        for result in batch_analysis_results.get('results', []):
            try:
                # 只处理有效题目
                if not result.get('is_valid_question', False):
                    continue

                # 获取题目列表（新的简化格式）
                questions = result.get('questions', [])
                if not questions:
                    continue

                # 为每道题目创建数据库记录
                for i, question_data in enumerate(questions):
                    # 获取学科
                    subject_name = question_data.get('subject', '数学')
                    subject, created = Subject.objects.get_or_create(name=subject_name)

                    # 创建题目
                    exercise = Exercise.objects.create(
                        title=question_data.get('title', f'批量上传题目-{len(saved_exercises) + 1}'),
                        question_text=question_data.get('question_text', ''),
                        subject=subject,
                        grade_level=question_data.get('grade_level', '初一'),  # 使用用户选择的年级
                        difficulty=question_data.get('difficulty', 'medium'),

                        # 需要AI进一步处理的字段
                        answer_text=question_data.get('answer_text', '未处理'),
                        answer_steps=question_data.get('answer_steps', '未处理'),

                        # 权限和来源设置
                        created_by=request.user,
                        visibility=question_data.get('visibility', 'public'),  # 设置为公共权限
                        source=question_data.get('source', 'batch_upload'),  # 标记为批量上传
                        is_solved=question_data.get('is_solved', False),  # 标记为未解决

                        # 统计字段初始值
                        total_attempts=question_data.get('total_attempts', 0),
                        correct_attempts=question_data.get('correct_attempts', 0),
                        wrong_attempts=question_data.get('wrong_attempts', 0),
                    )

                    # 处理知识点关联（如果有的话）
                    knowledge_points = question_data.get('knowledge_points', [])
                    for kp_name in knowledge_points:
                        if kp_name:  # 确保不是空字符串
                            kp, created = KnowledgePoint.objects.get_or_create(
                                name=kp_name,
                                subject=exercise.subject,
                                grade_level=exercise.grade_level,
                                defaults={'description': f'{kp_name}相关知识点'}
                            )
                            exercise.knowledge_points.add(kp)

                    # 处理考点关联（如果有的话）
                    exam_points = question_data.get('exam_points', [])
                    for ep_name in exam_points:
                        if ep_name:  # 确保不是空字符串
                            # 考点需要关联知识点，这里暂时关联第一个知识点或创建默认知识点
                            if exercise.knowledge_points.exists():
                                knowledge_point = exercise.knowledge_points.first()
                            else:
                                knowledge_point, created = KnowledgePoint.objects.get_or_create(
                                    name='基础知识点',
                                    subject=exercise.subject,
                                    grade_level=exercise.grade_level,
                                    defaults={'description': '基础知识点'}
                                )
                                exercise.knowledge_points.add(knowledge_point)

                            ep, created = ExamPoint.objects.get_or_create(
                                name=ep_name,
                                knowledge_point=knowledge_point,
                                subject=exercise.subject,
                                grade_level=exercise.grade_level,
                                defaults={'description': f'{ep_name}相关考点'}
                            )
                            exercise.exam_points.add(ep)

                    saved_exercises.append({
                        'exercise_id': exercise.id,
                        'title': exercise.title,
                        'subject': exercise.subject.name,
                        'grade_level': exercise.grade_level,
                        'file_name': result.get('file_name', ''),
                        'question_index': i + 1
                    })

            except Exception as e:
                failed_exercises.append({
                    'file_name': result.get('file_name', ''),
                    'error': str(e)
                })

        return JsonResponse({
            'success': True,
            'saved_count': len(saved_exercises),
            'failed_count': len(failed_exercises),
            'saved_exercises': saved_exercises,
            'failed_exercises': failed_exercises,
            'message': f'成功保存 {len(saved_exercises)} 道题目'
        })

    except Exception as e:
        return JsonResponse({
            'error': f'批量保存失败: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def solve_exercise_batch_advanced(request):
    """高级批量解答题目"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': '无权限访问'}, status=403)

    try:
        data = json.loads(request.body)
        exercises = data.get('exercises', [])  # 使用前端传递的完整题目数据

        if not exercises:
            return JsonResponse({'error': '未选择题目'}, status=400)

        # 准备批量解答数据
        exercises_data = []
        for exercise_data in exercises:
            exercises_data.append({
                'exercise_id': exercise_data['id'],
                'question_text': exercise_data.get('question_text', ''),
                'subject': exercise_data.get('subject', '数学'),
                'grade_level': exercise_data.get('grade_level', '初一')
            })

        # 调用VLM服务批量解答
        vllm_service = VLLMService()
        batch_solution = vllm_service.solve_exercise_batch(exercises_data)

        # 更新数据库中的题目信息
        solved_count = 0
        failed_count = 0

        for result in batch_solution['results']:
            if result['status'] == 'success':
                try:
                    exercise = Exercise.objects.get(id=result['exercise_id'])
                    solution = result.get('solution', {})

                    # 更新题目标题、答案和解题步骤
                    exercise.title = solution.get('title', exercise.title)  # 更新AI生成的题目标题
                    exercise.answer_text = solution.get('correct_answer', '')
                    exercise.answer_steps = solution.get('answer_steps', '')
                    exercise.is_solved = True
                    exercise.save()
                    solved_count += 1

                    print(f"✅ 题目更新成功: ID={exercise.id}, 新标题={exercise.title}")

                except Exercise.DoesNotExist:
                    print(f"❌ 题目不存在: ID={result.get('exercise_id')}")
                    failed_count += 1
                except Exception as e:
                    print(f"❌ 题目更新失败: ID={result.get('exercise_id')}, 错误={str(e)}")
                    failed_count += 1
            else:
                print(f"❌ 题目解答失败: {result}")
                failed_count += 1
        
        return JsonResponse({
            'success': True,
            'successful_solutions': solved_count,
            'failed_solutions': failed_count,
            'total_exercises': len(exercises),
            'message': f'成功解答 {solved_count} 道题目，失败 {failed_count} 道'
        })

    except Exception as e:
        return JsonResponse({
            'error': f'批量解答失败: {str(e)}'
        }, status=500)


@login_required
def get_unsolved_exercises(request):
    """获取未解决的题目列表"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': '无权限访问'}, status=403)

    try:
        # 获取所有答案为空或未处理的题目（包括批量上传和其他来源的题目）
        unsolved_exercises = Exercise.objects.filter(
            answer_text__in=['', '未处理', None],
            visibility='public'
        ).select_related('subject').order_by('-created_at')

        exercises_data = []
        for exercise in unsolved_exercises:
            exercises_data.append({
                'id': exercise.id,
                'title': exercise.title,
                'question_text': exercise.question_text[:100] + '...' if len(exercise.question_text) > 100 else exercise.question_text,
                'question_image': exercise.question_image.url if exercise.question_image else None,
                'subject_name': exercise.subject.name,  # 统一字段名，与前端匹配
                'subject': exercise.subject.name,
                'grade_level': exercise.grade_level,
                'difficulty': exercise.difficulty,
                'created_at': exercise.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'source': exercise.source,
                'is_solved': exercise.is_solved
            })

        print(f"DEBUG: 获取到 {len(exercises_data)} 个未解决题目")  # 调试信息
        for ex in exercises_data[:3]:  # 打印前3个题目用于调试
            print(f"  - {ex['title']} (来源: {ex.get('source', 'unknown')})")

        return JsonResponse({
            'success': True,
            'exercises': exercises_data,
            'total_count': len(exercises_data)
        })

    except Exception as e:
        print(f"ERROR: 获取未解决题目失败: {str(e)}")  # 调试信息
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'获取未解决题目失败: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def solve_exercise_batch(request):
    """批量解决题目"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': '无权限访问'}, status=403)
    
    try:
        data = json.loads(request.body)
        exercise_ids = data.get('exercise_ids', [])
        
        if not exercise_ids:
            return JsonResponse({'error': '未选择题目'}, status=400)
        
        # 获取需要解决的题目
        exercises = Exercise.objects.filter(id__in=exercise_ids, answer_text='')
        
        vllm_service = VLLMService()
        results = []
        
        for exercise in exercises:
            try:
                # 构建解题提示词
                prompt = f"""
请解答以下题目：

题目：{exercise.question_text}
学科：{exercise.subject.name}
年级：{exercise.grade_level}

要求：
1. 提供详细的解题步骤
2. 给出最终答案
3. 如果是数学物理等理科题，请使用LaTeX格式表示公式
4. 解题步骤要清晰易懂，适合{exercise.grade_level}学生理解

请按照以下JSON格式返回：
{{
    "answer_steps": "详细的解题步骤（使用LaTeX格式）",
    "correct_answer": "最终答案（使用LaTeX格式）",
    "difficulty_analysis": "题目难度分析"
}}
"""
                
                # 调用VLM服务获取解答
                response = vllm_service._call_vllm_text_api(prompt)
                
                # 解析响应
                import json
                result = json.loads(response['choices'][0]['message']['content'])
                
                # 更新题目信息
                exercise.answer_steps = result.get('answer_steps', '')
                exercise.answer_text = result.get('correct_answer', '')
                exercise.save()
                
                results.append({
                    'exercise_id': exercise.id,
                    'success': True,
                    'title': exercise.title
                })
                
            except Exception as e:
                results.append({
                    'exercise_id': exercise.id,
                    'success': False,
                    'error': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'批量解决失败: {str(e)}'
        }, status=500)

def test_batch_page(request):
    """测试批量上传功能的简化页面"""
    return render(request, 'web/test_batch.html')

def batch_upload_fixed(request):
    """简化版批量上传题目"""
    if request.method == 'GET':
        return render(request, 'web/batch_upload_fixed.html')

    # 处理POST请求的逻辑可以复用现有的analyze_batch_exercise函数
    return analyze_batch_exercise(request)

def test_vlm_api(request):
    """测试VLM API - 直接分析base64图片"""
    if request.method == 'POST':
        try:
            import base64
            from django.http import JsonResponse
            from . import VLLMService

            data = json.loads(request.body)
            grade_level = data.get('grade_level', '小学三年级')
            image_data = data.get('image_base64', '')

            print(f"=== 测试VLM API ===")
            print(f"年级: {grade_level}")
            print(f"图片数据长度: {len(image_data)}")

            if not image_data:
                return JsonResponse({'error': '缺少图片数据'}, status=400)

            # 调用VLM服务
            vllm_service = VLLMService()

            # 创建模拟图片文件对象
            class MockFile:
                def __init__(self, content):
                    self.content = content

                def read(self):
                    return self.content

            mock_file = MockFile('test.jpg', image_data)

            print(f"开始分析图片...")
            analysis_result = vllm_service.analyze_exercise(mock_file, grade_level)

            return JsonResponse({
                'success': True,
                'analysis': analysis_result
            })

        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'success': False
            })

    # GET请求返回测试页面
    return render(request, 'web/test_vlm.html')
