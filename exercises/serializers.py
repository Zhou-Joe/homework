from rest_framework import serializers
from .models import Subject, KnowledgePoint, ExamPoint, Exercise, StudentExercise


class SubjectSerializer(serializers.ModelSerializer):
    """学科序列化器"""
    class Meta:
        model = Subject
        fields = '__all__'


class KnowledgePointSerializer(serializers.ModelSerializer):
    """知识点序列化器"""
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = KnowledgePoint
        fields = '__all__'


class ExamPointSerializer(serializers.ModelSerializer):
    """考点序列化器"""
    knowledge_point_name = serializers.CharField(source='knowledge_point.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    full_path = serializers.CharField(read_only=True)

    class Meta:
        model = ExamPoint
        fields = '__all__'


class ExerciseSerializer(serializers.ModelSerializer):
    """习题序列化器"""
    knowledge_points = KnowledgePointSerializer(many=True, read_only=True)
    exam_points = ExamPointSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.nickname', read_only=True)

    # 权限相关字段
    target_users = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
        allow_null=True
    )
    visibility_text = serializers.CharField(source='get_visibility_display', read_only=True)
    can_user_access = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = '__all__'

    def get_can_user_access(self, obj):
        """检查当前用户是否有权限访问此题目"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.can_user_access(request.user)
        return False


class StudentExerciseSerializer(serializers.ModelSerializer):
    """学生错题记录序列化器"""
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_subject = serializers.CharField(source='exercise.subject.name', read_only=True)
    student_nickname = serializers.CharField(source='student.nickname', read_only=True)

    class Meta:
        model = StudentExercise
        fields = '__all__'
        read_only_fields = ('student', 'upload_time', 'llm_analysis')  # 这些字段由后端自动设置


class DashboardStatsSerializer(serializers.Serializer):
    """首页统计数据序列化器"""
    total_exercises = serializers.IntegerField()
    mistake_count = serializers.IntegerField()
    practice_count = serializers.IntegerField()
    accuracy_rate = serializers.FloatField()
    subject_stats = serializers.ListField()
    recent_mistakes = serializers.ListField()
    weak_knowledge_points = serializers.ListField()