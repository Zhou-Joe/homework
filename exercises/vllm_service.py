import requests
import json
import base64
import logging
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
你是一个专业的教育专家，请分析这道题目。请完成以下任务：

1. 识别题目内容和类型
2. 确定学科（数学、语文、英语等）
3. 进行三级分类识别：
   - 学科（一级）：如数学、语文、英语等
   - 知识点（二级）：如数列、函数、几何等
   - 考点（三级）：如递推数列、等差数列、二次函数等
4. 生成详细的解题步骤
5. 给出标准答案

已知知识点列表（二级分类）：
{kp_list}

已知考点列表（三级分类）：
{ep_list}

请严格按照以下JSON格式返回结果：
{{
    "subject": "学科名称",
    "grade_level": "题目适用的年级（小学1年级-小学6年级、初一-初三、高一-高三）",
    "knowledge_points": ["知识点1", "知识点2"],
    "exam_points": ["考点1", "考点2"],
    "question_text": "识别出的题目文本",
    "difficulty": "easy/medium/hard",
    "answer_steps": "详细的解题步骤",
    "correct_answer": "标准答案",
    "title": "题目标题",
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
- 年级必须是标准中国教育体系格式：小学1年级-小学6年级、初一-初三、高一-高三
- 难度必须是easy、medium、hard之一
- knowledge_points对应二级分类（知识点）
- exam_points对应三级分类（考点）
- 请优先匹配已有考点，如无匹配则创建新考点
- 如果图片中有学生的解答过程，请在student_solution字段中描述
- 如果发现新知识点或新考点，请在对应字段中列出
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
            "subject": "数学",
            "grade_level": 6,
            "knowledge_points": ["基础运算"],
            "question_text": "无法解析题目内容",
            "difficulty": "medium",
            "answer_steps": "请重新上传清晰的题目图片",
            "correct_answer": "请重新上传",
            "title": "解析失败的题目",
            "new_knowledge_points": [],
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
