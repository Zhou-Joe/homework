from django.contrib import admin
from .models import Subject, KnowledgePoint, ExamPoint, Exercise, StudentExercise


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(KnowledgePoint)
class KnowledgePointAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'grade_level', 'created_at')
    list_filter = ('subject', 'grade_level', 'created_at')
    search_fields = ('name', 'subject__name')
    ordering = ('subject', 'grade_level', 'name')


@admin.register(ExamPoint)
class ExamPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'knowledge_point', 'subject', 'grade_level', 'difficulty_weight', 'created_at')
    list_filter = ('subject', 'knowledge_point', 'grade_level', 'created_at')
    search_fields = ('name', 'knowledge_point__name', 'subject__name')
    ordering = ('subject', 'knowledge_point', 'grade_level', 'name')


class KnowledgePointInline(admin.TabularInline):
    model = Exercise.knowledge_points.through
    extra = 1


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'grade_level', 'difficulty', 'created_by', 'accuracy_rate', 'total_attempts', 'created_at')
    list_filter = ('subject', 'grade_level', 'difficulty', 'created_at')
    search_fields = ('title', 'question_text')
    readonly_fields = ('accuracy_rate', 'total_attempts', 'correct_attempts', 'wrong_attempts', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'subject', 'grade_level', 'difficulty', 'created_by')
        }),
        ('题目内容', {
            'fields': ('question_text', 'question_image')
        }),
        ('答案信息', {
            'fields': ('answer_text', 'answer_steps')
        }),
        ('统计信息', {
            'fields': ('total_attempts', 'correct_attempts', 'wrong_attempts', 'accuracy_rate')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    inlines = [KnowledgePointInline]


@admin.register(StudentExercise)
class StudentExerciseAdmin(admin.ModelAdmin):
    list_display = ('student', 'exercise', 'status', 'is_mistake', 'upload_time')
    list_filter = ('status', 'is_mistake', 'upload_time')
    search_fields = ('student__nickname', 'student__username', 'exercise__title')
    ordering = ('-upload_time',)

    fieldsets = (
        ('基本信息', {
            'fields': ('student', 'exercise', 'status', 'is_mistake')
        }),
        ('学生答案', {
            'fields': ('student_answer_text', 'student_answer_image')
        }),
        ('分析结果', {
            'fields': ('llm_analysis',)
        }),
        ('时间信息', {
            'fields': ('upload_time',)
        }),
    )

    readonly_fields = ('upload_time',)
