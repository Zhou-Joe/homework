#!/usr/bin/env python
"""
测试知识点分类器
"""

import os
import sys
import django

# 设置Django环境
sys.path.append('/mnt/c/Users/ZC/VSProject/homework')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_learning_platform.settings')
django.setup()

from exercises.knowledge_classifier import KnowledgePointClassifier
from exercises.models import KnowledgePoint


def test_classifier():
    """测试知识点分类器"""
    print("=== 知识点分类器测试 ===\n")

    classifier = KnowledgePointClassifier()

    # 测试用例
    test_cases = [
        {
            'text': '已知函数f(x) = x² + 2x - 1，求其最小值',
            'grade': 10,
            'expected_concepts': ['二次函数', '函数']
        },
        {
            'text': '计算数列1, 3, 5, 7, ...的前10项和',
            'grade': 10,
            'expected_concepts': ['数列', '等差数列']
        },
        {
            'text': '已知抛物线y = ax² + bx + c过点(1,2), (2,1), (3,6)，求其方程',
            'grade': 9,
            'expected_concepts': ['二次函数', '抛物线']
        },
        {
            'text': '求不定积分∫x²dx',
            'grade': 12,
            'expected_concepts': ['积分', '导数']
        },
        {
            'text': '从6个球中取出2个球的组合数',
            'grade': 12,
            'expected_concepts': ['概率', '排列组合']
        },
        {
            'text': '已知三角形三边分别为3, 4, 5，求其面积',
            'grade': 8,
            'expected_concepts': ['几何', '勾股定理']
        },
        {
            'text': '小明有10个苹果，吃了3个，还剩几个？',
            'grade': 2,
            'expected_concepts': ['加减法']
        },
        {
            'text': '计算圆的周长，半径为5cm',
            'grade': 6,
            'expected_concepts': ['圆']
        },
        {
            'text': '解方程2x + 3 = 7',
            'grade': 7,
            'expected_concepts': ['一元一次方程']
        },
        {
            'text': '计算sin30°的值',
            'grade': 9,
            'expected_concepts': ['三角函数']
        },
        {
            'text': '求导数f\'(x)，其中f(x) = e^x',
            'grade': 12,
            'expected_concepts': ['导数', '指数函数']
        },
        {
            'text': '不等式x² - 4x + 3 > 0的解集',
            'grade': 10,
            'expected_concepts': ['不等式']
        },
        {
            'text': '向量a = (1, 2)，b = (3, 4)，求a·b',
            'grade': 10,
            'expected_concepts': ['平面向量', '向量']
        }
    ]

    print(f"开始测试 {len(test_cases)} 个用例...\n")

    correct_predictions = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"测试用例 {i}: {test_case['text']}")
        print(f"年级: {test_case['grade']}, 期望概念: {test_case['expected_concepts']}")

        # 进行分类
        matches = classifier.classify_by_text(
            test_case['text'],
            grade_level=test_case['grade'],
            subject_id=1  # 数学
        )

        if matches:
            best_match = matches[0]
            kp = best_match['knowledge_point']
            score = best_match['score']
            reasons = best_match['match_reasons']

            print(f"最佳匹配: {kp.name} (分数: {score})")
            print(f"匹配原因: {reasons}")

            # 检查是否匹配期望概念
            matched_concepts = []
            for concept in test_case['expected_concepts']:
                if concept.lower() in kp.name.lower():
                    matched_concepts.append(concept)

            if matched_concepts:
                print(f"✅ 正确匹配概念: {matched_concepts}")
                correct_predictions += 1
            else:
                print(f"❌ 未匹配期望概念")
        else:
            print("❌ 无匹配结果")

        print("-" * 50)

    # 统计结果
    accuracy = correct_predictions / len(test_cases) * 100
    print(f"\n=== 测试结果 ===")
    print(f"总测试用例: {len(test_cases)}")
    print(f"正确预测: {correct_predictions}")
    print(f"准确率: {accuracy:.1f}%")

    # 测试知识点数量
    total_kps = KnowledgePoint.objects.count()
    math_kps = KnowledgePoint.objects.filter(subject_id=1).count()
    print(f"\n数据库中的知识点:")
    print(f"总知识点数: {total_kps}")
    print(f"数学知识点数: {math_kps}")

    # 测试新知识点建议功能
    print(f"\n=== 新知识点建议测试 ===")
    test_new_cases = [
        "计算椭圆的面积公式",
        "使用拉格朗日乘数法求解条件极值",
        "矩阵的特征值和特征向量",
        "傅里叶级数的收敛性"
    ]

    for text in test_new_cases:
        suggestions = classifier.suggest_new_knowledge_point(text)
        print(f"题目: {text}")
        if suggestions:
            for suggestion in suggestions:
                print(f"  建议知识点: {suggestion['name']} (年级: {suggestion['grade']})")
        else:
            print("  无特殊建议")
        print()


if __name__ == '__main__':
    test_classifier()