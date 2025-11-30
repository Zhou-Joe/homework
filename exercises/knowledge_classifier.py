"""
智能知识点分类器
基于VLLM的题目知识点自动分类系统
"""

import json
import re
from django.db.models import Q
from .models import Subject, KnowledgePoint


class KnowledgePointClassifier:
    """知识点智能分类器"""

    def __init__(self):
        self.math_keywords = {
            # 小学阶段关键词
            'elementary': {
                '1年级': ['加法', '减法', '认识数字', '比较大小', '图形'],
                '2年级': ['乘法', '除法', '表内', '两位数', '长度'],
                '3年级': ['万以内', '三位数', '分数', '小数', '面积'],
                '4年级': ['大数', '运算定律', '小数加减', '角', '平行四边形'],
                '5年级': ['小数乘除', '方程', '因数', '倍数', '分数', '长方体'],
                '6年级': ['分数乘除', '比', '比例', '百分数', '圆', '圆柱', '圆锥']
            },
            # 初中阶段关键词
            'middle_school': {
                '7年级': ['有理数', '整式', '一元一次方程', '相交线', '平行线'],
                '8年级': ['二次根式', '一元二次方程', '一次函数', '反比例函数', '全等', '勾股定理'],
                '9年级': ['二次函数', '抛物线', '圆', '相似', '旋转', '概率']
            },
            # 高中阶段关键词
            'high_school': {
                '10年级': ['集合', '函数', '指数', '对数', '立体几何', '解析几何', '向量', '数列', '不等式'],
                '11年级': ['三角函数', '解三角形', '平面向量', '概率', '统计'],
                '12年级': ['导数', '积分', '极限', '排列组合', '概率统计', '解析几何综合']
            }
        }

        # 核心数学概念关键词映射
        self.concept_keywords = {
            '不等式': ['不等式', '大于', '小于', '不小于', '不大于', '区间', '解集'],
            '数列': ['数列', '等差', '等比', '通项', '前n项和', '递推', '数列求和'],
            '概率': ['概率', '随机', '可能', '组合', '排列', '样本空间', '事件'],
            '几何': ['几何', '图形', '三角形', '四边形', '圆', '立体', '平面', '角度'],
            '立体几何': ['立体', '空间', '向量', '三维', '体积', '表面积', '投影'],
            '解析几何': ['坐标', '方程', '直线', '圆', '抛物线', '椭圆', '双曲线', '距离'],
            '函数': ['函数', '定义域', '值域', '单调', '奇偶', '周期', '最值'],
            '二次函数': ['二次', '抛物线', '顶点', '对称轴', '开口', '判别式'],
            '三角函数': ['三角', '正弦', '余弦', '正切', '角度', '弧度', '周期'],
            '导数': ['导数', '微商', '斜率', '极值', '最值', '单调', '切线'],
            '积分': ['积分', '面积', '体积', '原函数', '不定积分', '定积分']
        }

    def classify_by_text(self, question_text, grade_level=None, subject_id=None):
        """
        基于题目文本内容进行知识点分类
        """
        if not question_text:
            return []

        # 预处理文本
        text = question_text.lower()

        # 获取候选知识点
        candidate_kps = self._get_candidate_knowledge_points(grade_level, subject_id)

        # 计算每个知识点的匹配分数
        scored_kps = []
        for kp in candidate_kps:
            score = self._calculate_match_score(text, kp, grade_level)
            if score > 0:
                scored_kps.append({
                    'knowledge_point': kp,
                    'score': score,
                    'match_reasons': self._get_match_reasons(text, kp)
                })

        # 按分数排序并返回最佳匹配
        scored_kps.sort(key=lambda x: x['score'], reverse=True)

        return scored_kps[:3]  # 返回前3个最佳匹配

    def _get_candidate_knowledge_points(self, grade_level=None, subject_id=None):
        """获取候选知识点"""
        query = Q()

        if grade_level:
            query &= Q(grade_level=grade_level)

        if subject_id:
            query &= Q(subject_id=subject_id)

        # 如果没有指定年级，返回数学学科的所有知识点
        if not grade_level and not subject_id:
            math_subject = Subject.objects.filter(name='数学').first()
            if math_subject:
                query &= Q(subject=math_subject)

        return KnowledgePoint.objects.filter(query).order_by('grade_level', 'name')

    def _calculate_match_score(self, text, kp, grade_level=None):
        """计算匹配分数"""
        score = 0

        # 基础分数：年级匹配
        if grade_level:
            try:
                kp_grade = int(kp.grade_level) if kp.grade_level else 0
                user_grade = int(grade_level) if grade_level else 0

                if kp_grade == user_grade:
                    score += 50
                elif abs(kp_grade - user_grade) <= 1:
                    score += 25  # 相邻年级
                elif abs(kp_grade - user_grade) <= 2:
                    score += 10  # 相差2年级以内
            except (ValueError, TypeError):
                # 如果年级不是数字，跳过年级匹配
                pass

        # 关键词匹配
        kp_text = kp.name.lower() + ' ' + kp.description.lower()

        # 完全匹配检查
        if self._exact_match_check(text, kp_text):
            score += 100
            return score

        # 关键词匹配
        keywords = self._extract_keywords(kp_text)
        matched_keywords = 0
        for keyword in keywords:
            if keyword in text:
                matched_keywords += 1
                score += 20

        # 概念匹配
        for concept, concept_keywords in self.concept_keywords.items():
            if concept.lower() in kp_text:
                for kw in concept_keywords:
                    if kw in text:
                        score += 15

        # 数学符号和公式匹配
        if self._contains_math_symbols(text):
            if '函数' in kp_text or '方程' in kp_text or '不等式' in kp_text:
                score += 10
            if '几何' in kp_text and any(char in text for char in ['∠', '△', '○', '□']):
                score += 10
            if '数列' in kp_text and 'n' in text:
                score += 10

        return score

    def _exact_match_check(self, text, kp_text):
        """检查完全匹配"""
        # 检查关键短语的完全匹配
        key_phrases = [
            '二次函数', '抛物线', '椭圆', '双曲线', '等差数列', '等比数列',
            '导数', '积分', '概率', '统计', '向量', '矩阵', '极限'
        ]

        for phrase in key_phrases:
            if phrase in text and phrase in kp_text:
                return True

        return False

    def _extract_keywords(self, text):
        """提取关键词"""
        # 移除常见停用词
        stop_words = {'的', '是', '在', '和', '与', '或', '但', '如果', '因为', '所以', '那么', '这', '那', '之', '中'}

        # 按空格和标点分割
        words = re.split(r'[，。！？；：、\s]+', text)

        # 过滤并返回关键词
        keywords = []
        for word in words:
            word = word.strip()
            if len(word) >= 2 and word not in stop_words:
                keywords.append(word)

        return keywords

    def _contains_math_symbols(self, text):
        """检查是否包含数学符号"""
        math_symbols = ['=', '+', '-', '*', '/', '²', '³', '√', '∫', '∑', '∏', '∞', '≈', '≤', '≥', '≠', '∈', '∪', '∩', '⊂', '⊃', '→', '←']
        return any(symbol in text for symbol in math_symbols)

    def _get_match_reasons(self, text, kp):
        """获取匹配原因"""
        reasons = []

        # 年级匹配
        if kp.grade_level:
            if f'{kp.grade_level}年级' in text:
                reasons.append(f"年级匹配: {kp.grade_level}年级")

        # 关键词匹配
        kp_text = kp.name.lower()
        keywords = self._extract_keywords(kp_text)
        matched = [kw for kw in keywords if kw in text]
        if matched:
            reasons.append(f"关键词匹配: {', '.join(matched[:3])}")

        # 概念匹配
        for concept, concept_keywords in self.concept_keywords.items():
            if concept.lower() in kp_text:
                matched_concepts = [kw for kw in concept_keywords if kw in text]
                if matched_concepts:
                    reasons.append(f"概念匹配: {concept} - {', '.join(matched_concepts[:2])}")

        # 数学符号匹配
        if self._contains_math_symbols(text):
            reasons.append("包含数学符号")

        return reasons

    def get_best_knowledge_points(self, question_text, grade_level=None, subject_id=None, max_results=3):
        """
        获取最佳匹配的知识点
        """
        matches = self.classify_by_text(question_text, grade_level, subject_id)

        if not matches:
            # 如果没有匹配，返回通用知识点
            return self._get_generic_knowledge_points(grade_level, subject_id, max_results)

        return [m['knowledge_point'] for m in matches[:max_results]]

    def _get_generic_knowledge_points(self, grade_level=None, subject_id=None, max_results=3):
        """获取通用知识点作为默认返回"""
        generic_names = [
            '数学思想-函数与方程',
            '数学思想-数形结合',
            '数学思想-转化与化归',
            '数学思想-分类讨论'
        ]

        kps = KnowledgePoint.objects.filter(
            name__in=generic_names
        ).order_by('id')[:max_results]

        if kps.exists():
            return list(kps)

        # 如果连通用知识点都没有，返回数学学科的基础知识点
        if subject_id is None:
            math_subject = Subject.objects.filter(name='数学').first()
            if math_subject:
                subject_id = math_subject.id

        if subject_id:
            return list(KnowledgePoint.objects.filter(
                subject_id=subject_id
            ).order_by('grade_level', 'name')[:max_results])

        return []

    def suggest_new_knowledge_point(self, question_text, grade_level=None, subject_id=None):
        """
        建议创建新知识点
        """
        # 基于题目内容分析可能的知识点
        suggestions = []

        # 分析题目特征
        text = question_text.lower()

        # 检查特殊数学概念
        special_concepts = {
            '椭圆': {'name': '解析几何-椭圆', 'grade': 10},
            '双曲线': {'name': '解析几何-双曲线', 'grade': 10},
            '矩阵': {'name': '线性代数-矩阵', 'grade': 12},
            '极限': {'name': '微积分-极限', 'grade': 12},
            '傅里叶': {'name': '高等数学-傅里叶级数', 'grade': 12},
            '拉格朗日': {'name': '高等数学-拉格朗日中值定理', 'grade': 12}
        }

        for concept, info in special_concepts.items():
            if concept in text:
                suggestions.append(info)

        return suggestions