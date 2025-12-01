from django.db import models
from django.conf import settings


class Subject(models.Model):
    """学科模型"""
    name = models.CharField(max_length=50, verbose_name='学科名称')
    description = models.TextField(blank=True, verbose_name='学科描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '学科'
        verbose_name_plural = '学科'

    def __str__(self):
        return self.name


class KnowledgePoint(models.Model):
    """知识点模型 (二级分类)"""
    name = models.CharField(max_length=100, verbose_name='知识点名称')
    description = models.TextField(blank=True, verbose_name='知识点描述')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='所属学科')
    grade_level = models.CharField(max_length=10, verbose_name='适用年级', choices=[
        ('小学1年级', '小学1年级'), ('小学2年级', '小学2年级'), ('小学3年级', '小学3年级'),
        ('小学4年级', '小学4年级'), ('小学5年级', '小学5年级'), ('小学6年级', '小学6年级'),
        ('初一', '初一'), ('初二', '初二'), ('初三', '初三'),
        ('高一', '高一'), ('高二', '高二'), ('高三', '高三'),
    ])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '知识点'
        verbose_name_plural = '知识点'
        unique_together = ['name', 'subject', 'grade_level']

    def __str__(self):
        return f"{self.subject.name} - {self.grade_level}年级 - {self.name}"


class ExamPoint(models.Model):
    """考点模型 (三级分类)"""
    name = models.CharField(max_length=100, verbose_name='考点名称')
    knowledge_point = models.ForeignKey(KnowledgePoint, on_delete=models.CASCADE, verbose_name='所属知识点')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='学科')
    grade_level = models.CharField(max_length=10, verbose_name='适用年级', choices=[
        ('小学1年级', '小学1年级'), ('小学2年级', '小学2年级'), ('小学3年级', '小学3年级'),
        ('小学4年级', '小学4年级'), ('小学5年级', '小学5年级'), ('小学6年级', '小学6年级'),
        ('初一', '初一'), ('初二', '初二'), ('初三', '初三'),
        ('高一', '高一'), ('高二', '高二'), ('高三', '高三'),
    ])
    description = models.TextField(blank=True, verbose_name='考点描述')
    difficulty_weight = models.FloatField(default=1.0, verbose_name='难度系数', help_text='1.0-3.0，数值越大难度越高')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '考点'
        verbose_name_plural = '考点'
        unique_together = ['name', 'knowledge_point', 'grade_level']

    def __str__(self):
        return f"{self.subject.name} - {self.knowledge_point.name} - {self.name}"

    @property
    def full_path(self):
        """获取完整分类路径：学科 - 知识点 - 考点"""
        return f"{self.subject.name} - {self.knowledge_point.name} - {self.name}"


class Exercise(models.Model):
    """习题模型"""
    DIFFICULTY_CHOICES = [
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ]

    VISIBILITY_CHOICES = [
        ('private', '私人'),  # 用户上传的错题，仅创建者可见
        ('public', '公共'),   # 管理员上传，对所有用户可见
        ('shared', '共享'),   # 共享题目，对指定用户或年级可见
    ]

    title = models.CharField(max_length=200, verbose_name='题目标题')
    question_text = models.TextField(verbose_name='题目内容')
    question_image = models.ImageField(upload_to='uploads/questions/', blank=True, null=True, verbose_name='题目图片')
    answer_text = models.TextField(verbose_name='标准答案')
    answer_steps = models.TextField(verbose_name='解题步骤')
    knowledge_points = models.ManyToManyField(KnowledgePoint, blank=True, verbose_name='相关知识点')
    exam_points = models.ManyToManyField('ExamPoint', blank=True, verbose_name='相关考点')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name='所属学科')
    grade_level = models.CharField(max_length=10, verbose_name='适用年级', choices=[
        ('小学1年级', '小学1年级'), ('小学2年级', '小学2年级'), ('小学3年级', '小学3年级'),
        ('小学4年级', '小学4年级'), ('小学5年级', '小学5年级'), ('小学6年级', '小学6年级'),
        ('初一', '初一'), ('初二', '初二'), ('初三', '初三'),
        ('高一', '高一'), ('高二', '高二'), ('高三', '高三'),
    ])
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', verbose_name='难度')

    # 权限相关字段
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private', verbose_name='可见性')
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_exercises',
        verbose_name='目标用户',
        help_text='当可见性为"共享"时，指定的用户可以访问此题目'
    )
    target_grade_levels = models.JSONField(
        default=list,
        blank=True,
        verbose_name='目标年级',
        help_text='当可见性为"共享"时，指定的年级用户可以访问此题目'
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # 统计字段
    total_attempts = models.IntegerField(default=0, verbose_name='总尝试次数')
    correct_attempts = models.IntegerField(default=0, verbose_name='正确次数')
    wrong_attempts = models.IntegerField(default=0, verbose_name='错误次数')

    # 批量上传相关字段
    source = models.CharField(max_length=50, default='individual', verbose_name='题目来源',
                              help_text='题目来源：individual(个人上传), batch_upload(批量上传)')
    is_solved = models.BooleanField(default=True, verbose_name='是否已解答',
                                   help_text='标记题目是否已有标准答案和解题步骤')

    class Meta:
        verbose_name = '习题'
        verbose_name_plural = '习题'

    def __str__(self):
        return self.title

    @property
    def accuracy_rate(self):
        """正确率"""
        if self.total_attempts == 0:
            return 0
        return (self.correct_attempts / self.total_attempts) * 100

    def can_user_access(self, user):
        """检查用户是否有权限访问此题目"""
        # 创建者始终可以访问
        if self.created_by == user:
            return True

        # 管理员可以访问所有题目
        if user.is_staff or user.is_superuser:
            return True

        # 公共题目，所有用户可以访问
        if self.visibility == 'public':
            return True

        # 私人题目，只有创建者可以访问
        if self.visibility == 'private':
            return False

        # 共享题目，检查是否在目标用户或年级中
        if self.visibility == 'shared':
            # 检查用户是否在目标用户列表中
            if user in self.target_users.all():
                return True

            # 检查用户年级是否在目标年级列表中
            if hasattr(user, 'grade_level') and user.grade_level:
                if user.grade_level in self.target_grade_levels:
                    return True

        return False

    @classmethod
    def get_accessible_exercises_for_user(cls, user):
        """获取用户可访问的题目（类方法，用于查询）"""
        from django.db.models import Q

        # 管理员可以访问所有题目
        if user.is_staff or user.is_superuser:
            return cls.objects.all()

        # 构建权限查询条件
        permission_q = (
            Q(created_by=user) |  # 创建者自己的题目
            Q(visibility='public') |  # 公共题目
            Q(visibility='shared', target_users=user)  # 共享给该用户的题目
        )

        # 如果用户有年级信息，添加年级条件
        if hasattr(user, 'grade_level') and user.grade_level:
            # 对于 JSONField，我们需要使用更兼容的查询方式
            # 先获取所有共享题目，然后在 Python 中过滤年级
            shared_by_grade = []
            shared_exercises = cls.objects.filter(
                visibility='shared'
            ).exclude(target_grade_levels=[])
            
            for exercise in shared_exercises:
                if user.grade_level in exercise.target_grade_levels:
                    shared_by_grade.append(exercise.id)
            
            if shared_by_grade:
                permission_q = permission_q | Q(id__in=shared_by_grade)

        return cls.objects.filter(permission_q).distinct()


class StudentExercise(models.Model):
    """学生错题记录"""
    STATUS_CHOICES = [
        ('correct', '正确'),
        ('wrong', '错误'),
        ('not_attempted', '未尝试'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='学生')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, verbose_name='习题')
    student_answer_text = models.TextField(blank=True, verbose_name='学生答案')
    student_answer_image = models.ImageField(upload_to='uploads/answers/', blank=True, null=True, verbose_name='学生答题图片')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_attempted', verbose_name='答题状态')
    is_mistake = models.BooleanField(default=True, verbose_name='是否为错题')
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    llm_analysis = models.JSONField(default=dict, blank=True, verbose_name='LLM分析结果')

    class Meta:
        verbose_name = '学生错题记录'
        verbose_name_plural = '学生错题记录'
        unique_together = ['student', 'exercise']

    def __str__(self):
        return f"{self.student.nickname} - {self.exercise.title}"
