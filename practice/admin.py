from django.contrib import admin
from .models import PracticeSession, PracticeRecord, KnowledgePointMastery, VLLMConfig


class PracticeRecordInline(admin.TabularInline):
    model = PracticeRecord
    extra = 0
    readonly_fields = ('created_at', 'llm_analysis')
    fields = ('exercise', 'status', 'response_time', 'student_answer_text', 'created_at')


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'start_time', 'end_time', 'total_questions', 'correct_answers', 'score', 'accuracy_rate')
    list_filter = ('start_time', 'score')
    search_fields = ('student__nickname', 'student__username')
    readonly_fields = ('accuracy_rate', 'start_time', 'end_time')
    ordering = ('-start_time',)

    fieldsets = (
        ('基本信息', {
            'fields': ('student', 'total_questions', 'correct_answers', 'score')
        }),
        ('统计信息', {
            'fields': ('accuracy_rate',)
        }),
        ('时间信息', {
            'fields': ('start_time', 'end_time')
        }),
    )

    inlines = [PracticeRecordInline]


@admin.register(PracticeRecord)
class PracticeRecordAdmin(admin.ModelAdmin):
    list_display = ('session', 'exercise', 'status', 'response_time', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('session__student__nickname', 'exercise__title')
    readonly_fields = ('created_at', 'llm_analysis')
    ordering = ('-created_at',)

    fieldsets = (
        ('基本信息', {
            'fields': ('session', 'exercise', 'status', 'response_time')
        }),
        ('学生答案', {
            'fields': ('student_answer_text', 'student_answer_image')
        }),
        ('分析结果', {
            'fields': ('llm_analysis',)
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )


@admin.register(KnowledgePointMastery)
class KnowledgePointMasteryAdmin(admin.ModelAdmin):
    list_display = ('student', 'knowledge_point', 'mastery_level', 'total_attempts', 'correct_attempts', 'accuracy_rate', 'last_practiced')
    list_filter = ('mastery_level', 'last_practiced', 'knowledge_point__subject')
    search_fields = ('student__nickname', 'knowledge_point__name')
    readonly_fields = ('accuracy_rate', 'last_practiced')
    ordering = ('mastery_level', '-last_practiced')

    fieldsets = (
        ('基本信息', {
            'fields': ('student', 'knowledge_point')
        }),
        ('掌握情况', {
            'fields': ('mastery_level', 'total_attempts', 'correct_attempts', 'accuracy_rate')
        }),
        ('时间信息', {
            'fields': ('last_practiced',)
        }),
    )


@admin.register(VLLMConfig)
class VLLMConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_url', 'model_name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'api_url', 'model_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'is_active')
        }),
        ('API配置', {
            'fields': ('api_url', 'api_key', 'model_name')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # 非管理员用户不能修改API密钥
        if request.user.user_type != 'admin' and obj:
            return self.readonly_fields + ('api_key',)
        return self.readonly_fields
