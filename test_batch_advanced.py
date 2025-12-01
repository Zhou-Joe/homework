#!/usr/bin/env python3
"""
测试新的高级批量上传功能
"""

import requests
import json
import base64
import os
from PIL import Image
import io

def create_test_image(text="测试题目\n1+1=？"):
    """创建测试图片"""
    from PIL import Image, ImageDraw, ImageFont
    
    # 创建白色背景图片
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # 尝试使用系统字体
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # 绘制文本
    draw.text((50, 50), text, fill='black', font=font)
    
    # 转换为base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return img_base64

def test_batch_analyze():
    """测试批量分析功能"""
    print("测试批量分析功能...")
    
    # 创建测试图片
    img1 = create_test_image("数学题目\n计算：2+3=？")
    img2 = create_test_image("物理题目\n一个物体从10米高处自由落下，求落地时间。")
    
    # 准备测试数据
    test_data = {
        "grade_level": "小学6年级"
    }
    
    # 注意：这里需要实际的图片文件，我们创建临时文件
    files = []
    
    # 创建临时图片文件
    for i, img_data in enumerate([img1, img2]):
        img = Image.open(io.BytesIO(base64.b64decode(img_data)))
        filename = f"test_image_{i+1}.png"
        img.save(filename)
        files.append(('images', open(filename, 'rb')))
    
    try:
        # 发送请求到本地服务器
        response = requests.post(
            'http://localhost:8000/api/analyze-batch-exercise-advanced/',
            data=test_data,
            files=files
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("批量分析成功！")
            print(f"总图片数: {result['summary']['total_images']}")
            print(f"有效题目: {result['summary']['valid_questions']}")
            print(f"成功率: {result['summary']['success_rate']}%")
            
            # 显示详细结果
            for i, analysis in enumerate(result['batch_analysis']['results']):
                print(f"\n图片 {i+1}: {analysis['file_name']}")
                print(f"  有效: {analysis['is_valid_question']}")
                if analysis['is_valid_question']:
                    print(f"  标题: {analysis['title']}")
                    print(f"  学科: {analysis['subject']}")
                    print(f"  知识点: {', '.join(analysis['knowledge_points'])}")
            
            return result
        else:
            print(f"批量分析失败: {response.text}")
            return None
            
    finally:
        # 清理临时文件
        for _, file_obj in files:
            file_obj.close()
            filename = file_obj.name
            if os.path.exists(filename):
                os.remove(filename)

def test_batch_save():
    """测试批量保存功能"""
    print("\n测试批量保存功能...")
    
    # 模拟分析结果
    mock_analysis = {
        "batch_analysis": {
            "results": [
                {
                    "file_name": "test1.png",
                    "is_valid_question": True,
                    "title": "数学计算题",
                    "question_text": "计算：2+3=？",
                    "subject": "数学",
                    "grade_level": 6,
                    "difficulty": "easy",
                    "knowledge_points": ["加法运算"],
                    "exam_points": ["基础计算"]
                },
                {
                    "file_name": "test2.png", 
                    "is_valid_question": True,
                    "title": "物理应用题",
                    "question_text": "一个物体从10米高处自由落下，求落地时间。",
                    "subject": "物理",
                    "grade_level": 9,
                    "difficulty": "medium",
                    "knowledge_points": ["自由落体", "重力加速度"],
                    "exam_points": ["运动学"]
                }
            ]
        }
    }
    
    # 创建一个会话以处理认证
    session = requests.Session()
    
    # 首先尝试登录（假设我们有测试账户）
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    login_response = session.post('http://localhost:8000/login/', data=login_data)
    
    if login_response.status_code != 200:
        print("登录失败，尝试匿名访问...")
        session = requests.Session()
    
    response = session.post(
        'http://localhost:8000/api/save-batch-exercise-advanced/',
        json=mock_analysis,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text[:200]}...")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print("批量保存成功！")
            print(f"保存数量: {result['saved_count']}")
            print(f"失败数量: {result['failed_count']}")
            
            if result['saved_exercises']:
                print("保存的题目:")
                for exercise in result['saved_exercises']:
                    print(f"  - {exercise['title']} (ID: {exercise['exercise_id']})")
            
            return result
        except Exception as e:
            print(f"解析JSON失败: {e}")
            return None
    else:
        print(f"批量保存失败: {response.text}")
        return None

def test_batch_solve():
    """测试批量解题功能"""
    print("\n测试批量解题功能...")
    
    # 创建一个会话以处理认证
    session = requests.Session()
    
    # 首先尝试登录
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    login_response = session.post('http://localhost:8000/login/', data=login_data)
    
    # 首先获取未解决的题目
    response = session.get('http://localhost:8000/api/get-unsolved-exercises/')
    
    if response.status_code == 200:
        result = response.json()
        exercises = result.get('exercises', [])
        
        if not exercises:
            print("没有未解决的题目")
            return
        
        # 选择前2个题目进行测试
        exercise_ids = [ex['id'] for ex in exercises[:2]]
        print(f"选择题目ID进行解题: {exercise_ids}")
        
        data = {
            "exercise_ids": exercise_ids
        }
        
        response = session.post(
            'http://localhost:8000/api/solve-exercise-batch-advanced/',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("批量解题成功！")
                print(f"解题数量: {result['solved_count']}")
                print(f"失败数量: {result['failed_count']}")
                print(f"成功率: {result['success_rate']}%")
                
                return result
            except Exception as e:
                print(f"解析JSON失败: {e}")
                return None
        else:
            print(f"批量解题失败: {response.text}")
            return None
    else:
        print(f"获取未解决题目失败: {response.text}")
        return None

if __name__ == "__main__":
    print("=== 测试高级批量上传功能 ===\n")
    
    # 测试批量分析
    # analysis_result = test_batch_analyze()
    
    # 测试批量保存
    save_result = test_batch_save()
    
    # 测试批量解题
    solve_result = test_batch_solve()
    
    print("\n=== 测试完成 ===")