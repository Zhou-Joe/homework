from django.db import models
from django.conf import settings
from exercises.models import Exercise


class PracticeSession(models.Model):
    """练习会话模型"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='学生')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    total_questions = models.IntegerField(default=0, verbose_name='总题目数')
    correct_answers = models.IntegerField(default=0, verbose_name='正确答案数')
    score = models.FloatField(default=0, verbose_name='得分')

    class Meta:
        verbose_name = '练习会话'
        verbose_name_plural = '练习会话'

    def __str__(self):
        return f"{self.student.nickname} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    @property
    def accuracy_rate(self):
        """正确率"""
        if self.total_questions == 0:
            return 0
        return (self.correct_answers / self.total_questions) * 100


class PracticeRecord(models.Model):
    """练习记录模型"""
    STATUS_CHOICES = [
        ('correct', '正确'),
        ('wrong', '错误'),
        ('skipped', '跳过'),
        ('pending', '待分析'),
    ]

    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, verbose_name='练习会话')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, verbose_name='习题')
    student_answer_text = models.TextField(blank=True, verbose_name='学生答案')
    student_answer_image = models.ImageField(upload_to='uploads/answers/', blank=True, null=True, verbose_name='学生答题图片')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='答题状态')
    response_time = models.IntegerField(help_text='响应时间（毫秒）', verbose_name='响应时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='答题时间')
    llm_analysis = models.JSONField(default=dict, blank=True, null=True, verbose_name='LLM分析结果')
    question_number = models.IntegerField(default=1, verbose_name='题目序号')
    points_earned = models.FloatField(default=0, verbose_name='获得分数')

    class Meta:
        verbose_name = '练习记录'
        verbose_name_plural = '练习记录'
        ordering = ['session', 'question_number']

    def __str__(self):
        return f"{self.session.student.nickname} - {self.exercise.title}"

    @property
    def is_correct(self):
        """是否答对"""
        return self.status == 'correct'


class KnowledgePointMastery(models.Model):
    """知识点掌握程度模型"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='学生')
    knowledge_point = models.ForeignKey('exercises.KnowledgePoint', on_delete=models.CASCADE, verbose_name='知识点')
    mastery_level = models.FloatField(default=0, verbose_name='掌握程度 (0-100)')
    total_attempts = models.IntegerField(default=0, verbose_name='总尝试次数')
    correct_attempts = models.IntegerField(default=0, verbose_name='正确次数')
    last_practiced = models.DateTimeField(auto_now=True, verbose_name='最后练习时间')

    class Meta:
        verbose_name = '知识点掌握程度'
        verbose_name_plural = '知识点掌握程度'
        unique_together = ['student', 'knowledge_point']

    def __str__(self):
        return f"{self.student.nickname} - {self.knowledge_point.name}"

    @property
    def accuracy_rate(self):
        """正确率"""
        if self.total_attempts == 0:
            return 0
        return (self.correct_attempts / self.total_attempts) * 100


class SessionKnowledgePointScore(models.Model):
    """练习会话知识点得分模型"""
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, verbose_name='练习会话')
    knowledge_point = models.ForeignKey('exercises.KnowledgePoint', on_delete=models.CASCADE, verbose_name='知识点')
    total_questions = models.IntegerField(default=0, verbose_name='该知识点题目数')
    correct_answers = models.IntegerField(default=0, verbose_name='该知识点答对数')
    score = models.FloatField(default=0, verbose_name='知识点得分')
    weight = models.FloatField(default=1.0, verbose_name='权重')

    class Meta:
        verbose_name = '练习会话知识点得分'
        verbose_name_plural = '练习会话知识点得分'
        unique_together = ['session', 'knowledge_point']

    def __str__(self):
        return f"{self.session.student.nickname} - {self.knowledge_point.name}"

    @property
    def accuracy_rate(self):
        """正确率"""
        if self.total_questions == 0:
            return 0
        return (self.correct_answers / self.total_questions) * 100

    def calculate_weighted_score(self):
        """计算加权得分"""
        return self.score * self.weight


class VLLMConfig(models.Model):
    """VL LLM 配置模型 - 单例模式，只有一个活跃配置"""
    name = models.CharField(max_length=100, default='VL LLM配置', verbose_name='配置名称')
    api_url = models.URLField(verbose_name='API地址')
    api_key = models.CharField(max_length=200, verbose_name='API密钥')
    model_name = models.CharField(max_length=100, verbose_name='模型名称')
    is_active = models.BooleanField(default=True, unique=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = 'VL LLM配置'
        verbose_name_plural = 'VL LLM配置'

    def __str__(self):
        return self.name

    @classmethod
    def get_active_config(cls):
        """获取当前活跃配置"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            # 如果没有活跃配置，创建一个默认配置
            return cls.objects.create(
                name='默认VL LLM配置',
                api_url='https://api.siliconflow.cn/v1/chat/completions',
                api_key='sk-hglnfzrlezgqtiionjdduvqrfmwfpjnkdksfizvnpseqvlwu',
                model_name='Qwen/Qwen3-VL-32B-Instruct',
                is_active=True
            )

    def save(self, *args, **kwargs):
        """确保只有一个活跃配置"""
        if self.is_active:
            # 将其他所有配置设为非活跃
            VLLMConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
