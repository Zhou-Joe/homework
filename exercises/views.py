import os
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import Subject, KnowledgePoint, ExamPoint, Exercise, StudentExercise
from .serializers import (
    SubjectSerializer,
    KnowledgePointSerializer,
    ExamPointSerializer,
    ExerciseSerializer,
    StudentExerciseSerializer,
    DashboardStatsSerializer
)
from practice.models import PracticeSession, KnowledgePointMastery
from .vllm_service import VLLMService


class SubjectListView(generics.ListAPIView):
    """学科列表视图"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]


class KnowledgePointListView(generics.ListAPIView):
    """知识点列表视图"""
    serializer_class = KnowledgePointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = KnowledgePoint.objects.all()
        subject_id = self.request.query_params.get('subject')
        grade_level = self.request.query_params.get('grade_level')

        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if grade_level:
            queryset = queryset.filter(grade_level=grade_level)

        return queryset


class ExamPointListView(generics.ListAPIView):
    """考点列表视图"""
    serializer_class = ExamPointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ExamPoint.objects.all().select_related('knowledge_point', 'subject')
        subject_id = self.request.query_params.get('subject')
        knowledge_point_id = self.request.query_params.get('knowledge_point')
        grade_level = self.request.query_params.get('grade_level')

        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if knowledge_point_id:
            queryset = queryset.filter(knowledge_point_id=knowledge_point_id)
        if grade_level:
            queryset = queryset.filter(grade_level=grade_level)

        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """首页统计数据"""
    user = request.user

    # 获取学生的统计数据
    total_exercises = StudentExercise.objects.filter(student=user).count()
    mistake_count = StudentExercise.objects.filter(student=user, is_mistake=True).count()

    # 获取练习会话统计
    practice_sessions = PracticeSession.objects.filter(student=user)
    practice_count = practice_sessions.count()

    # 计算平均正确率
    total_attempts = StudentExercise.objects.filter(student=user, status__in=['correct', 'wrong']).count()
    correct_attempts = StudentExercise.objects.filter(student=user, status='correct').count()
    accuracy_rate = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

    # 按学科统计
    subject_stats = []
    for subject in Subject.objects.all():
        subject_exercises = StudentExercise.objects.filter(
            student=user,
            exercise__subject=subject
        )
        subject_mistakes = subject_exercises.filter(is_mistake=True).count()
        subject_correct = subject_exercises.filter(status='correct').count()
        subject_total = subject_exercises.count()

        subject_stats.append({
            'subject_name': subject.name,
            'total_exercises': subject_total,
            'mistake_count': subject_mistakes,
            'accuracy_rate': (subject_correct / subject_total * 100) if subject_total > 0 else 0
        })

    # 最近错题
    recent_mistakes = StudentExercise.objects.filter(
        student=user,
        is_mistake=True
    ).order_by('-upload_time')[:5]

    recent_mistakes_data = []
    for mistake in recent_mistakes:
        recent_mistakes_data.append({
            'id': mistake.id,
            'exercise_title': mistake.exercise.title,
            'subject': mistake.exercise.subject.name,
            'upload_time': mistake.upload_time.strftime('%Y-%m-%d %H:%M'),
            'status': mistake.status
        })

    # 薄弱知识点（基于掌握程度）
    weak_knowledge_points = KnowledgePointMastery.objects.filter(
        student=user
    ).order_by('mastery_level')[:5]

    weak_kp_data = []
    for kp in weak_knowledge_points:
        weak_kp_data.append({
            'knowledge_point': kp.knowledge_point.name,
            'subject': kp.knowledge_point.subject.name,
            'mastery_level': kp.mastery_level,
            'total_attempts': kp.total_attempts,
            'accuracy_rate': kp.accuracy_rate
        })

    stats_data = {
        'total_exercises': total_exercises,
        'mistake_count': mistake_count,
        'practice_count': practice_count,
        'accuracy_rate': round(accuracy_rate, 2),
        'subject_stats': subject_stats,
        'recent_mistakes': recent_mistakes_data,
        'weak_knowledge_points': weak_kp_data
    }

    serializer = DashboardStatsSerializer(stats_data)
    return Response(serializer.data)


class StudentExerciseListView(generics.ListCreateAPIView):
    """学生错题列表视图"""
    serializer_class = StudentExerciseSerializer
    permission_classes = [IsAuthenticated]
    # 设置分页大小为20条
    pagination_class = None  # 禁用分页，返回所有结果

    def get_queryset(self):
        # 获取用户可访问的题目
        accessible_exercises = Exercise.get_accessible_exercises_for_user(self.request.user)

        # 查询学生自己的错题记录，但限制为可访问的题目
        queryset = StudentExercise.objects.filter(
            student=self.request.user,
            exercise__in=accessible_exercises
        )

        subject_id = self.request.query_params.get('subject')
        is_mistake = self.request.query_params.get('is_mistake')

        if subject_id:
            queryset = queryset.filter(exercise__subject_id=subject_id)
        if is_mistake is not None:
            queryset = queryset.filter(is_mistake=is_mistake.lower() == 'true')

        return queryset.order_by('-upload_time')

    def perform_create(self, serializer):
        """创建学生习题记录时关联到当前用户"""
        serializer.save(student=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_mistakes(request):
    """获取学生错题"""
    try:
        # 获取用户可访问的题目
        accessible_exercises = Exercise.get_accessible_exercises_for_user(request.user)

        # 查询学生自己的错题记录，但限制为可访问的题目
        student_exercises = StudentExercise.objects.filter(
            student=request.user,
            is_mistake=True,
            exercise__in=accessible_exercises
        ).order_by('-upload_time')

        serializer = StudentExerciseSerializer(student_exercises, many=True)
        return Response(serializer.data)
    except Exception as e:
        import traceback
        print(f"获取学生错题失败: {str(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        return Response(
            {'error': f'获取错题列表失败: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ExerciseListView(generics.ListAPIView):
    """题目列表视图 - 根据用户权限过滤"""
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # 禁用分页，返回所有结果

    def get_queryset(self):
        # 获取用户可访问的题目
        return Exercise.get_accessible_exercises_for_user(self.request.user)

    def get_serializer_context(self):
        """添加request到序列化器上下文"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_exercise(request):
    """上传习题图片进行分析"""
    try:
        # 获取上传的图片
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'error': '请上传图片文件'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证文件类型
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        file_ext = os.path.splitext(image_file.name)[1].lower()
        if file_ext not in allowed_extensions:
            return Response({'error': '请上传图片文件（支持jpg、jpeg、png、gif、bmp、webp格式）'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证文件大小（10MB）
        if image_file.size > 10 * 1024 * 1024:
            return Response({'error': '图片文件大小不能超过10MB'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取用户年级
        student_grade_level = request.user.grade_level

        # 调用VL LLM服务分析习题
        vllm_service = VLLMService()
        analysis_result = vllm_service.analyze_exercise(image_file, student_grade_level)

        # 检查AI是否识别为有效题目
        if not analysis_result.get('is_valid_question', False):
            # 不是有效题目，不保存到数据库，返回拒绝原因
            return Response({
                'message': '图片未识别为有效的学生错题',
                'is_valid_question': False,
                'rejection_reason': analysis_result.get('rejection_reason', '图片内容不符合学习题目的要求'),
                'analysis': analysis_result
            }, status=status.HTTP_400_BAD_REQUEST)

        # 是有效题目，创建或获取习题记录
        exercise = _create_or_update_exercise(analysis_result, request.user, image_file)

        # 创建学生错题记录
        student_exercise, created = StudentExercise.objects.get_or_create(
            student=request.user,
            exercise=exercise,
            defaults={
                'status': 'wrong' if analysis_result.get('student_solution') else 'not_attempted',
                'is_mistake': True,
                'llm_analysis': analysis_result
            }
        )

        # 更新习题统计
        exercise.total_attempts += 1
        if not created:
            exercise.wrong_attempts += 1
        exercise.save()

        return Response({
            'message': '错题上传分析成功',
            'is_valid_question': True,
            'exercise_id': exercise.id,
            'student_exercise_id': student_exercise.id,
            'analysis': analysis_result
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_student_answer(request):
    """分析学生答案"""
    try:
        exercise_id = request.data.get('exercise_id')
        student_exercise_id = request.data.get('student_exercise_id')
        answer_image = request.FILES.get('answer_image')
        response_time = request.data.get('response_time', 0)

        if not answer_image:
            return Response({'error': '缺少答案图片'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证文件类型
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        file_ext = os.path.splitext(answer_image.name)[1].lower()
        if file_ext not in allowed_extensions:
            return Response({'error': '请上传图片文件（支持jpg、jpeg、png、gif、bmp、webp格式）'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证文件大小（10MB）
        if answer_image.size > 10 * 1024 * 1024:
            return Response({'error': '图片文件大小不能超过10MB'}, status=status.HTTP_400_BAD_REQUEST)

        if not exercise_id and not student_exercise_id:
            return Response({'error': '缺少习题ID或学生习题ID'}, status=status.HTTP_400_BAD_REQUEST)

        # 如果提供了student_exercise_id，优先使用它
        if student_exercise_id:
            try:
                student_exercise = StudentExercise.objects.get(
                    id=student_exercise_id,
                    student=request.user
                )
                exercise = student_exercise.exercise
            except StudentExercise.DoesNotExist:
                return Response({'error': '学生习题记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 使用exercise_id查找学生习题记录
            try:
                exercise = Exercise.objects.get(id=exercise_id)
                student_exercise = StudentExercise.objects.get(
                    student=request.user,
                    exercise=exercise
                )
            except (Exercise.DoesNotExist, StudentExercise.DoesNotExist):
                return Response({'error': '习题或学生记录不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 调用VL LLM服务分析答案
        vllm_service = VLLMService()
        
        # 准备题目图片（如果存在）
        question_image_file = None
        if exercise.question_image:
            try:
                # 题目图片是ImageFieldFile对象，需要获取路径
                import os
                from django.conf import settings
                question_image_path = os.path.join(settings.MEDIA_ROOT, str(exercise.question_image))
                if os.path.exists(question_image_path):
                    question_image_file = open(question_image_path, 'rb')
                    print(f"题目图片已加载: {question_image_path}")
                else:
                    print(f"题目图片文件不存在: {question_image_path}")
            except Exception as img_error:
                print(f"加载题目图片失败: {str(img_error)}")
        
        try:
            answer_analysis = vllm_service.analyze_student_answer(
                exercise.question_text,
                exercise.answer_text,
                exercise.answer_steps,
                answer_image,
                question_image_file  # 传递题目图片
            )
        finally:
            # 清理题目图片文件句柄
            if question_image_file:
                question_image_file.close()

        student_exercise.student_answer_image = answer_image
        student_exercise.student_answer_text = answer_analysis.get('student_answer', '')
        student_exercise.status = 'correct' if answer_analysis.get('is_correct') else 'wrong'
        student_exercise.is_mistake = not answer_analysis.get('is_correct')
        student_exercise.llm_analysis = answer_analysis
        student_exercise.save()

        # 更新习题统计
        exercise.total_attempts += 1
        if answer_analysis.get('is_correct'):
            exercise.correct_attempts += 1
        else:
            exercise.wrong_attempts += 1
        exercise.save()

        # 更新知识点掌握程度
        _update_knowledge_point_mastery(request.user, exercise, answer_analysis.get('is_correct', False))

        return Response({
            'message': '答案分析完成',
            'is_correct': answer_analysis.get('is_correct'),
            'analysis': answer_analysis
        })

    except Exercise.DoesNotExist:
        return Response({'error': '习题不存在'}, status=status.HTTP_404_NOT_FOUND)
    except StudentExercise.DoesNotExist:
        return Response({'error': '学生习题记录不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_text_answer(request):
    """分析学生文字答案"""
    try:
        exercise_id = request.data.get('exercise_id')
        student_exercise_id = request.data.get('student_exercise_id')
        answer_text = request.data.get('answer_text', '').strip()
        response_time = request.data.get('response_time', 0)

        if not answer_text:
            return Response({'error': '缺少文字答案'}, status=status.HTTP_400_BAD_REQUEST)

        if not exercise_id and not student_exercise_id:
            return Response({'error': '缺少习题ID或学生习题ID'}, status=status.HTTP_400_BAD_REQUEST)

        # 如果提供了student_exercise_id，优先使用它
        if student_exercise_id:
            try:
                student_exercise = StudentExercise.objects.get(
                    id=student_exercise_id,
                    student=request.user
                )
                exercise = student_exercise.exercise
            except StudentExercise.DoesNotExist:
                return Response({'error': '学生习题记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 使用exercise_id查找学生习题记录
            try:
                exercise = Exercise.objects.get(id=exercise_id)
                student_exercise = StudentExercise.objects.get(
                    student=request.user,
                    exercise=exercise
                )
            except (Exercise.DoesNotExist, StudentExercise.DoesNotExist):
                return Response({'error': '习题或学生记录不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 调用VL LLM服务分析文字答案
        vllm_service = VLLMService()
        answer_analysis = vllm_service.analyze_student_text_answer(
            exercise.question_text,
            exercise.answer_text,
            exercise.answer_steps,
            answer_text
        )

        # 保存文字答案
        student_exercise.student_answer_text = answer_text
        student_exercise.status = 'correct' if answer_analysis.get('is_correct') else 'wrong'
        student_exercise.is_mistake = not answer_analysis.get('is_correct')
        student_exercise.llm_analysis = answer_analysis
        student_exercise.save()

        # 更新习题统计
        exercise.total_attempts += 1
        if answer_analysis.get('is_correct'):
            exercise.correct_attempts += 1
        else:
            exercise.wrong_attempts += 1
        exercise.save()

        # 更新知识点掌握程度
        _update_knowledge_point_mastery(request.user, exercise, answer_analysis.get('is_correct', False))

        return Response({
            'message': '文字答案分析完成',
            'is_correct': answer_analysis.get('is_correct'),
            'student_answer': answer_text,
            'analysis': answer_analysis
        })

    except Exercise.DoesNotExist:
        return Response({'error': '习题不存在'}, status=status.HTTP_404_NOT_FOUND)
    except StudentExercise.DoesNotExist:
        return Response({'error': '学生习题记录不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _create_or_update_exercise(analysis_result, user, image_file):
    """创建或更新习题记录"""
    try:
        subject = Subject.objects.get(id=analysis_result['subject_id'])

        # 检查是否已存在相同的题目
        existing_exercise = Exercise.objects.filter(
            title=analysis_result.get('title', ''),
            subject=subject,
            grade_level=user.grade_level
        ).first()

        if existing_exercise:
            # 更新现有习题的图片
            existing_exercise.question_image = image_file
            existing_exercise.save()
            return existing_exercise

        # 创建新习题
        exercise = Exercise.objects.create(
            title=analysis_result.get('title', ''),
            question_text=analysis_result.get('question_text', ''),
            question_image=image_file,
            answer_text=analysis_result.get('correct_answer', ''),
            answer_steps=analysis_result.get('answer_steps', ''),
            subject=subject,
            grade_level=user.grade_level,  # 关联用户当前年级
            difficulty=analysis_result.get('difficulty', 'medium'),
            visibility='private',  # 用户上传的错题默认为私人可见
            created_by=user
        )

        # 关联知识点
        knowledge_point_ids = analysis_result.get('knowledge_point_ids', [])
        if knowledge_point_ids:
            exercise.knowledge_points.add(*knowledge_point_ids)

        # 关联考点
        exam_point_ids = analysis_result.get('exam_point_ids', [])
        if exam_point_ids:
            exercise.exam_points.add(*exam_point_ids)

        return exercise

    except Subject.DoesNotExist:
        raise Exception('学科不存在')
    except Exception as e:
        raise Exception(f'习题创建失败: {str(e)}')


def _update_knowledge_point_mastery(student, exercise, is_correct):
    """更新知识点掌握程度"""
    from practice.models import KnowledgePointMastery

    for kp in exercise.knowledge_points.all():
        mastery, created = KnowledgePointMastery.objects.get_or_create(
            student=student,
            knowledge_point=kp,
            defaults={
                'mastery_level': 100 if is_correct else 0,
                'total_attempts': 1,
                'correct_attempts': 1 if is_correct else 0
            }
        )

        if not created:
            mastery.total_attempts += 1
            if is_correct:
                mastery.correct_attempts += 1

            # 重新计算掌握程度 (使用指数移动平均)
            if mastery.total_attempts > 0:
                accuracy_rate = mastery.correct_attempts / mastery.total_attempts
                alpha = 0.3  # 平滑因子
                mastery.mastery_level = mastery.mastery_level * (1 - alpha) + accuracy_rate * 100 * alpha

            mastery.save()


class StudentExerciseDetailView(generics.RetrieveAPIView):
    """学生错题记录详情视图"""
    queryset = StudentExercise.objects.all()
    serializer_class = StudentExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudentExercise.objects.filter(student=self.request.user)


class ExerciseDetailView(generics.RetrieveAPIView):
    """习题详情视图 - 检查权限"""
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只返回用户可访问的题目
        return Exercise.get_accessible_exercises_for_user(self.request.user)

    def get_serializer_context(self):
        """添加request到序列化器上下文"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_subject_stats(request):
    """学科统计信息"""
    user = request.user
    
    subject_stats = []
    for subject in Subject.objects.all():
        subject_exercises = StudentExercise.objects.filter(
            student=user,
            exercise__subject=subject
        )
        
        total_questions = subject_exercises.count()
        correct_answers = subject_exercises.filter(status='correct').count()
        mistake_count = subject_exercises.filter(is_mistake=True).count()
        
        accuracy_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        subject_stats.append({
            'subject_name': subject.name,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'mistake_count': mistake_count,
            'accuracy_rate': round(accuracy_rate, 1)
        })
    
    return Response({
        'results': subject_stats
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_weak_knowledge_points(request):
    """薄弱知识点"""
    user = request.user
    
    # 获取掌握度低于60%的知识点
    weak_points = KnowledgePointMastery.objects.filter(
        student=user,
        mastery_level__lt=60
    ).order_by('mastery_level')[:10]
    
    knowledge_points = []
    for mastery in weak_points:
        attempts = StudentExercise.objects.filter(
            student=user,
            exercise__knowledge_points=mastery.knowledge_point
        )
        
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(status='correct').count()
        
        knowledge_points.append({
            'id': mastery.knowledge_point.id,
            'name': mastery.knowledge_point.name,
            'subject_name': mastery.knowledge_point.subject.name,
            'mastery_level': round(mastery.mastery_level, 1),
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts
        })
    
    return Response({
        'results': knowledge_points
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_recent_mistakes(request):
    """最近错题"""
    user = request.user
    
    recent_mistakes = StudentExercise.objects.filter(
        student=user,
        is_mistake=True
    ).order_by('-upload_time')[:10]
    
    mistakes = []
    for mistake in recent_mistakes:
        exercise = mistake.exercise
        
        # 难度映射
        difficulty_map = {
            'easy': { 'text': '简单', 'color': 'success' },
            'medium': { 'text': '中等', 'color': 'warning' },
            'hard': { 'text': '困难', 'color': 'danger' }
        }
        difficulty_info = difficulty_map.get(exercise.difficulty, { 'text': '未知', 'color': 'default' })
        
        mistakes.append({
            'id': exercise.id,
            'title': exercise.title or '错题',
            'difficulty': exercise.difficulty,
            'difficulty_text': difficulty_info['text'],
            'subject_name': exercise.subject.name if exercise.subject else '未知',
            'created_at': mistake.upload_time.strftime('%Y-%m-%d %H:%M')
        })
    
    return Response({
        'results': mistakes
    })
