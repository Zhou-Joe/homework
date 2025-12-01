@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_batch_exercise_advanced(request):
    """高级批量保存题目"""
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': '无权限访问'}, status=403)

    try:
        data = json.loads(request.body)
        exercises_to_save = data.get('exercises_to_save', [])

        if not exercises_to_save:
            return JsonResponse({'error': '没有题目数据'}, status=400)

        saved_exercises = []
        failed_exercises = []

        # 遍历所有要保存的题目
        for exercise_data in exercises_to_save:
            try:
                # 获取学科
                subject_name = exercise_data.get('subject', '数学')
                subject, created = Subject.objects.get_or_create(name=subject_name)

                # 创建题目
                exercise = Exercise.objects.create(
                    title=exercise_data.get('title', '批量上传题目'),
                    question_text=exercise_data.get('question_text', ''),
                    subject=subject,
                    grade_level=exercise_data.get('grade_level', '初一'),
                    difficulty=exercise_data.get('difficulty', 'medium'),
                    answer_text=exercise_data.get('answer_text', ''),  # 题目答案
                    answer_steps=exercise_data.get('answer_steps', ''),  # 解题步骤
                    created_by=request.user,
                    visibility=exercise_data.get('visibility', 'public'),  # 使用前端传递的权限
                    is_solved=exercise_data.get('is_solved', False),  # 使用前端传递的解决状态
                    source=exercise_data.get('source', 'batch_upload'),  # 使用前端传递的来源
                    total_attempts=exercise_data.get('total_attempts', 0),
                    correct_attempts=exercise_data.get('correct_attempts', 0),
                    wrong_attempts=exercise_data.get('wrong_attempts', 0),
                )

                # 处理知识点关联
                knowledge_points = exercise_data.get('knowledge_points', [])
                for kp_name in knowledge_points:
                    kp, created = KnowledgePoint.objects.get_or_create(
                        name=kp_name,
                        subject=exercise.subject,
                        grade_level=exercise.grade_level,
                        defaults={'description': f'{kp_name}相关知识点'}
                    )
                    exercise.knowledge_points.add(kp)

                # 处理考点关联
                exam_points = exercise_data.get('exam_points', [])
                for ep_name in exam_points:
                    ep, created = ExamPoint.objects.get_or_create(
                        name=ep_name,
                        subject=exercise.subject,
                        grade_level=exercise.grade_level,
                        defaults={'description': f'{ep_name}相关考点'}
                    )
                    exercise.exam_points.add(ep)

                saved_exercises.append({
                    'exercise_id': exercise.id,
                    'title': exercise.title,
                    'subject': exercise.subject,
                    'grade_level': exercise.grade_level,
                    'file_name': exercise_data.get('file_name', '')
                })

            except Exception as e:
                failed_exercises.append({
                    'file_name': exercise_data.get('file_name', ''),
                    'error': str(e)
                })
                print(f"题目保存失败: {str(e)}")

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