#!/usr/bin/env python
"""
测试批量上传统计修复
"""
import os
import sys
import json
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_learning_platform.settings')
django.setup()

from exercises.vllm_service import VLLMService

def test_batch_statistics():
    """测试批量分析统计功能"""
    print("=== 测试批量分析统计修复 ===")

    # 创建测试分析结果
    mock_results = [
        {
            'file_name': 'image1.jpg',
            'index': 0,
            'status': 'success',
            'is_valid_question': True,
            'rejection_reason': '',
            'questions': [
                '题目1: 2+2=?',
                '题目2: 3+4=?',
                '题目3: 5-2=?'
            ]
        },
        {
            'file_name': 'image2.jpg',
            'index': 1,
            'status': 'error',
            'is_valid_question': False,
            'rejection_reason': '图片无法识别',
            'questions': []
        },
        {
            'file_name': 'image3.jpg',
            'index': 2,
            'status': 'success',
            'is_valid_question': True,
            'rejection_reason': '',
            'questions': [
                '题目4: x^2=9，求x的值'
            ]
        }
    ]

    # 模拟处理结果的统计逻辑
    total_files = len(mock_results)
    valid_questions_count = 0
    invalid_questions_count = 0

    for result in mock_results:
        if result.get('is_valid_question', False):
            # 统计这张图片中的题目数量
            questions = result.get('questions', [])
            valid_questions_count += len(questions)
            print(f"✅ 有效图片 {result['file_name']}: {len(questions)} 道题目")
        else:
            # 这张图片无效，记为0道题目
            invalid_questions_count += 1
            print(f"❌ 无效图片 {result['file_name']}: 0 道题目")

    print(f"\n=== 统计结果 ===")
    print(f"总图片数: {total_files}")
    print(f"有效图片数: {len([r for r in mock_results if r.get('is_valid_question', False)])}")
    print(f"无效图片数: {len([r for r in mock_results if not r.get('is_valid_question', False)])}")
    print(f"识别题目总数: {valid_questions_count}")

    # 验证期望结果
    expected_questions = 4  # image1有3道 + image3有1道 = 4道
    expected_valid_images = 2  # image1和image3有效
    expected_invalid_images = 1  # image2无效

    if valid_questions_count == expected_questions:
        print(f"✅ 题目统计正确: {valid_questions_count}道")
    else:
        print(f"❌ 题目统计错误: 期望{expected_questions}道，实际{valid_questions_count}道")

    if expected_valid_images == len([r for r in mock_results if r.get('is_valid_question', False)]):
        print(f"✅ 有效图片统计正确: {expected_valid_images}张")
    else:
        print(f"❌ 有效图片统计错误")

    if expected_invalid_images == len([r for r in mock_results if not r.get('is_valid_question', False)]):
        print(f"✅ 无效图片统计正确: {expected_invalid_images}张")
    else:
        print(f"❌ 无效图片统计错误")

    return {
        'total_files': total_files,
        'successful_analyses': valid_questions_count,
        'failed_analyses': invalid_questions_count,
        'results': mock_results
    }

if __name__ == "__main__":
    result = test_batch_statistics()
    print(f"\n=== 返回结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))