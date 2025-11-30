from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, F, Avg, Count
from django.utils import timezone
from datetime import timedelta
import random
import requests
import os
from .models import PracticeSession, PracticeRecord, KnowledgePointMastery, VLLMConfig, SessionKnowledgePointScore
from exercises.models import Exercise, StudentExercise
from .serializers import (
    PracticeSessionSerializer,
    PracticeRecordSerializer,
    KnowledgePointMasterySerializer,
    VLLMConfigSerializer,
    SessionKnowledgePointScoreSerializer
)
from exercises.serializers import ExerciseSerializer
from exercises.vllm_service import VLLMService


class PracticeSessionListView(generics.ListAPIView):
    """练习会话列表视图"""
    serializer_class = PracticeSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PracticeSession.objects.filter(student=self.request.user).order_by('-start_time')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_practice_session(request):
    """开始练习会话"""
    try:
        # 获取练习参数
        subject_id = request.data.get('subject_id')
        knowledge_point_ids = request.data.get('knowledge_point_ids', [])
        difficulty = request.data.get('difficulty')
        question_count = request.data.get('question_count', 10)

        # 创建练习会话
        session = PracticeSession.objects.create(
            student=request.user,
            total_questions=question_count
        )

        # 生成推荐题目
        recommended_exercises = _get_recommended_exercises(
            request.user,
            subject_id,
            knowledge_point_ids,
            difficulty,
            question_count
        )

        # 初始化知识点得分记录
        from practice.models import SessionKnowledgePointScore
        from exercises.models import KnowledgePoint

        # 收集推荐题目涉及的所有知识点
        involved_knowledge_points = set()
        for item in recommended_exercises:
            exercise = item.get('exercise', {})
            if 'knowledge_points' in exercise:
                for kp in exercise['knowledge_points']:
                    involved_knowledge_points.add(kp['id'])

        # 如果没有指定知识点，获取该学科的所有知识点
        if not involved_knowledge_points and subject_id:
            all_kps = KnowledgePoint.objects.filter(subject_id=subject_id)
            involved_knowledge_points.update(all_kps.values_list('id', flat=True))

        # 为每个知识点创建得分记录（初始化为0）
        for kp_id in involved_knowledge_points:
            try:
                kp = KnowledgePoint.objects.get(id=kp_id)
                SessionKnowledgePointScore.objects.get_or_create(
                    session=session,
                    knowledge_point=kp,
                    defaults={
                        'total_questions': 0,
                        'correct_answers': 0,
                        'score': 0.0,
                        'weight': 1.0  # 默认权重
                    }
                )
            except KnowledgePoint.DoesNotExist:
                continue

        return Response({
            'session_id': session.id,
            'recommended_exercises': recommended_exercises
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_practice_answer(request):
    """提交练习答案"""
    try:
        session_id = request.data.get('session_id')
        exercise_id = request.data.get('exercise_id')
        answer_image = request.FILES.get('answer_image')
        answer_text = request.data.get('answer_text', '').strip()
        response_time = request.data.get('response_time', 0)

        if not all([session_id, exercise_id]):
            return Response({'error': '缺少必要参数：session_id和exercise_id'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查至少有一种答案形式
        if not answer_image and not answer_text:
            return Response({'error': '请提供图片或文字答案'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取习题和会话
        exercise = Exercise.objects.get(id=exercise_id)
        session = PracticeSession.objects.get(id=session_id, student=request.user)

        # 使用VL LLM分析答案
        vllm_service = VLLMService()

        # 根据答案类型选择分析方法
        if answer_image:
            answer_analysis = vllm_service.analyze_student_answer(
                exercise.question_text,
                exercise.answer_text,
                exercise.answer_steps,
                answer_image
            )
        else:
            # 纯文字答案分析
            answer_analysis = vllm_service.analyze_student_text_answer(
                exercise.question_text,
                exercise.answer_text,
                exercise.answer_steps,
                answer_text
            )

        # 计算本题得分（基于难度）
        difficulty_points = {
            'easy': 10,
            'medium': 20,
            'hard': 30
        }
        base_points = difficulty_points.get(exercise.difficulty, 20)
        earned_points = base_points if answer_analysis.get('is_correct') else 0

        # 获取当前题目序号
        question_number = PracticeRecord.objects.filter(session=session).count() + 1

        # 创建练习记录
        practice_record = PracticeRecord.objects.create(
            session=session,
            exercise=exercise,
            student_answer_image=answer_image,
            student_answer_text=answer_text if answer_text else answer_analysis.get('student_answer', ''),
            status='correct' if answer_analysis.get('is_correct') else 'wrong',
            response_time=response_time,
            llm_analysis=answer_analysis,
            question_number=question_number,
            points_earned=earned_points
        )

        # 更新知识点得分
        _update_session_knowledge_points(session, exercise, answer_analysis.get('is_correct', False), earned_points)

        # 重新计算会话统计
        _update_session_stats(session)

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
            'message': '答案提交成功',
            'is_correct': answer_analysis.get('is_correct'),
            'analysis': answer_analysis,
            'session_score': session.score
        })

    except (Exercise.DoesNotExist, PracticeSession.DoesNotExist):
        return Response({'error': '习题或会话不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_practice_answer_async(request):
    """异步提交练习答案（后台处理AI分析）"""
    try:
        session_id = request.data.get('session_id')
        exercise_id = request.data.get('exercise_id')
        answer_image = request.FILES.get('answer_image')
        answer_text = request.data.get('answer_text', '').strip()
        response_time = request.data.get('response_time', 0)

        if not all([session_id, exercise_id]):
            return Response({'error': '缺少必要参数：session_id和exercise_id'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查至少有一种答案形式
        if not answer_image and not answer_text:
            return Response({'error': '请提供图片或文字答案'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取习题和会话
        exercise = Exercise.objects.get(id=exercise_id)
        session = PracticeSession.objects.get(id=session_id, student=request.user)

        # 获取当前题目序号
        question_number = PracticeRecord.objects.filter(session=session).count() + 1

        # 保存图片内容到内存，避免在线程中访问request对象
        image_content = None
        image_name = None
        if answer_image:
            answer_image.seek(0)
            image_content = answer_image.read()
            image_name = os.path.basename(answer_image.name)
        
        # 保存图片文件到磁盘，避免I/O问题
        saved_image_path = None
        if image_content:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_content)
                saved_image_path = temp_file.name
        
        # 创建练习记录（暂不进行AI分析）
        practice_record = PracticeRecord.objects.create(
            session=session,
            exercise=exercise,
            student_answer_image=answer_image,
            student_answer_text=answer_text,
            status='pending',  # 标记为待分析
            response_time=response_time,
            llm_analysis=None,  # 暂不保存分析结果
            question_number=question_number,
            points_earned=0  # 暂不给分
        )

        # 后台异步处理AI分析
        import threading
        
        # 保存必要的变量到线程本地
        thread_data = {
            'exercise_id': exercise_id,
            'session_id': session.id,
            'practice_record_id': practice_record.id,
            'saved_image_path': saved_image_path,
            'answer_text': answer_text,
            'user_id': request.user.id
        }
        
        def process_analysis():
            import django
            from django.conf import settings
            from django.db import connections
            
            # 确保Django环境正确初始化
            if not settings.configured:
                django.setup()
            
            try:
                # 关闭所有现有连接，确保获取新连接
                connections.close_all()
                
                # 重新获取对象，因为线程中无法访问外部变量
                from exercises.models import Exercise
                from practice.models import PracticeRecord, PracticeSession
                from accounts.models import User
                
                print(f"开始异步分析，线程ID: {threading.get_ident()}")
                print(f"分析数据: exercise_id={thread_data['exercise_id']}, record_id={thread_data['practice_record_id']}")
                
                # 重新获取数据库对象
                updated_exercise = Exercise.objects.get(id=thread_data['exercise_id'])
                updated_session = PracticeSession.objects.get(id=thread_data['session_id'])
                updated_record = PracticeRecord.objects.get(id=thread_data['practice_record_id'])
                user = User.objects.get(id=thread_data['user_id'])
                
                # 在线程中重新创建VLLMService实例
                vllm_service = VLLMService()
                print(f"VLLM服务初始化成功: API URL={vllm_service.api_url}, Model={vllm_service.model_name}")
                
                print(f"题目ID: {updated_exercise.id}, 是否有图片: {bool(thread_data['saved_image_path'])}")
                print(f"题目内容预览: {updated_exercise.question_text[:50] if updated_exercise.question_text else 'N/A'}...")
                
                # 根据答案类型选择分析方法
                if thread_data['saved_image_path']:
                    # 使用保存的临时文件
                    try:
                        with open(thread_data['saved_image_path'], 'rb') as f:
                            from django.core.files.base import File
                            answer_file = File(f)
                            
                            # 准备题目图片（如果存在）
                            question_image_file = None
                            if updated_exercise.question_image:
                                try:
                                    # 题目图片是相对路径，需要构建完整路径
                                    import os
                                    from django.conf import settings
                                    question_image_path = os.path.join(settings.MEDIA_ROOT, updated_exercise.question_image.lstrip('/'))
                                    if os.path.exists(question_image_path):
                                        question_image_file = open(question_image_path, 'rb')
                                        print(f"题目图片已加载: {question_image_path}")
                                    else:
                                        print(f"题目图片文件不存在: {question_image_path}")
                                except Exception as img_error:
                                    print(f"加载题目图片失败: {str(img_error)}")
                            
                            try:
                                answer_analysis = vllm_service.analyze_student_answer(
                                    updated_exercise.question_text,
                                    updated_exercise.answer_text,
                                    updated_exercise.answer_steps,
                                    answer_file,
                                    question_image_file  # 传递题目图片
                                )
                                print(f"图片分析完成: {answer_analysis.get('is_correct', 'unknown')}")
                            finally:
                                # 清理题目图片文件句柄
                                if question_image_file:
                                    question_image_file.close()
                    except Exception as img_error:
                        print(f"图片分析失败: {str(img_error)}")
                        import traceback
                        traceback.print_exc()
                        
                        # 如果图片分析失败，尝试文字分析
                        if thread_data['answer_text']:
                            try:
                                answer_analysis = vllm_service.analyze_student_text_answer(
                                    updated_exercise.question_text,
                                    updated_exercise.answer_text,
                                    updated_exercise.answer_steps,
                                    thread_data['answer_text']
                                )
                                print(f"切换到文字分析完成: {answer_analysis.get('is_correct', 'unknown')}")
                            except Exception as text_error:
                                print(f"文字分析也失败: {str(text_error)}")
                                answer_analysis = {
                                    'is_correct': False,
                                    'student_answer': '图片和文字分析都失败',
                                    'error_analysis': f'图片分析失败: {str(img_error)}；文字分析失败: {str(text_error)}',
                                    'feedback': '请确保答案清晰可读，建议重新上传图片或输入文字答案',
                                    'solution_quality': '无法评估'
                                }
                        else:
                            # 只有图片且分析失败，返回错误信息但不要抛出异常
                            answer_analysis = {
                                'is_correct': False,
                                'student_answer': '图片分析失败',
                                'error_analysis': f'图片分析失败: {str(img_error)}',
                                'feedback': '请确保图片清晰可读，建议重新拍摄或上传清晰的答题图片',
                                'solution_quality': '无法评估'
                            }
                else:
                    answer_analysis = vllm_service.analyze_student_text_answer(
                        updated_exercise.question_text,
                        updated_exercise.answer_text,
                        updated_exercise.answer_steps,
                        thread_data['answer_text']
                    )
                    print(f"文字分析完成: {answer_analysis.get('is_correct', 'unknown')}")

                # 计算本题得分
                difficulty_points = {
                    'easy': 10,
                    'medium': 20,
                    'hard': 30
                }
                base_points = difficulty_points.get(updated_exercise.difficulty, 20)
                earned_points = base_points if answer_analysis.get('is_correct') else 0

                # 确保数据库连接有效
                connections.close_all()
                
                # 更新记录
                updated_record.llm_analysis = answer_analysis
                updated_record.status = 'correct' if answer_analysis.get('is_correct') else 'wrong'
                updated_record.points_earned = earned_points
                updated_record.save()
                print(f"记录更新完成: 状态={updated_record.status}, 得分={earned_points}")

                # 更新知识点得分
                _update_session_knowledge_points(updated_session, updated_exercise, answer_analysis.get('is_correct', False), earned_points)

                # 重新计算会话统计
                _update_session_stats(updated_session)

                # 更新习题统计
                updated_exercise.total_attempts += 1
                if answer_analysis.get('is_correct'):
                    updated_exercise.correct_attempts += 1
                else:
                    updated_exercise.wrong_attempts += 1
                updated_exercise.save()

                # 更新知识点掌握程度
                _update_knowledge_point_mastery(user, updated_exercise, answer_analysis.get('is_correct', False))
                
                print(f"题目 {updated_exercise.id} 异步分析完成")

            except Exception as e:
                import traceback
                error_details = f"AI分析失败: {str(e)}\n{traceback.format_exc()}"
                print(error_details)
                
                # 如果分析失败，标记为错误状态
                try:
                    connections.close_all()
                    from practice.models import PracticeRecord
                    updated_record = PracticeRecord.objects.get(id=thread_data['practice_record_id'])
                    updated_record.status = 'wrong'
                    updated_record.llm_analysis = {
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'analysis_failed': True
                    }
                    updated_record.points_earned = 0
                    updated_record.save()
                    print(f"错误状态保存完成")
                except Exception as save_error:
                    print(f"保存错误状态失败: {str(save_error)}")
                    import traceback
                    traceback.print_exc()
            finally:
                # 清理临时文件
                if thread_data['saved_image_path']:
                    try:
                        import os
                        os.unlink(thread_data['saved_image_path'])
                        print(f"临时文件已清理: {thread_data['saved_image_path']}")
                    except Exception as cleanup_error:
                        print(f"清理临时文件失败: {str(cleanup_error)}")

        # 启动后台线程
        analysis_thread = threading.Thread(target=process_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
        print(f"异步分析线程已启动，记录ID: {practice_record.id}")

        return Response({
            'message': '答案已提交，AI正在后台分析',
            'status': 'submitted'
        })

    except (Exercise.DoesNotExist, PracticeSession.DoesNotExist):
        return Response({'error': '习题或会话不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_analysis_status(request, session_id):
    """获取练习会话的分析状态"""
    try:
        session = PracticeSession.objects.get(id=session_id, student=request.user)
        
        # 检查是否还有待分析的记录
        pending_records = PracticeRecord.objects.filter(
            session=session,
            status='pending'
        ).count()
        
        total_records = PracticeRecord.objects.filter(session=session).count()
        
        analysis_complete = pending_records == 0 and total_records > 0
        
        return Response({
            'analysis_complete': analysis_complete,
            'pending_count': pending_records,
            'total_count': total_records,
            'progress': ((total_records - pending_records) / total_records * 100) if total_records > 0 else 0
        })

    except PracticeSession.DoesNotExist:
        return Response({'error': '练习会话不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_practice_session(request):
    """结束练习会话"""
    try:
        session_id = request.data.get('session_id')
        session = PracticeSession.objects.get(id=session_id, student=request.user)
        session.end_time = timezone.now()
        session.save()

        # 计算知识点得分
        _calculate_session_knowledge_scores(session)

        return Response({
            'message': '练习会话已结束',
            'session': PracticeSessionSerializer(session).data
        })

    except PracticeSession.DoesNotExist:
        return Response({'error': '练习会话不存在'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommended_exercises(request):
    """获取推荐练习题目"""
    try:
        subject_id = request.query_params.get('subject_id')
        knowledge_point_ids = request.query_params.getlist('knowledge_point_ids')
        difficulty = request.query_params.get('difficulty')
        count = int(request.query_params.get('count', 10))
        practice_mode = request.query_params.get('practice_mode', 'weakness')

        recommended_exercises = _get_recommended_exercises(
            request.user,
            subject_id,
            knowledge_point_ids,
            difficulty,
            count,
            practice_mode
        )

        return Response({
            'recommended_exercises': recommended_exercises
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KnowledgePointMasteryListView(generics.ListAPIView):
    """知识点掌握程度列表视图"""
    serializer_class = KnowledgePointMasterySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = KnowledgePointMastery.objects.filter(student=self.request.user)
        subject_id = self.request.query_params.get('subject_id')
        min_mastery = self.request.query_params.get('min_mastery')

        if subject_id:
            queryset = queryset.filter(knowledge_point__subject_id=subject_id)
        if min_mastery:
            queryset = queryset.filter(mastery_level__lte=min_mastery)

        return queryset.order_by('mastery_level')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def vllm_config(request):
    """获取或更新VL LLM配置（单例模式）"""
    try:
        if request.method == 'GET':
            # 获取当前活跃配置
            config = VLLMConfig.get_active_config()
            serializer = VLLMConfigSerializer(config)
            return Response(serializer.data)

        elif request.method == 'POST':
            # 只有管理员可以更新配置
            if request.user.user_type != 'admin':
                return Response({'error': '只有管理员可以修改VL LLM配置'},
                              status=status.HTTP_403_FORBIDDEN)

            # 获取当前配置并更新
            config = VLLMConfig.get_active_config()
            serializer = VLLMConfigSerializer(config, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'VL LLM配置更新成功',
                    'config': serializer.data
                })

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_vllm_connection(request):
    """测试VL LLM连接"""
    try:
        # 只有管理员可以测试连接
        if request.user.user_type != 'admin':
            return Response({'error': '只有管理员可以测试VL LLM连接'},
                          status=status.HTTP_403_FORBIDDEN)

        from exercises.vllm_service import VLLMService
        vllm_service = VLLMService()

        print(f"=== VLLM配置信息 ===")
        print(f"API URL: {vllm_service.api_url}")
        print(f"API Key: {vllm_service.api_key[:20]}...")
        print(f"Model Name: {vllm_service.model_name}")
        print(f"===================")

        # 测试连接 - 发送一个简单的请求
        headers = {
            "Authorization": f"Bearer {vllm_service.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": vllm_service.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": "测试连接"
                }
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }

        print(f"发送测试请求到: {vllm_service.api_url}")
        response = requests.post(
            vllm_service.api_url,
            headers=headers,
            json=payload,
            timeout=10
        )

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            return Response({
                'message': 'VL LLM连接测试成功',
                'api_url': vllm_service.api_url,
                'model_name': vllm_service.model_name
            })
        else:
            return Response({
                'error': 'VL LLM连接测试失败',
                'status_code': response.status_code,
                'response': response.text
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"VLLM连接测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'连接测试失败: {str(e)}'},
                      status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_vllm_config(request):
    """调试VLLM配置信息"""
    try:
        from exercises.vllm_service import VLLMService
        vllm_service = VLLMService()
        
        config_info = {
            'api_url': vllm_service.api_url,
            'api_key_prefix': vllm_service.api_key[:20] + '...' if vllm_service.api_key else 'None',
            'model_name': vllm_service.model_name,
            'api_key_length': len(vllm_service.api_key) if vllm_service.api_key else 0
        }
        
        return Response({
            'message': 'VLLM配置信息获取成功',
            'config': config_info
        })
        
    except Exception as e:
        return Response({
            'error': f'获取VLLM配置失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_practice_session(request, session_id):
    """获取练习会话详情"""
    try:
        session = PracticeSession.objects.get(id=session_id, student=request.user)
        serializer = PracticeSessionSerializer(session)
        return Response(serializer.data)

    except PracticeSession.DoesNotExist:
        return Response({'error': '练习会话不存在'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_practice_records(request):
    """获取练习记录列表"""
    try:
        session_id = request.query_params.get('session_id')
        if session_id:
            records = PracticeRecord.objects.filter(
                session_id=session_id,
                session__student=request.user
            ).select_related('exercise').prefetch_related('exercise__knowledge_points')
        else:
            records = PracticeRecord.objects.filter(
                session__student=request.user
            ).select_related('exercise').prefetch_related('exercise__knowledge_points')

        serializer = PracticeRecordSerializer(records, many=True)
        return Response({
            'results': serializer.data,
            'count': len(records)
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_knowledge_points(request):
    """获取练习会话知识点得分"""
    try:
        session_id = request.query_params.get('session_id')
        if session_id:
            kp_scores = SessionKnowledgePointScore.objects.filter(
                session_id=session_id,
                session__student=request.user
            ).select_related('knowledge_point')
        else:
            kp_scores = SessionKnowledgePointScore.objects.filter(
                session__student=request.user
            ).select_related('knowledge_point')

        serializer = SessionKnowledgePointScoreSerializer(kp_scores, many=True)
        return Response({
            'results': serializer.data,
            'count': len(kp_scores)
        })

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_recommended_exercises(user, subject_id, knowledge_point_ids, difficulty, count, practice_mode='weakness'):
    """获取推荐练习题目"""
    try:
        # 构建基础查询条件
        exercises = Exercise.objects.all()

        if subject_id:
            exercises = exercises.filter(subject_id=subject_id)

        if knowledge_point_ids:
            exercises = exercises.filter(knowledge_points__id__in=knowledge_point_ids)

        if difficulty:
            exercises = exercises.filter(difficulty=difficulty)

        # 获取用户相关数据
        user_mistakes = StudentExercise.objects.filter(
            student=user,
            is_mistake=True
        ).values_list('exercise_id', flat=True)

        weak_knowledge_points = KnowledgePointMastery.objects.filter(
            student=user,
            mastery_level__lt=70
        ).values_list('knowledge_point_id', flat=True)

        # 根据练习模式应用不同的筛选和权重策略
        if practice_mode == 'mistakes':
            # 错题重练模式：只推荐错题
            if not user_mistakes:
                # 如果没有错题，返回空列表
                return []
            exercises = exercises.filter(id__in=user_mistakes)
            
        elif practice_mode == 'weakness':
            # 薄弱强化模式：优先推荐薄弱知识点题目
            if weak_knowledge_points:
                exercises = exercises.filter(
                    Q(id__in=user_mistakes) |
                    Q(knowledge_points__id__in=weak_knowledge_points)
                ).distinct()
            # 如果没有薄弱知识点，使用智能推荐（错题+困难题）
            else:
                exercises = exercises.filter(
                    Q(id__in=user_mistakes) |
                    Q(difficulty='hard')
                ).distinct()
                
        elif practice_mode == 'mixed':
            # 综合练习模式：混合各种类型的题目
            # 1/3 错题，1/3 薄弱知识点题目，1/3 随机新题
            all_exercises = list(exercises.distinct())
            
            # 如果没有足够的题目，放宽筛选条件
            if len(all_exercises) < count:
                # 重新获取所有符合条件的题目（不限制错题和薄弱知识点）
                all_exercises = list(Exercise.objects.all())
                if subject_id:
                    all_exercises = [ex for ex in all_exercises if ex.subject_id == int(subject_id)]
                if difficulty:
                    all_exercises = [ex for ex in all_exercises if ex.difficulty == difficulty]
            
            random.shuffle(all_exercises)
            
            # 分配题目
            exercises_per_type = max(1, count // 3)
            recommended = []
            
            # 添加错题
            mistake_exercises = [ex for ex in all_exercises if ex.id in user_mistakes][:exercises_per_type]
            recommended.extend(mistake_exercises)
            
            # 添加薄弱知识点题目
            if weak_knowledge_points:
                weak_exercises = [ex for ex in all_exercises 
                                if any(kp.id in weak_knowledge_points for kp in ex.knowledge_points.all())
                                and ex not in recommended][:exercises_per_type]
                recommended.extend(weak_exercises)
            
            # 添加随机新题
            remaining_exercises = [ex for ex in all_exercises if ex not in recommended]
            new_exercises = remaining_exercises[:count - len(recommended)]
            recommended.extend(new_exercises)
            
            # 确保有足够的题目
            if len(recommended) < count:
                # 如果还不够，再添加一些随机题目
                additional_exercises = [ex for ex in all_exercises if ex not in recommended]
                recommended.extend(additional_exercises[:count - len(recommended)])
            
            # 为综合练习模式生成推荐结果
            result = []
            for i, exercise in enumerate(recommended[:count]):
                reason = ""
                if exercise.id in user_mistakes:
                    reason = "错题重练"
                elif weak_knowledge_points and any(kp.id in weak_knowledge_points for kp in exercise.knowledge_points.all()):
                    reason = "薄弱知识点强化"
                else:
                    reason = "新题练习"
                    
                result.append({
                    'exercise': ExerciseSerializer(exercise).data,
                    'weight': count - i,  # 简单的递减权重
                    'reason': reason
                })
            
            return result

        # 对于 'weakness' 和 'mistakes' 模式，使用权重计算
        recommended = []
        for exercise in exercises:
            weight = _calculate_exercise_weight(exercise, user, user_mistakes, weak_knowledge_points, practice_mode)
            recommended.append({
                'exercise': ExerciseSerializer(exercise).data,
                'weight': weight,
                'reason': _get_recommendation_reason(exercise, user, user_mistakes, weak_knowledge_points, practice_mode)
            })

        # 按权重排序并选择指定数量的题目
        recommended.sort(key=lambda x: x['weight'], reverse=True)
        return recommended[:count]

    except Exception as e:
        raise Exception(f"获取推荐题目失败: {str(e)}")


def _calculate_exercise_weight(exercise, user, user_mistakes, weak_knowledge_points, practice_mode='weakness'):
    """计算习题推荐权重"""
    weight = 1.0

    # 根据练习模式调整基础权重
    if practice_mode == 'mistakes':
        # 错题重练模式：错题权重极高
        if exercise.id in user_mistakes:
            weight += 10.0
        else:
            weight += 0.1  # 非错题权重极低
    elif practice_mode == 'weakness':
        # 薄弱强化模式：错题和薄弱知识点权重高
        if exercise.id in user_mistakes:
            weight += 5.0
        
        # 薄弱知识点的题目权重较高
        for kp in exercise.knowledge_points.all():
            if kp.id in weak_knowledge_points:
                try:
                    mastery = KnowledgePointMastery.objects.get(
                        student=user,
                        knowledge_point=kp
                    )
                    weight += (100 - mastery.mastery_level) / 20  # 掌握程度越低，权重越高
                except KnowledgePointMastery.DoesNotExist:
                    weight += 2.0  # 没有掌握程度记录的给予中等权重
    else:  # mixed模式
        # 综合练习模式：平衡各种因素
        if exercise.id in user_mistakes:
            weight += 3.0
        for kp in exercise.knowledge_points.all():
            if kp.id in weak_knowledge_points:
                weight += 2.0

    # 题目难度权重（所有模式都适用）
    if exercise.difficulty == 'easy':
        weight += 1.0
    elif exercise.difficulty == 'medium':
        weight += 2.0
    elif exercise.difficulty == 'hard':
        weight += 3.0

    # 习题正确率（正确率低的题目优先）
    if exercise.total_attempts > 0:
        accuracy_rate = exercise.correct_attempts / exercise.total_attempts
        weight += (1 - accuracy_rate) * 3.0

    return weight


def _get_recommendation_reason(exercise, user, user_mistakes, weak_knowledge_points, practice_mode='weakness'):
    """获取推荐原因"""
    reasons = []

    if practice_mode == 'mistakes':
        if exercise.id in user_mistakes:
            reasons.append("错题重练 - 专门复习您的错题")
        else:
            reasons.append("错题重练 - 相关错题")
    elif practice_mode == 'weakness':
        if exercise.id in user_mistakes:
            reasons.append("薄弱强化 - 错题优先")
        
        exercise_kps = set(exercise.knowledge_points.all().values_list('id', flat=True))
        weak_overlap = exercise_kps & set(weak_knowledge_points)
        if weak_overlap:
            reasons.append("薄弱强化 - 针对薄弱知识点")
        else:
            reasons.append("薄弱强化 - 智能推荐")
    elif practice_mode == 'mixed':
        if exercise.id in user_mistakes:
            reasons.append("综合练习 - 错题复习")
        else:
            exercise_kps = set(exercise.knowledge_points.all().values_list('id', flat=True))
            weak_overlap = exercise_kps & set(weak_knowledge_points)
            if weak_overlap:
                reasons.append("综合练习 - 薄弱知识点")
            else:
                reasons.append("综合练习 - 新题练习")
    else:
        # 默认推荐原因
        if exercise.id in user_mistakes:
            reasons.append("这是您之前的错题")

        exercise_kps = set(exercise.knowledge_points.all().values_list('id', flat=True))
        weak_overlap = exercise_kps & set(weak_knowledge_points)
        if weak_overlap:
            reasons.append("涉及您掌握薄弱的知识点")

        if exercise.total_attempts > 0:
            accuracy_rate = exercise.correct_attempts / exercise.total_attempts
            if accuracy_rate < 0.5:
                reasons.append("这是一道大多数同学都觉得困难的题目")

        if not reasons:
            reasons.append("根据您的学习情况智能推荐")

    return "; ".join(reasons)


def _update_knowledge_point_mastery(student, exercise, is_correct):
    """更新知识点掌握程度"""
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


def _update_session_knowledge_points(session, exercise, is_correct, earned_points):
    """更新练习会话知识点得分"""
    for kp in exercise.knowledge_points.all():
        kp_score, created = SessionKnowledgePointScore.objects.get_or_create(
            session=session,
            knowledge_point=kp,
            defaults={
                'total_questions': 1,
                'correct_answers': 1 if is_correct else 0,
                'score': earned_points,
                'weight': _get_knowledge_point_weight(kp)
            }
        )

        if not created:
            kp_score.total_questions += 1
            if is_correct:
                kp_score.correct_answers += 1
            kp_score.score += earned_points
            kp_score.save()


def _update_session_stats(session):
    """重新计算练习会话统计"""
    records = PracticeRecord.objects.filter(session=session)
    session.total_questions = records.count()
    session.correct_answers = records.filter(status='correct').count()

    # 计算加权总分
    total_weighted_score = 0
    total_weight = 0

    kp_scores = SessionKnowledgePointScore.objects.filter(session=session)
    for kp_score in kp_scores:
        weighted_score = kp_score.calculate_weighted_score()
        total_weighted_score += weighted_score
        total_weight += kp_score.weight

    if total_weight > 0:
        session.score = total_weighted_score / total_weight
    else:
        # 如果没有知识点得分，使用简单的正确率计算
        if session.total_questions > 0:
            session.score = (session.correct_answers / session.total_questions) * 100
        else:
            session.score = 0

    session.save()


def _get_knowledge_point_weight(knowledge_point):
    """获取知识点权重（可根据重要性调整）"""
    # 这里可以根据知识点的重要性设置不同权重
    # 目前使用默认权重1.0
    return 1.0


def _calculate_session_knowledge_scores(session):
    """计算练习会话的知识点得分"""
    try:
        from django.db.models import Q, Sum, Count, Avg
        from exercises.models import Exercise

        # 获取该会话的所有练习记录
        practice_records = PracticeRecord.objects.filter(session=session).select_related('exercise')

        # 统计每个知识点的答题情况
        knowledge_points_stats = {}

        for record in practice_records:
            exercise = record.exercise
            # 获取题目的所有知识点
            knowledge_points = exercise.knowledge_points.all()

            for kp in knowledge_points:
                if kp.id not in knowledge_points_stats:
                    knowledge_points_stats[kp.id] = {
                        'knowledge_point': kp,
                        'total_questions': 0,
                        'correct_answers': 0,
                        'weight': _get_knowledge_point_weight(kp)
                    }

                knowledge_points_stats[kp.id]['total_questions'] += 1
                if record.is_correct:
                    knowledge_points_stats[kp.id]['correct_answers'] += 1

        # 保存知识点得分
        SessionKnowledgePointScore.objects.filter(session=session).delete()  # 删除旧的记录

        for kp_id, stats in knowledge_points_stats.items():
            kp = stats['knowledge_point']
            total_questions = stats['total_questions']
            correct_answers = stats['correct_answers']
            weight = stats['weight']

            # 计算知识点得分
            if total_questions > 0:
                score = (correct_answers / total_questions) * 100
            else:
                score = 0

            # 创建知识点得分记录
            SessionKnowledgePointScore.objects.create(
                session=session,
                knowledge_point=kp,
                total_questions=total_questions,
                correct_answers=correct_answers,
                score=score,
                weight=weight
            )

        # 更新会话的总分
        kp_scores = SessionKnowledgePointScore.objects.filter(session=session)
        total_weighted_score = sum(kp.score * kp.weight for kp in kp_scores)
        total_weight = sum(kp.weight for kp in kp_scores)

        if total_weight > 0:
            session.score = total_weighted_score / total_weight
        else:
            # 如果没有知识点得分，使用简单的正确率计算
            if session.total_questions > 0:
                session.score = (session.correct_answers / session.total_questions) * 100
            else:
                session.score = 0

        session.save()

    except Exception as e:
        print(f"计算知识点得分失败: {str(e)}")
        # 不抛出异常，避免影响会话结束流程


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_practice_session(request, session_id):
    """完成练习会话"""
    try:
        session = PracticeSession.objects.get(id=session_id, student=request.user)
        
        # 计算最终统计数据
        _calculate_session_knowledge_scores(session)
        
        # 标记会话为已完成
        session.status = 'completed'
        session.end_time = timezone.now()
        session.save()
        
        return Response({
            'message': '练习会话已完成',
            'session_id': session.id,
            'score': session.score,
            'accuracy_rate': session.accuracy_rate,
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers
        })
    except PracticeSession.DoesNotExist:
        return Response(
            {'error': '练习会话不存在'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'完成练习会话失败: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
