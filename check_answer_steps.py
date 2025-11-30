import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_learning_platform.settings')
django.setup()

from exercises.models import Exercise

def check_answer_steps():
    exercises = Exercise.objects.all()
    print(f'总习题数量: {exercises.count()}')
    
    empty_steps = exercises.filter(answer_steps='')
    null_steps = exercises.filter(answer_steps__isnull=True)
    
    print(f'answer_steps为空的习题数量: {empty_steps.count()}')
    print(f'answer_steps为null的习题数量: {null_steps.count()}')
    
    # 显示前5个习题的answer_steps情况
    print('\n前5个习题的answer_steps情况:')
    for i, exercise in enumerate(exercises[:5]):
        print(f'{i+1}. 题目ID: {exercise.id}, 标题: {exercise.title[:30]}...')
        print(f'   answer_steps长度: {len(exercise.answer_steps) if exercise.answer_steps else 0}')
        if exercise.answer_steps:
            print(f'   answer_steps内容: {exercise.answer_steps[:100]}...')
        else:
            print('   answer_steps内容: 空')
        print('---')

if __name__ == '__main__':
    check_answer_steps()
