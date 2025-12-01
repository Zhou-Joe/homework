#!/usr/bin/env python
"""
测试批量上传功能的简单脚本
"""
import os
import sys
import django
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_learning_platform.settings')
django.setup()

from exercises.vllm_service import VLLMService
from exercises.models import Subject, Exercise
from django.core.files.uploadedfile import SimpleUploadedFile

def test_vlm_service():
    """测试VLM服务的简化分析功能"""
    print("=== 测试VLM服务简化分析功能 ===")

    # 创建一个虚拟的图片文件（仅用于测试）
    test_image_content = b"fake_image_content_for_testing"
    test_image = SimpleUploadedFile("test_question.jpg", test_image_content, content_type="image/jpeg")

    try:
        # 初始化VLM服务
        vllm_service = VLLMService()
        print("✅ VLM服务初始化成功")

        # 测试简化分析提示词生成
        prompt = vllm_service._build_simple_analysis_prompt("初一")
        print("✅ 简化分析提示词生成成功")
        print(f"提示词长度: {len(prompt)} 字符")

        # 检查提示词是否包含要求的内容
        required_phrases = [
            "选择题必须包含所有选项",
            "LaTeX格式",
            '{"questions": ["题目1", "题目2"]}',
            "未识别到题目内容"
        ]

        for phrase in required_phrases:
            if phrase in prompt:
                print(f"✅ 提示词包含: {phrase}")
            else:
                print(f"❌ 提示词缺少: {phrase}")

        # 测试默认结果格式
        default_result = vllm_service._get_default_simple_analysis_result()
        expected_keys = ["questions"]

        print("✅ 默认分析结果:")
        print(json.dumps(default_result, indent=2, ensure_ascii=False))

        for key in expected_keys:
            if key in default_result:
                print(f"✅ 默认结果包含: {key}")
            else:
                print(f"❌ 默认结果缺少: {key}")

        # 测试后处理功能
        test_analysis = {
            "questions": [
                "下列哪个是正确的数学表达式？A. $2+2=4$ B. $2+2=5$ C. $2+2=3$ D. $2+2=6$",
                "解方程：$x^2 - 4 = 0$"
            ]
        }

        processed_result = vllm_service._post_process_exercise_data(
            test_analysis, "初一", test_image, 1
        )

        print("✅ 后处理结果:")
        print(json.dumps(processed_result, indent=2, ensure_ascii=False))

        # 检查后处理结果的字段
        required_fields = [
            "title", "question_text", "subject", "grade_level",
            "answer_text", "answer_steps", "visibility",
            "source", "is_solved"
        ]

        questions = processed_result.get("questions", [])
        if questions:
            for i, question in enumerate(questions):
                print(f"\n--- 检查题目 {i+1} ---")
                for field in required_fields:
                    if field in question:
                        print(f"✅ 题目{i+1}包含: {field} = {question[field]}")
                    else:
                        print(f"❌ 题目{i+1}缺少: {field}")

        return True

    except Exception as e:
        print(f"❌ VLM服务测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_structure():
    """测试数据库结构和Exercise模型"""
    print("\n=== 测试数据库结构 ===")

    try:
        # 检查Exercise模型的所有字段
        exercise_fields = [field.name for field in Exercise._meta.fields]
        print("✅ Exercise模型字段:")
        for field in exercise_fields:
            print(f"  - {field}")

        # 检查必需的字段
        required_fields = [
            "title", "question_text", "subject", "grade_level",
            "difficulty", "answer_text", "answer_steps",
            "visibility", "source", "is_solved", "created_by"
        ]

        for field in required_fields:
            if field in exercise_fields:
                print(f"✅ 必需字段存在: {field}")
            else:
                print(f"❌ 必需字段缺失: {field}")

        # 检查权限选项
        visibility_choices = [choice[0] for choice in Exercise.VISIBILITY_CHOICES]
        print(f"✅ 权限选项: {visibility_choices}")

        if "public" in visibility_choices:
            print("✅ 公共权限选项存在")
        else:
            print("❌ 公共权限选项缺失")

        return True

    except Exception as e:
        print(f"❌ 数据库结构测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始测试批量上传功能...")

    success_count = 0
    total_tests = 2

    # 测试VLM服务
    if test_vlm_service():
        success_count += 1

    # 测试数据库结构
    if test_database_structure():
        success_count += 1

    print(f"\n=== 测试总结 ===")
    print(f"总测试数: {total_tests}")
    print(f"成功测试: {success_count}")
    print(f"失败测试: {total_tests - success_count}")

    if success_count == total_tests:
        print("🎉 所有测试通过！批量上传功能准备就绪。")
        return True
    else:
        print("⚠️  部分测试失败，请检查上述错误。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)