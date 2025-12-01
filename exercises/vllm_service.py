import requests
import json
import base64
import logging
import os
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Subject, KnowledgePoint, ExamPoint, Exercise, StudentExercise

logger = logging.getLogger(__name__)


class VLLMService:
    """VL LLM 服务类"""

    def __init__(self):
        # 使用单例模式获取活跃配置
        from practice.models import VLLMConfig
        try:
            config = VLLMConfig.get_active_config()
            self.api_url = config.api_url
            self.api_key = config.api_key
            self.model_name = config.model_name
            print(f"VLLM服务初始化成功: URL={self.api_url}, Model={self.model_name}")
        except Exception as e:
            print(f"VLLM配置获取失败，使用默认配置: {str(e)}")
            # 使用默认配置，不抛出异常
            self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
            self.api_key = "sk-hglnfzrlezgqtiionjdduvqrfmwfpjnkdksfizvnpseqvlwu"
            self.model_name = "Qwen/Qwen3-VL-32B-Instruct"

    def encode_image(self, image_file):
        """将图片文件编码为base64"""
        try:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            return image_data
        except Exception as e:
            raise Exception(f"图片编码失败: {str(e)}")

    def analyze_exercise_batch_simple(self, image_files, student_grade_level):
        """简化的批量分析多个习题图片 - 只识别题目内容，其他参数由后处理填充"""
        results = []
        total_files = len(image_files)

        print(f"=== 开始简化批量习题分析 ===")
        print(f"总文件数: {total_files}")
        print(f"年级: {student_grade_level}")

        for index, image_file in enumerate(image_files):
            try:
                print(f"\n处理第 {index + 1}/{total_files} 个文件: {image_file.name if hasattr(image_file, 'name') else 'unknown'}")

                # 使用简化的分析
                result = self._analyze_simple_exercise(image_file, student_grade_level)

                # 后处理填充其他参数
                processed_result = self._post_process_exercise_data(result, student_grade_level, image_file, index)

                results.append(processed_result)
                print(f"第 {index + 1} 个文件分析成功")

            except Exception as e:
                error_result = {
                    'file_name': image_file.name if hasattr(image_file, 'name') else f'image_{index + 1}',
                    'index': index,
                    'status': 'error',
                    'error_message': str(e),
                    'is_valid_question': False,
                    'rejection_reason': f'分析失败: {str(e)}'
                }
                results.append(error_result)
                print(f"第 {index + 1} 个文件分析失败: {str(e)}")

        # 统计题目总数量（不是图片数量）
        valid_questions_count = 0
        invalid_questions_count = 0

        for result in results:
            if result.get('is_valid_question', False):
                # 统计这张图片中的题目数量
                questions = result.get('questions', [])
                valid_questions_count += len(questions)
            else:
                # 这张图片无效，记为0道题目
                invalid_questions_count += 1

        print(f"\n=== 简化批量分析完成 ===")
        print(f"有效图片数: {len([r for r in results if r.get('is_valid_question', False)])}")
        print(f"无效图片数: {len([r for r in results if not r.get('is_valid_question', False)])}")
        print(f"识别题目总数: {valid_questions_count}")

        return {
            'total_files': total_files,
            'successful_analyses': valid_questions_count,  # 题目总数，不是图片数
            'failed_analyses': invalid_questions_count,  # 无效图片数
            'results': results
        }

    def analyze_exercise_batch(self, image_files, student_grade_level):
        """批量分析多个习题图片 - 原有功能"""
        results = []
        total_files = len(image_files)

        print(f"=== 开始批量习题分析 ===")
        print(f"总文件数: {total_files}")
        print(f"年级: {student_grade_level}")

        for index, image_file in enumerate(image_files):
            try:
                print(f"\n处理第 {index + 1}/{total_files} 个文件: {image_file.name if hasattr(image_file, 'name') else 'unknown'}")

                # 分析单个图片
                result = self.analyze_exercise(image_file, student_grade_level)

                # 确保包含所有必需字段，符合数据库格式
                formatted_result = {
                    'file_name': image_file.name if hasattr(image_file, 'name') else f'image_{index + 1}',
                    'index': index,
                    'status': 'success' if result.get('is_valid_question', False) else 'error',
                    'is_valid_question': result.get('is_valid_question', False),
                    'rejection_reason': result.get('rejection_reason', '未知原因'),
                    'title': result.get('title', f'题目 {index + 1}'),
                    'subject': result.get('subject', '数学'),
                    'grade_level': result.get('grade_level', student_grade_level),
                    'knowledge_points': result.get('knowledge_points', []),
                    'exam_points': result.get('exam_points', []),
                    'question_text': result.get('question_text', ''),
                    'difficulty': result.get('difficulty', 'medium'),
                    'answer_steps': result.get('answer_steps', ''),  # 留空，后续由LLM解答
                    'correct_answer': result.get('correct_answer', ''),  # 留空，后续由LLM解答
                    'new_knowledge_points': result.get('new_knowledge_points', []),
                    'new_exam_points': result.get('new_exam_points', []),
                    'student_solution': result.get('student_solution', ''),
                    'subject_id': result.get('subject_id'),
                    'knowledge_point_ids': result.get('knowledge_point_ids', []),
                    'exam_point_ids': result.get('exam_point_ids', [])
                }

                results.append(formatted_result)
                print(f"第 {index + 1} 个文件分析成功")

            except Exception as e:
                error_result = {
                    'file_name': image_file.name if hasattr(image_file, 'name') else f'image_{index + 1}',
                    'index': index,
                    'status': 'error',
                    'error_message': str(e),
                    'is_valid_question': False,
                    'rejection_reason': f'分析失败: {str(e)}'
                }
                results.append(error_result)
                print(f"第 {index + 1} 个文件分析失败: {str(e)}")

        print(f"\n=== 批量分析完成 ===")
        print(f"成功: {len([r for r in results if r.get('is_valid_question', False)])}")
        print(f"失败: {len([r for r in results if not r.get('is_valid_question', False)])}")

        return {
            'total_files': total_files,
            'successful_analyses': len([r for r in results if r.get('is_valid_question', False)]),
            'failed_analyses': len([r for r in results if not r.get('is_valid_question', False)]),
            'results': results
        }

    def _analyze_simple_exercise(self, image_file, student_grade_level):
        """简化分析单个图片 - 只识别题目内容"""
        try:
            print(f"=== 开始简化习题分析 ===")
            print(f"年级: {student_grade_level}")
            print(f"图片文件: {image_file.name if hasattr(image_file, 'name') else 'unknown'}")

            # 构建简化的提示词
            prompt = self._build_simple_analysis_prompt(student_grade_level)
            print(f"简化提示词长度: {len(prompt)}")

            # 编码图片
            image_base64 = self.encode_image(image_file)
            print(f"图片base64长度: {len(image_base64)}")

            # 调用VL LLM API
            print("开始调用VLLM API（简化模式）...")
            response = self._call_vllm_api(prompt, image_base64)
            print("VLLM API调用成功")

            # 解析响应
            analysis_result = self._parse_simple_analysis_response(response)
            print(f"简化分析结果: {analysis_result}")

            print("=== 简化习题分析完成 ===")
            return analysis_result

        except Exception as e:
            print(f"简化习题分析异常: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"简化习题分析失败: {str(e)}")

    def _build_simple_analysis_prompt(self, grade_level):
        """构建简化的习题分析提示词"""
        prompt = f"""
你是一个专业的教育题目识别专家，请仔细分析上传的图片内容。

**任务：识别题目内容并返回题目文本列表**

请识别图片中的所有有效题目：
- 学校作业题目、练习题、考试题
- 数学题、物理题、化学题、语文题、英语题等学科题目
- 需要解答的数学公式、几何图形、阅读理解、填空题、选择题等
- 手写或打印的题目内容

**忽略以下内容：**
- 风景照片、人物照片、动物照片、食物照片、自拍照
- 书本封面、笔记截图、聊天记录截图、网页截图
- 网络图片、表情包、二维码
- 建筑物、家具、日用品、物品照片
- 空白纸张、随意涂鸦、无关图形、乱写乱画
- 模糊到无法辨认文字的图片
- 任何与学习无关的内容

识别要求：
- 完整的题目文本
- **选择题必须包含所有选项（A、B、C、D等），缺一不可**
- 如果是填空题，标明填空位置
- 如果是理科题目，数学公式使用LaTeX格式
- 一张图片可能包含多道题目，都要识别出来

请严格按照以下JSON格式返回结果：
{{
    "questions": [
        "第一道题目的完整文本（选择题包含所有选项A、B、C、D等，理科题目使用LaTeX格式）",
        "第二道题目的完整文本（选择题包含所有选项A、B、C、D等，理科题目使用LaTeX格式）"
    ]
}}

重要说明：
- 只返回题目文本列表，不包含其他参数
- 如果图片中没有有效题目，返回空数组：{{"questions": []}}
- **选择题必须包含所有选项，如果选项不完整或不清晰，请不要识别这道题目**
- 数学、物理、化学公式必须使用LaTeX格式：
  * 分数：\\frac{{a}}{{b}}
  * 根号：\\sqrt{{x}}
  * 上标：x^2
  * 下标：x_1
  * 求和：\\sum
  * 积分：\\int
  * 希腊字母：\\alpha, \\beta, \\pi, \\sigma, \\theta
"""
        return prompt

    def _parse_simple_analysis_response(self, response):
        """解析简化分析的响应"""
        try:
            content = response['choices'][0]['message']['content']

            # 调试：打印原始响应内容
            print(f"=== 简化VLLM Raw Response ===")
            print(f"Content length: {len(content)}")
            print(f"First 500 chars: {content[:500]}")
            print(f"Last 200 chars: {content[-200:]}")
            print(f"=== End 简化VLLM Response ===")

            # 尝试多种方法提取JSON
            methods = [
                lambda: self._extract_first_json(content),
                lambda: self._extract_json_braces(content),
                lambda: self._extract_json_regex(content)
            ]

            for method in methods:
                try:
                    result = method()
                    if result and 'questions' in result:
                        return result
                except:
                    continue

            # 如果所有方法都失败，返回默认结构
            return self._get_default_simple_analysis_result()

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise Exception(f"简化分析响应解析失败: {str(e)}")

    def _get_default_simple_analysis_result(self):
        """返回默认的简化分析结果"""
        return {
            "questions": []
        }

    def _post_process_exercise_data(self, analysis_result, student_grade_level, image_file, index):
        """后处理题目数据，填充其他字段"""
        file_name = image_file.name if hasattr(image_file, 'name') else f'image_{index + 1}'

        # 获取题目列表（新的简化格式）
        questions = analysis_result.get('questions', [])
        if not questions:
            return {
                'file_name': file_name,
                'index': index,
                'status': 'error',
                'is_valid_question': False,
                'rejection_reason': '未识别到题目内容'
            }

        # 处理每道题目
        processed_questions = []
        for i, question_text in enumerate(questions):
            subject_name = self._infer_subject_from_question(question_text)

            processed_question = {
                'title': f'题目 {index + 1}-{i + 1}',
                'question_text': question_text,  # VLM识别的题目文本
                'subject': subject_name,
                'grade_level': student_grade_level,  # 使用用户选择的年级
                'difficulty': 'medium',  # 默认中等难度

                # 需要AI进一步处理的字段
                'answer_text': '未处理',  # 标准答案，待AI处理
                'answer_steps': '未处理',  # 解题步骤，待AI处理
                'knowledge_points': [],  # 知识点，待AI处理
                'exam_points': [],  # 考点，待AI处理

                # 权限和来源设置
                'visibility': 'public',  # 设置为公共权限
                'source': 'batch_upload',  # 标记为批量上传
                'is_solved': False,  # 标记为未解决，需要后续AI处理

                # 统计字段初始值
                'total_attempts': 0,
                'correct_attempts': 0,
                'wrong_attempts': 0,

                # 其他字段
                'new_knowledge_points': [],  # 新知识点（兼容性保留）
                'new_exam_points': []  # 新考点（兼容性保留）
            }
            processed_questions.append(processed_question)

        return {
            'file_name': file_name,
            'index': index,
            'status': 'success',
            'is_valid_question': True,
            'rejection_reason': '',
            'questions': processed_questions
        }

    def _infer_subject_from_question(self, question_text):
        """根据题目内容推断学科"""
        question_lower = question_text.lower()

        # 数学关键词
        math_keywords = ['方程', '函数', '几何', '代数', '计算', '求解', '证明', '坐标', '角度', '面积', '体积', '概率', '统计']
        # 物理关键词
        physics_keywords = ['力', '速度', '加速度', '质量', '密度', '压强', '功', '功率', '电压', '电流', '电阻', '磁场']
        # 化学关键词
        chemistry_keywords = ['化学方程式', '分子', '原子', '溶液', '酸碱', '氧化', '还原', '元素', '化合物']
        # 语文关键词
        chinese_keywords = ['阅读', '作文', '古诗', '文言文', '修辞', '段落', '主旨', '概括']
        # 英语关键词
        english_keywords = ['translation', 'translate', 'grammar', 'verb', 'noun', 'adjective', 'article']

        if any(keyword in question_lower for keyword in math_keywords):
            return '数学'
        elif any(keyword in question_lower for keyword in physics_keywords):
            return '物理'
        elif any(keyword in question_lower for keyword in chemistry_keywords):
            return '化学'
        elif any(keyword in question_lower for keyword in chinese_keywords):
            return '语文'
        elif any(keyword in question_lower for keyword in english_keywords):
            return '英语'
        else:
            return '数学'  # 默认数学

    def solve_exercise_batch(self, exercises_data):
        """批量解答多个题目"""
        results = []
        total_exercises = len(exercises_data)
        
        print(f"=== 开始批量题目解答 ===")
        print(f"总题目数: {total_exercises}")
        
        for index, exercise_data in enumerate(exercises_data):
            try:
                print(f"\n解答第 {index + 1}/{total_exercises} 题")
                
                # 获取题目信息
                exercise_id = exercise_data.get('exercise_id')
                question_text = exercise_data.get('question_text')
                subject = exercise_data.get('subject', '数学')
                grade_level = exercise_data.get('grade_level', 6)
                
                if not question_text:
                    raise Exception("题目内容为空")
                
                # 调用文本解答
                solution_result = self.solve_question_from_text(
                    question_text, subject, grade_level
                )
                
                result = {
                    'exercise_id': exercise_id,
                    'index': index,
                    'status': 'success',
                    'solution': solution_result,
                    'answer': solution_result.get('answer', ''),
                    'steps': solution_result.get('steps', ''),
                    'knowledge_points': solution_result.get('knowledge_points', []),
                    'difficulty': solution_result.get('difficulty', 'medium')
                }
                
                results.append(result)
                print(f"第 {index + 1} 题解答成功")
                
            except Exception as e:
                error_result = {
                    'exercise_id': exercise_data.get('exercise_id'),
                    'index': index,
                    'status': 'error',
                    'error_message': str(e)
                }
                results.append(error_result)
                print(f"第 {index + 1} 题解答失败: {str(e)}")
        
        print(f"\n=== 批量解答完成 ===")
        print(f"成功: {len([r for r in results if r['status'] == 'success'])}")
        print(f"失败: {len([r for r in results if r['status'] == 'error'])}")
        
        return {
            'total_exercises': total_exercises,
            'successful_solutions': len([r for r in results if r['status'] == 'success']),
            'failed_solutions': len([r for r in results if r['status'] == 'error']),
            'results': results
        }

    def analyze_exercise(self, image_file, student_grade_level):
        """分析习题图片，使用VL LLM识别题目、学科、知识点等"""
        try:
            print(f"=== 开始习题分析 ===")
            print(f"年级: {student_grade_level}")
            print(f"图片文件: {image_file.name if hasattr(image_file, 'name') else 'unknown'}")

            # 获取所有已存在的知识点用于匹配
            knowledge_points = self._get_knowledge_points_for_prompt()
            print(f"知识点数量: {len(knowledge_points)}")

            # 构建提示词
            prompt = self._build_analysis_prompt(knowledge_points, student_grade_level)
            print(f"提示词长度: {len(prompt)}")

            # 编码图片
            image_base64 = self.encode_image(image_file)
            print(f"图片base64长度: {len(image_base64)}")

            # 调用VL LLM API
            print("开始调用VLLM API...")
            response = self._call_vllm_api(prompt, image_base64)
            print("VLLM API调用成功")

            # 解析响应
            analysis_result = self._parse_analysis_response(response)
            print(f"解析结果: {analysis_result}")

            # 处理知识点匹配
            analysis_result = self._process_knowledge_points(analysis_result, student_grade_level)

            print("=== 习题分析完成 ===")
            return analysis_result

        except Exception as e:
            print(f"习题分析异常: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"习题分析失败: {str(e)}")

    def analyze_student_answer(self, question_text, correct_answer, answer_steps, answer_image_file, question_image_file=None):
        """分析学生答案，判断是否正确"""
        try:
            # 构建提示词
            prompt = self._build_answer_analysis_prompt(question_text, correct_answer, answer_steps)

            # 编码答案图片
            answer_base64 = self.encode_image(answer_image_file)

            # 如果有题目图片，同时传递题目图片和答案图片
            if question_image_file:
                question_base64 = self.encode_image(question_image_file)
                response = self._call_vllm_api_with_two_images(prompt, question_base64, answer_base64)
            else:
                # 只有答案图片的情况
                response = self._call_vllm_api(prompt, answer_base64)

            # 解析响应
            analysis_result = self._parse_answer_analysis_response(response)

            return analysis_result

        except Exception as e:
            raise Exception(f"答案分析失败: {str(e)}")

    def analyze_student_text_answer(self, question_text, correct_answer, answer_steps, student_text):
        """分析学生文字答案，判断是否正确"""
        try:
            # 构建提示词
            prompt = self._build_text_answer_analysis_prompt(question_text, correct_answer, answer_steps, student_text)

            # 调用VL LLM API (纯文本，不需要图片)
            response = self._call_vllm_text_api(prompt)

            # 解析响应
            analysis_result = self._parse_answer_analysis_response(response)

            return analysis_result

        except Exception as e:
            raise Exception(f"文字答案分析失败: {str(e)}")

    def _get_knowledge_points_for_prompt(self):
        """获取知识点列表用于提示词"""
        knowledge_points = []
        for kp in KnowledgePoint.objects.all().select_related('subject'):
            knowledge_points.append({
                'name': kp.name,
                'subject': kp.subject.name,
                'grade_level': kp.grade_level
            })
        return knowledge_points

    def _get_exam_points_for_prompt(self):
        """获取考点列表用于提示词"""
        exam_points = []
        for ep in ExamPoint.objects.all().select_related('knowledge_point', 'subject'):
            exam_points.append({
                'name': ep.name,
                'subject': ep.subject.name,
                'knowledge_point': ep.knowledge_point.name,
                'grade_level': ep.grade_level,
                'full_path': f"{ep.subject.name} - {ep.knowledge_point.name} - {ep.name}"
            })
        return exam_points

    def _build_analysis_prompt(self, knowledge_points, grade_level):
        """构建习题分析的提示词"""
        kp_list = "\n".join([f"- {kp['subject']} {kp['grade_level']}年级: {kp['name']}"
                           for kp in knowledge_points])

        # 获取考点信息
        exam_points = self._get_exam_points_for_prompt()
        ep_list = "\n".join([f"- {ep['full_path']} ({ep['grade_level']}年级)"
                           for ep in exam_points])

        prompt = f"""
你是一个专业的教育题目识别专家，请仔细分析上传的图片内容，完成以下任务：

**第一步：严格判断图片内容是否为有效题目**
请首先判断图片是否包含以下教育相关内容：
- 学校作业题目、练习题、考试题
- 数学题、物理题、化学题、语文题、英语题等学科题目
- 包含题目要求、问题描述的计算题或应用题
- 需要解答的数学公式、几何图形、阅读理解、填空题、选择题等
- 手写或打印的题目内容

**必须拒绝的情况（is_valid_question必须为false）：**
- 风景照片、人物照片、动物照片、食物照片、自拍照
- 书本封面、笔记截图、聊天记录截图、网页截图
- 网络图片、表情包、表情符号、二维码
- 建筑物、家具、日用品、物品照片
- 空白纸张、随意涂鸦、无关的线条图形、乱写乱画
- 重复上传的同一张图片（用于测试系统）
- 任何与学习无关的内容、垃圾图片
- 模糊到无法辨认文字的图片

**第二步：如果是有效题目，进行专业分析**
如果确定是有效题目，请完成以下专业分析：

1. **题目内容识别**：
   - 准确识别题目文本内容
   - 识别题目类型（选择题、填空题、解答题、应用题等）
   - 如果是理科题目，数学公式必须使用LaTeX格式

2. **学科分类**：
   - 准确判断学科（数学、物理、化学、生物、语文、英语、历史、地理、政治）
   - 根据题目内容确定最适合的学科

3. **知识体系分类**：
   - 知识点（二级分类）：如代数、几何、函数、力学、电学等
   - 考点（三级分类）：如二次函数、勾股定理、牛顿定律等

4. **题目质量评估**：
   - 难度等级：easy（简单）、medium（中等）、hard（困难）
   - 根据年级水平和题目复杂度判断

**重要要求：**
- 数学、物理、化学等理科题目的公式必须使用标准LaTeX格式
- 确保题目文本完整准确，包含所有必要信息
- 如果是选择题，必须包含所有选项
- 解题步骤要详细清晰，便于学生理解

已知知识点列表（二级分类）：
{kp_list}

已知考点列表（三级分类）：
{ep_list}

请严格按照以下JSON格式返回结果：
{{
    "is_valid_question": true/false,
    "rejection_reason": "如果不是有效题目，详细说明拒绝原因",
    "subject": "学科名称（仅当is_valid_question=true时）",
    "grade_level": "题目适用的年级（仅当is_valid_question=true时）",
    "knowledge_points": ["知识点1", "知识点2"],
    "exam_points": ["考点1", "考点2"],
    "question_text": "识别出的题目文本（仅当is_valid_question=true时）",
    "difficulty": "easy/medium/hard（仅当is_valid_question=true时）",
    "answer_steps": "详细的解题步骤（仅当is_valid_question=true时）",
    "correct_answer": "标准答案（仅当is_valid_question=true时）",
    "title": "题目标题（仅当is_valid_question=true时）",
    "new_knowledge_points": [
        {{
            "name": "新知识点名称",
            "description": "知识点描述"
        }}
    ],
    "new_exam_points": [
        {{
            "name": "新考点名称",
            "knowledge_point": "所属知识点",
            "description": "考点描述"
        }}
    ]
}}

重要说明：
- is_valid_question为true时，必须提供完整的学科分析内容
- is_valid_question为false时，只需提供rejection_reason说明拒绝原因
- 年级必须是标准中国教育体系格式：小学1年级-小学6年级、初一-初三、高一-高三
- 难度必须是easy、medium、hard之一
- knowledge_points对应二级分类（知识点）
- exam_points对应三级分类（考点）
- 请优先匹配已有考点，如无匹配则创建新考点
- 如果图片中有学生的解答过程，请在student_solution字段中描述
- 如果发现新知识点或新考点，请在对应字段中列出
- **严格要求：宁可错杀，不可放过** - 对于任何不确定是否为学习题目的图片，请将is_valid_question设为false
"""
        return prompt

    def _build_answer_analysis_prompt(self, question_text, correct_answer, answer_steps):
        """构建答案分析的提示词"""
        prompt = f"""
请分析学生的答题情况。

题目：{question_text}
标准答案：{correct_answer}
详细解题步骤：{answer_steps}

请查看学生给出的答案图片，严格按照以下标准进行判断：

**第一优先级：答案相关性检查（最重要！）**
学生上传的图片是否确实是针对这道题目的答案？

**必须判定为错误的情况：**
1. 图片内容与题目完全无关（如风景照、人物照、动物、建筑、食物等）
2. 图片是文字、符号涂鸦但没有解题过程
3. 图片是其他科目的题目或答案
4. 图片中只有空白纸张或线条
5. 图片模糊到无法识别任何文字或符号
6. 图片是网络图片、截图、聊天记录等非手写内容
7. 图片是重复上传的同一张图（用于测试）

**可以认为是相关答案的情况：**
1. 图片中有数学计算过程
2. 图片中有解题步骤或公式推导
3. 图片中有明确的答案数字或表达式
4. 图片中有与题目相关的图形或图表分析

**第二优先级：答案正确性检查**
只有在确认图片内容是针对题目的相关答案后，才判断对错

**分析步骤：**
1. 首先确认图片内容是否为针对该题目的答案（这是关键步骤！）
2. 如果图片不是相关答案，直接判定为错误，并在error_analysis中详细说明原因
3. 如果是相关答案，再判断是否正确
4. 分析错误原因或评价答案质量

**格式要求：**
- 如果涉及数学公式，请使用LaTeX格式，例如：$x^2 + y^2 = r^2$，$$\\int_0^1 x^2 dx = \\frac{{1}}{{3}}$$
- 分数使用 $\\frac{{a}}{{b}}$ 格式
- 根号使用 $\\sqrt{{x}}$ 格式
- 求和使用 $\\sum$ 格式
- 积分使用 $\\int$ 格式
- 希腊字母使用 $\\alpha$, $\\beta$, $\\gamma$, $\\pi$, $\\sigma$, $\\theta$ 等格式

请严格按照以下JSON格式返回：
{{
    "student_answer": "学生给出的答案（含LaTeX格式数学公式）",
    "is_correct": true/false,
    "error_analysis": "错误原因分析（如果正确则为空，含LaTeX格式数学公式）",
    "feedback": "给学生反馈和建议（含LaTeX格式数学公式）",
    "solution_quality": "解题质量评价，包括步骤完整性和方法正确性"
}}

**严格检查标准：**
- 如果图片与题目无关，is_correct必须为false
- 在error_analysis中必须明确说明："上传的图片与题目不符：图片显示的是[具体描述]，而题目要求解答的是[简述题目要求]"
- 如果无法识别图片内容，is_correct必须为false
- 不要因为学生上传了图片就默认他们回答了题目
- 宁可错杀，不可放过：宁可误判相关答案为错误，也不要把无关内容判定为正确

**常见无关图片示例：**
- 风景照片、自拍照、宠物照片
- 书本封面、笔记照片（非解题过程）
- 聊天截图、网页截图
- 空白纸、涂鸦线条
- 其他数学题目（非本题）
"""
        return prompt

    def _build_text_answer_analysis_prompt(self, question_text, correct_answer, answer_steps, student_text):
        """构建文字答案分析的提示词"""
        prompt = f"""
请分析学生的文字答题情况。

题目：{question_text}
标准答案：{correct_answer}
详细解题步骤：{answer_steps}
学生答案：{student_text}

请判断：
1. 学生的答案是否正确
2. 如果正确，答案的质量如何，是否按照标准解题步骤进行
3. 如果错误，分析错误原因，指出学生在哪个步骤出了问题
4. 给出学习建议和反馈，帮助学生掌握正确的解题方法

重要说明：
- 如果涉及数学公式，请使用LaTeX格式，例如：$x^2 + y^2 = r^2$，$$\\int_0^1 x^2 dx = \\frac{{1}}{{3}}$$
- 分数使用 $\\frac{{a}}{{b}}$ 格式
- 根号使用 $\\sqrt{{x}}$ 格式
- 求和使用 $\\sum$ 格式
- 积分使用 $\\int$ 格式
- 希腊字母使用 $\\alpha$, $\\beta$, $\\gamma$, $\\pi$, $\\sigma$, $\\theta$ 等格式
- 请根据标准解题步骤详细分析学生的解题思路和方法
- 如果学生跳过了重要步骤或方法不正确，请明确指出

请严格按照以下JSON格式返回：
{{
    "student_answer": "学生的答案（重述，含LaTeX格式数学公式）",
    "is_correct": true/false,
    "error_analysis": "错误原因分析（如果正确则为空，含LaTeX格式数学公式）",
    "feedback": "给学生反馈和建议（含LaTeX格式数学公式）",
    "solution_quality": "解题质量评价，包括步骤完整性和方法正确性"
}}
"""
        return prompt

    def _call_vllm_api(self, prompt, image_base64):
        """调用VL LLM API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=600  # 增加到600秒，因为VL LLM图片分析需要更长时间
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"VL LLM API调用失败: {str(e)}")

    def _call_vllm_api_with_two_images(self, prompt, question_base64, answer_base64):
        """调用VL LLM API - 支持两张图片（题目图片和学生答案图片）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{question_base64}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{answer_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=600  # 两张图片分析可能需要更长时间
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"VL LLM API调用失败: {str(e)}")

    def _call_vllm_text_api(self, prompt):
        """调用VL LLM API (纯文本模式)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120  # 纯文本分析时间较短
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"VL LLM文本API调用失败: {str(e)}")

    def _parse_analysis_response(self, response):
        """解析习题分析响应"""
        try:
            content = response['choices'][0]['message']['content']

            # 调试：打印原始响应内容
            print(f"=== VLLM Raw Response ===")
            print(f"Content length: {len(content)}")
            print(f"First 500 chars: {content[:500]}")
            print(f"Last 200 chars: {content[-200:]}")
            print(f"=== End VLLM Response ===")

            # 尝试多种方法提取JSON
            methods = [
                # 方法1: 直接查找第一个完整的JSON对象
                lambda: self._extract_first_json(content),
                # 方法2: 查找所有可能的JSON字符串
                lambda: self._extract_json_braces(content),
                # 方法3: 使用正则表达式查找JSON
                lambda: self._extract_json_regex(content)
            ]

            for method in methods:
                try:
                    result = method()
                    if result:
                        return result
                except:
                    continue

            # 如果所有方法都失败，返回默认结构
            return self._get_default_analysis_result()

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise Exception(f"响应解析失败: {str(e)}")

    def _extract_first_json(self, content):
        """提取第一个完整的JSON对象"""
        start = content.find('{')
        if start == -1:
            return None

        brace_count = 0
        in_string = False
        escape_next = False

        for i in range(start, len(content)):
            char = content[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = content[start:i+1]
                        return json.loads(json_str)

        return None

    def _extract_json_braces(self, content):
        """通过大括号匹配提取JSON"""
        import re
        # 匹配最外层的大括号
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
        return None

    def _extract_json_regex(self, content):
        """使用正则表达式提取JSON"""
        import re
        # 匹配可能的JSON结构
        patterns = [
            r'\{[\s\S]*?\}',  # 简单的JSON匹配
            r'```json\s*(\{[\s\S]*?\})\s*```',  # 代码块中的JSON
            r'```(\{[\s\S]*?\})```',  # 无标记的代码块
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
        return None

    def _get_default_analysis_result(self):
        """返回默认的分析结果"""
        return {
            "is_valid_question": False,
            "rejection_reason": "AI无法解析图片内容或图片不是学生错题",
            "subject": "数学",
            "grade_level": 6,
            "knowledge_points": ["基础运算"],
            "question_text": "无法解析题目内容",
            "difficulty": "medium",
            "answer_steps": "请重新上传清晰的题目图片",
            "correct_answer": "请重新上传",
            "title": "解析失败的题目",
            "new_knowledge_points": [],
            "new_exam_points": [],
            "student_solution": ""
        }

    def _parse_answer_analysis_response(self, response):
        """解析答案分析响应"""
        try:
            content = response['choices'][0]['message']['content']

            # 使用相同的JSON解析方法
            methods = [
                lambda: self._extract_first_json(content),
                lambda: self._extract_json_braces(content),
                lambda: self._extract_json_regex(content)
            ]

            for method in methods:
                try:
                    result = method()
                    if result:
                        return result
                except:
                    continue

            # 如果所有方法都失败，返回默认结构
            return self._get_default_answer_result()

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise Exception(f"答案分析响应解析失败: {str(e)}")

    def _get_default_answer_result(self):
        """返回默认的答案分析结果"""
        return {
            "student_answer": "无法识别答案",
            "is_correct": False,
            "error_analysis": "AI无法解析你的答案，请尝试重新拍照或输入文字",
            "feedback": "请确保答案清晰可读，建议在良好的光线下拍摄",
            "solution_quality": "无法评估"
        }

    def _process_knowledge_points(self, analysis_result, grade_level):
        """处理知识点和考点匹配和创建"""
        try:
            subject_name = analysis_result.get('subject', '数学')
            subject, _ = Subject.objects.get_or_create(name=subject_name)

            knowledge_point_objs = []
            exam_point_objs = []

            # 处理已有知识点
            for kp_name in analysis_result.get('knowledge_points', []):
                kp_obj, created = KnowledgePoint.objects.get_or_create(
                    name=kp_name,
                    subject=subject,
                    grade_level=grade_level,
                    defaults={'description': f'{subject_name} - {kp_name}'}
                )
                knowledge_point_objs.append(kp_obj)

            # 处理已有考点
            for ep_name in analysis_result.get('exam_points', []):
                # 需要先找到对应的知识点
                # 简化处理：假设考点名称格式为 "知识点-考点"
                if ' - ' in ep_name:
                    kp_name, actual_ep_name = ep_name.split(' - ', 1)
                    # 查找知识点
                    kp_obj = self._find_or_create_knowledge_point(kp_name, subject, grade_level)
                    # 创建或获取考点
                    ep_obj, created = ExamPoint.objects.get_or_create(
                        name=actual_ep_name,
                        knowledge_point=kp_obj,
                        subject=subject,
                        grade_level=grade_level,
                        defaults={'description': f'{subject_name} - {kp_name} - {actual_ep_name}'}
                    )
                    exam_point_objs.append(ep_obj)
                else:
                    # 如果没有分隔符，作为考点处理
                    ep_obj, created = ExamPoint.objects.get_or_create(
                        name=ep_name,
                        knowledge_point=knowledge_point_objs[0] if knowledge_point_objs else self._get_default_knowledge_point(subject, grade_level),
                        subject=subject,
                        grade_level=grade_level,
                        defaults={'description': f'{subject_name} - {ep_name}'}
                    )
                    exam_point_objs.append(ep_obj)

            # 处理新知识点
            for new_kp in analysis_result.get('new_knowledge_points', []):
                kp_obj, created = KnowledgePoint.objects.get_or_create(
                    name=new_kp['name'],
                    subject=subject,
                    grade_level=grade_level,
                    defaults={'description': new_kp.get('description', '')}
                )
                knowledge_point_objs.append(kp_obj)

            # 处理新考点
            for new_ep in analysis_result.get('new_exam_points', []):
                kp_name = new_ep.get('knowledge_point', '通用知识点')
                kp_obj = self._find_or_create_knowledge_point(kp_name, subject, grade_level)

                ep_obj, created = ExamPoint.objects.get_or_create(
                    name=new_ep['name'],
                    knowledge_point=kp_obj,
                    subject=subject,
                    grade_level=grade_level,
                    defaults={'description': new_ep.get('description', '')}
                )
                exam_point_objs.append(ep_obj)

            # 更新分析结果中的ID
            analysis_result['subject_id'] = subject.id
            analysis_result['knowledge_point_ids'] = [kp.id for kp in knowledge_point_objs]
            analysis_result['exam_point_ids'] = [ep.id for ep in exam_point_objs]

            return analysis_result

        except Exception as e:
            logger.error(f"知识点/考点处理失败: {str(e)}")
            raise Exception(f"知识点/考点处理失败: {str(e)}")

    def _find_or_create_knowledge_point(self, kp_name, subject, grade_level):
        """查找或创建知识点"""
        kp_obj, created = KnowledgePoint.objects.get_or_create(
            name=kp_name,
            subject=subject,
            grade_level=grade_level,
            defaults={'description': f'{subject.name} - {kp_name}'}
        )
        return kp_obj

    def _get_default_knowledge_point(self, subject, grade_level):
        """获取默认知识点"""
        kp_obj, created = KnowledgePoint.objects.get_or_create(
            name='通用知识点',
            subject=subject,
            grade_level=grade_level,
            defaults={'description': f'{subject.name} - 通用知识点'}
        )
        return kp_obj

    def analyze_question_from_text(self, question_text, grade_level):
        """从文本分析题目（用于批量上传）"""
        try:
            # 构建提示词
            prompt = self._build_question_analysis_prompt_for_text(question_text, grade_level)
            
            # 调用文本API
            response = self._call_vllm_text_api(prompt)
            
            # 解析响应
            analysis_result = self._parse_analysis_response(response)
            
            # 处理知识点和考点
            processed_result = self._process_knowledge_points(analysis_result, grade_level)
            
            return processed_result
            
        except Exception as e:
            logger.error(f"文本题目分析失败: {str(e)}")
            raise Exception(f"文本题目分析失败: {str(e)}")

    def _build_question_analysis_prompt_for_text(self, question_text, grade_level):
        """为文本题目构建分析提示词"""
        prompt = f"""
请分析以下题目，并按照指定格式返回分析结果。

题目内容：
{question_text}

年级：{grade_level}

请严格按照以下JSON格式返回分析结果：
{{
    "is_valid_question": true/false,
    "rejection_reason": "拒绝原因（如果不是有效题目）",
    "subject": "学科名称（如：数学、物理、化学、生物、语文、英语、历史、地理、政治）",
    "grade_level": {grade_level},
    "knowledge_points": ["知识点1", "知识点2"],
    "question_text": "完整的题目文本（如果是理科题目，数学公式请使用LaTeX格式，例如：$x^2 + y^2 = r^2$，$$\\int_0^1 x^2 dx = \\frac{{1}}{{3}}$$）",
    "difficulty": "easy/medium/hard",
    "answer_steps": "详细的解题步骤（如果是理科题目，数学公式请使用LaTeX格式）",
    "correct_answer": "正确答案（如果是理科题目，数学公式请使用LaTeX格式）",
    "title": "题目标题",
    "new_knowledge_points": [{{"name": "新知识点名称", "description": "描述"}}],
    "new_exam_points": [{{"name": "新考点名称", "knowledge_point": "对应知识点名称", "description": "描述"}}],
    "student_solution": "学生解题过程（如果有的话）"
}}

重要说明：
1. 如果是数学、物理、化学等理科题目，所有数学公式必须使用LaTeX格式：
   - 分数使用 $\\frac{{a}}{{b}}$ 格式
   - 根号使用 $\\sqrt{{x}}$ 格式
   - 求和使用 $\\sum$ 格式
   - 积分使用 $\\int$ 格式
   - 希腊字母使用 $\\alpha$, $\\beta$, $\\gamma$, $\\pi$, $\\sigma$, $\\theta$ 等格式
   - 上标使用 $x^2$，下标使用 $x_1$
   - 矩阵使用 $\\begin{{matrix}}...\\end{{matrix}}$ 格式

2. 请确保返回的是有效的JSON格式，可以被Python的json.loads()解析

3. 题目文本应该完整准确，包含所有必要的信息

4. 解题步骤应该详细清晰，便于学生理解

5. 如果是选择题，请在题目文本中包含所有选项

6. 请根据年级水平判断题目的难度等级

请分析这个题目并提供完整的分析结果。
"""
        return prompt

    def solve_question_from_text(self, question_text, subject_name, grade_level):
        """解答题目（用于批量解题）"""
        try:
            # 构建解答提示词
            prompt = self._build_question_solution_prompt(question_text, subject_name, grade_level)

            # 调用文本API
            response = self._call_vllm_text_api(prompt)

            # 解析响应
            content = response['choices'][0]['message']['content']

            # 尝试提取JSON格式的解答
            result = self._extract_first_json(content)
            if not result:
                result = self._extract_json_braces(content)
            if not result:
                result = self._extract_json_regex(content)

            # 如果无法提取JSON，创建默认结果
            if not result:
                result = {
                    "title": "未命名题目",  # 添加默认题目标题
                    "answer_steps": content,
                    "correct_answer": "请查看详细解答步骤",
                    "explanation": "详细解答见步骤说明"
                }

            return result

        except Exception as e:
            logger.error(f"题目解答失败: {str(e)}")
            raise Exception(f"题目解答失败: {str(e)}")

    def _build_question_solution_prompt(self, question_text, subject_name, grade_level):
        """构建题目解答提示词"""
        prompt = f"""
请解答以下题目，并提供详细的解题步骤和答案。

学科：{subject_name}
年级：{grade_level}
题目：
{question_text}

请提供：
1. 详细的解题步骤（逐步说明）
2. 最终答案
3. 解题思路的解释

重要说明：
- 如果是数学、物理、化学等理科题目，所有数学公式必须使用LaTeX格式
- 步骤要清晰详细，便于学生理解
- 答案要准确

请严格按照以下JSON格式返回：
{{
    "answer_steps": "详细的解题步骤（含LaTeX格式公式）",
    "title": "重新整理的简洁题目标题",
    "correct_answer": "最终答案（含LaTeX格式公式）",
    "explanation": "解题思路解释"
}}

开始解答：
"""
        return prompt
