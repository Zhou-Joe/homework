from django.db import migrations


def create_initial_subjects_and_knowledge_points(apps, schema_editor):
    """创建初始学科和知识点数据"""
    Subject = apps.get_model('exercises', 'Subject')
    KnowledgePoint = apps.get_model('exercises', 'KnowledgePoint')

    # 创建基础学科
    subjects = [
        {'name': '数学', 'description': '数学学科'},
        {'name': '语文', 'description': '语文学科'},
        {'name': '英语', 'description': '英语学科'},
        {'name': '物理', 'description': '物理学科'},
        {'name': '化学', 'description': '化学学科'},
        {'name': '生物', 'description': '生物学科'},
        {'name': '历史', 'description': '历史学科'},
        {'name': '地理', 'description': '地理学科'},
        {'name': '政治', 'description': '政治学科'},
    ]

    created_subjects = {}
    for subject_data in subjects:
        subject = Subject.objects.create(**subject_data)
        created_subjects[subject.name] = subject

    # 为数学创建一些基础知识点（示例）
    math_knowledge_points = [
        {'name': '整数运算', 'grade_levels': [1, 2, 3]},
        {'name': '分数运算', 'grade_levels': [3, 4, 5, 6]},
        {'name': '小数运算', 'grade_levels': [4, 5, 6]},
        {'name': '代数方程', 'grade_levels': [7, 8, 9]},
        {'name': '函数', 'grade_levels': [8, 9, 10, 11]},
        {'name': '几何图形', 'grade_levels': [3, 4, 5, 6, 7, 8]},
        {'name': '三角函数', 'grade_levels': [10, 11, 12]},
        {'name': '概率统计', 'grade_levels': [7, 8, 9, 10, 11, 12]},
    ]

    for kp_data in math_knowledge_points:
        for grade in kp_data['grade_levels']:
            KnowledgePoint.objects.create(
                name=kp_data['name'],
                subject=created_subjects['数学'],
                grade_level=grade,
                description=f'{kp_data["name"]} - {grade}年级'
            )


def create_default_vllm_config(apps, schema_editor):
    """创建默认的VL LLM配置"""
    VLLMConfig = apps.get_model('practice', 'VLLMConfig')

    VLLMConfig.objects.create(
        name='默认配置',
        api_url='https://api.siliconflow.cn/v1/chat/completions',
        api_key='sk-hglnfzrlezgqtiionjdduvqrfmwfpjnkdksfizvnpseqvlwu',
        model_name='Qwen/Qwen3-VL-32B-Instruct',
        is_active=True
    )


class Migration(migrations.Migration):
    dependencies = [
        ('exercises', '0001_initial'),
        ('practice', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_subjects_and_knowledge_points),
        migrations.RunPython(create_default_vllm_config),
    ]