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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # 统计字段
    total_attempts = models.IntegerField(default=0, verbose_name='总尝试次数')
    correct_attempts = models.IntegerField(default=0, verbose_name='正确次数')
    wrong_attempts = models.IntegerField(default=0, verbose_name='错误次数')

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
