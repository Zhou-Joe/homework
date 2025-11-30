from rest_framework import serializers
from .models import PracticeSession, PracticeRecord, KnowledgePointMastery, VLLMConfig, SessionKnowledgePointScore
from exercises.models import Exercise
from exercises.serializers import ExerciseSerializer


class VLLMConfigSerializer(serializers.ModelSerializer):
    """VL LLM配置序列化器"""
    class Meta:
        model = VLLMConfig
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PracticeSessionSerializer(serializers.ModelSerializer):
    """练习会话序列化器"""
    student_nickname = serializers.CharField(source='student.nickname', read_only=True)
    accuracy_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = PracticeSession
        fields = '__all__'


class PracticeRecordSerializer(serializers.ModelSerializer):
    """练习记录序列化器"""
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    exercise_subject = serializers.CharField(source='exercise.subject.name', read_only=True)
    exercise_difficulty = serializers.CharField(source='exercise.difficulty', read_only=True)
    exercise_question_text = serializers.CharField(source='exercise.question_text', read_only=True)
    exercise_answer_steps = serializers.CharField(source='exercise.answer_steps', read_only=True)
    exercise_correct_answer = serializers.CharField(source='exercise.correct_answer', read_only=True)
    knowledge_points = serializers.SerializerMethodField()
    is_correct = serializers.BooleanField(read_only=True)

    class Meta:
        model = PracticeRecord
        fields = '__all__'

    def get_knowledge_points(self, obj):
        """获取知识点列表"""
        if obj.exercise:
            return [{
                'id': kp.id,
                'name': kp.name,
                'subject': kp.subject.name
            } for kp in obj.exercise.knowledge_points.all()]
        return []


class KnowledgePointMasterySerializer(serializers.ModelSerializer):
    """知识点掌握程度序列化器"""
    knowledge_point_name = serializers.CharField(source='knowledge_point.name', read_only=True)
    subject_name = serializers.CharField(source='knowledge_point.subject.name', read_only=True)
    accuracy_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = KnowledgePointMastery
        fields = '__all__'


class RecommendedExerciseSerializer(serializers.ModelSerializer):
    """推荐习题序列化器"""
    exercise = ExerciseSerializer(read_only=True)
    reason = serializers.CharField(read_only=True)
    priority = serializers.IntegerField(read_only=True)

    class Meta:
        model = PracticeRecord
        fields = ['exercise', 'reason', 'priority']


class SessionKnowledgePointScoreSerializer(serializers.ModelSerializer):
    """练习会话知识点得分序列化器"""
    knowledge_point_name = serializers.CharField(source='knowledge_point.name', read_only=True)
    subject_name = serializers.CharField(source='knowledge_point.subject.name', read_only=True)
    accuracy_rate = serializers.FloatField(read_only=True)
    weighted_score = serializers.FloatField(read_only=True)

    class Meta:
        model = SessionKnowledgePointScore
        fields = '__all__'