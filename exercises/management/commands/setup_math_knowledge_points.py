from django.core.management.base import BaseCommand
from exercises.models import Subject, KnowledgePoint


class Command(BaseCommand):
    help = 'Setup comprehensive math knowledge points from elementary to high school'

    def handle(self, *args, **options):
        self.stdout.write('Setting up comprehensive math knowledge points...')

        # 获取数学学科
        math_subject = Subject.objects.get_or_create(
            name='数学',
            defaults={'description': '数学学科'}
        )[0]

        # 定义完整的数学知识点体系
        math_knowledge_points = [
            # 小学阶段 (1-6年级)
            # 1年级
            {"name": "数与代数-认识数字", "grade_level": 1, "description": "认识0-100的数字，数字的读写和大小比较"},
            {"name": "数与代数-10以内加减法", "grade_level": 1, "description": "10以内的加法和减法运算"},
            {"name": "数与代数-20以内加减法", "grade_level": 1, "description": "20以内的加减法运算，包括进位加法"},
            {"name": "几何图形-认识图形", "grade_level": 1, "description": "认识长方形、正方形、圆形、三角形等基本图形"},

            # 2年级
            {"name": "数与代数-100以内加减法", "grade_level": 2, "description": "100以内加减法，包括两位数加减法"},
            {"name": "数与代数-表内乘法", "grade_level": 2, "description": "乘法口诀表，表内乘法运算"},
            {"name": "数与代数-除法初步", "grade_level": 2, "description": "除法的初步认识，平均分"},
            {"name": "几何图形-长度单位", "grade_level": 2, "description": "厘米、米的认识和换算"},

            # 3年级
            {"name": "数与代数-万以内加减法", "grade_level": 3, "description": "万以内加减法，三位数加减法"},
            {"name": "数与代数-多位数乘法", "grade_level": 3, "description": "两位数乘两位数，三位数乘两位数"},
            {"name": "数与代数-分数初步", "grade_level": 3, "description": "分数的初步认识，简单分数的大小比较"},
            {"name": "数与代数-小数初步", "grade_level": 3, "description": "小数的初步认识，一位小数"},
            {"name": "几何图形-面积", "grade_level": 3, "description": "长方形和正方形的面积计算"},

            # 4年级
            {"name": "数与代数-大数认识", "grade_level": 4, "description": "亿以内数的认识和读写"},
            {"name": "数与代数-三位数乘除法", "grade_level": 4, "description": "三位数乘两位数，除数是两位数的除法"},
            {"name": "数与代数-运算定律", "grade_level": 4, "description": "加法交换律、结合律，乘法分配律"},
            {"name": "数与代数-小数加减法", "grade_level": 4, "description": "小数加减法，小数的性质"},
            {"name": "几何图形-角的认识", "grade_level": 4, "description": "角的度量，直角、锐角、钝角"},
            {"name": "几何图形-平行四边形和梯形", "grade_level": 4, "description": "平行四边形和梯形的认识"},

            # 5年级
            {"name": "数与代数-小数乘除法", "grade_level": 5, "description": "小数乘除法运算"},
            {"name": "数与代数-简易方程", "grade_level": 5, "description": "用字母表示数，简易方程"},
            {"name": "数与代数-因数倍数", "grade_level": 5, "description": "因数和倍数，质数和合数"},
            {"name": "数与代数-分数意义", "grade_level": 5, "description": "分数的意义和基本性质"},
            {"name": "数与代数-分数加减法", "grade_level": 5, "description": "异分母分数加减法"},
            {"name": "几何图形-长方体正方体", "grade_level": 5, "description": "长方体和正方体的认识，表面积和体积"},

            # 6年级
            {"name": "数与代数-分数乘除法", "grade_level": 6, "description": "分数乘除法运算"},
            {"name": "数与代数-比和比例", "grade_level": 6, "description": "比的意义和基本性质，比例"},
            {"name": "数与代数-百分数", "grade_level": 6, "description": "百分数的意义和应用"},
            {"name": "数与代数-负数", "grade_level": 6, "description": "负数的初步认识"},
            {"name": "几何图形-圆", "grade_level": 6, "description": "圆的周长和面积"},
            {"name": "几何图形-圆柱圆锥", "grade_level": 6, "description": "圆柱和圆锥的认识，表面积和体积"},
            {"name": "统计与概率-扇形统计图", "grade_level": 6, "description": "扇形统计图的认识和应用"},

            # 初中阶段 (7-9年级)
            # 7年级 (初一)
            {"name": "有理数-正负数", "grade_level": 7, "description": "正数和负数的概念，数轴"},
            {"name": "有理数-有理数运算", "grade_level": 7, "description": "有理数的加减乘除乘方运算"},
            {"name": "代数式-整式", "grade_level": 7, "description": "整式及其加减法"},
            {"name": "代数式-整式乘除", "grade_level": 7, "description": "整式的乘法和除法"},
            {"name": "一元一次方程-解法", "grade_level": 7, "description": "一元一次方程的解法"},
            {"name": "一元一次方程-应用", "grade_level": 7, "description": "一元一次方程的应用题"},
            {"name": "几何图形-基本图形", "grade_level": 7, "description": "点、线、面、角的基本概念"},
            {"name": "几何图形-相交线平行线", "grade_level": 7, "description": "相交线和平行线的性质和判定"},

            # 8年级 (初二)
            {"name": "二次根式", "grade_level": 8, "description": "二次根式的概念和运算"},
            {"name": "一元二次方程", "grade_level": 8, "description": "一元二次方程的解法：公式法、因式分解法"},
            {"name": "函数-一次函数", "grade_level": 8, "description": "一次函数的概念、图像和性质"},
            {"name": "函数-反比例函数", "grade_level": 8, "description": "反比例函数的概念、图像和性质"},
            {"name": "几何图形-全等三角形", "grade_level": 8, "description": "全等三角形的判定和性质"},
            {"name": "几何图形-轴对称", "grade_level": 8, "description": "轴对称图形的概念和性质"},
            {"name": "几何图形-勾股定理", "grade_level": 8, "description": "勾股定理及其逆定理"},
            {"name": "几何图形-四边形", "grade_level": 8, "description": "平行四边形、矩形、菱形、正方形的性质"},
            {"name": "统计与概率-数据分析", "grade_level": 8, "description": "数据的收集、整理和分析，平均数、中位数、众数"},

            # 9年级 (初三)
            {"name": "二次函数", "grade_level": 9, "description": "二次函数的概念、图像和性质"},
            {"name": "函数-抛物线", "grade_level": 9, "description": "抛物线的性质，顶点、对称轴、开口方向"},
            {"name": "圆-基本性质", "grade_level": 9, "description": "圆的基本性质，圆心角、圆周角"},
            {"name": "圆-位置关系", "grade_level": 9, "description": "点与圆、直线与圆、圆与圆的位置关系"},
            {"name": "圆-切线", "grade_level": 9, "description": "圆的切线性质和判定"},
            {"name": "几何图形-相似三角形", "grade_level": 9, "description": "相似三角形的判定和性质"},
            {"name": "几何图形-旋转", "grade_level": 9, "description": "图形的旋转和中心对称"},
            {"name": "统计与概率-概率初步", "grade_level": 9, "description": "概率的初步认识和计算"},
            {"name": "几何图形-解直角三角形", "grade_level": 9, "description": "锐角三角函数，解直角三角形"},

            # 高中阶段 (10-12年级)
            # 10年级 (高一)
            {"name": "集合-基本概念", "grade_level": 10, "description": "集合的概念、表示方法和基本运算"},
            {"name": "函数-函数概念", "grade_level": 10, "description": "函数的定义、定义域、值域"},
            {"name": "函数-基本性质", "grade_level": 10, "description": "函数的单调性、奇偶性"},
            {"name": "函数-基本初等函数I", "grade_level": 10, "description": "指数函数和对数函数"},
            {"name": "函数-基本初等函数II", "grade_level": 10, "description": "幂函数、三角函数"},
            {"name": "函数-函数应用", "grade_level": 10, "description": "函数与方程，函数模型及其应用"},
            {"name": "立体几何-空间几何体", "grade_level": 10, "description": "空间几何体的结构特征和三视图"},
            {"name": "立体几何-点线面关系", "grade_level": 10, "description": "空间点、直线、平面之间的位置关系"},
            {"name": "立体几何-空间向量", "grade_level": 10, "description": "空间向量及其运算"},
            {"name": "解析几何-直线方程", "grade_level": 10, "description": "直线的倾斜角、斜率、方程"},
            {"name": "解析几何-圆的方程", "grade_level": 10, "description": "圆的标准方程和一般方程"},
            {"name": "数列-等差数列", "grade_level": 10, "description": "等差数列的概念、通项公式、前n项和"},
            {"name": "数列-等比数列", "grade_level": 10, "description": "等比数列的概念、通项公式、前n项和"},
            {"name": "不等式-基本性质", "grade_level": 10, "description": "不等式的基本性质和均值不等式"},
            {"name": "不等式-线性规划", "grade_level": 10, "description": "简单的线性规划问题"},

            # 11年级 (高二)
            {"name": "三角函数-任意角三角函数", "grade_level": 11, "description": "任意角的三角函数定义和诱导公式"},
            {"name": "三角函数-三角恒等变换", "grade_level": 11, "description": "三角函数的和差倍半公式"},
            {"name": "三角函数-解三角形", "grade_level": 11, "description": "正弦定理、余弦定理及其应用"},
            {"name": "平面向量-基本概念", "grade_level": 11, "description": "向量的概念、线性运算、坐标表示"},
            {"name": "平面向量-数量积", "grade_level": 11, "description": "平面向量的数量积及其应用"},
            {"name": "数列-数列综合", "grade_level": 11, "description": "数列的综合应用，数列求和的技巧"},
            {"name": "不等式-不等式解法", "grade_level": 11, "description": "一元二次不等式、分式不等式、含绝对值不等式"},
            {"name": "概率-古典概型", "grade_level": 11, "description": "古典概型，几何概型"},
            {"name": "统计-随机变量", "grade_level": 11, "description": "离散型随机变量及其分布列"},
            {"name": "统计-二项分布", "grade_level": 11, "description": "二项分布及其应用"},
            {"name": "统计-正态分布", "grade_level": 11, "description": "正态分布及其应用"},

            # 12年级 (高三)
            {"name": "导数-导数概念", "grade_level": 12, "description": "导数的定义、几何意义、物理意义"},
            {"name": "导数-导数计算", "grade_level": 12, "description": "基本初等函数的导数，导数的四则运算"},
            {"name": "导数-导数应用", "grade_level": 12, "description": "利用导数研究函数的单调性、极值、最值"},
            {"name": "导数-优化问题", "grade_level": 12, "description": "利用导数解决实际优化问题"},
            {"name": "积分-定积分概念", "grade_level": 12, "description": "定积分的定义、几何意义、基本性质"},
            {"name": "积分-微积分基本定理", "grade_level": 12, "description": "微积分基本定理，不定积分"},
            {"name": "积分-定积分应用", "grade_level": 12, "description": "定积分在几何和物理中的应用"},
            {"name": "计数原理-分类计数原理", "grade_level": 12, "description": "分类计数原理与分步计数原理"},
            {"name": "计数原理-排列组合", "grade_level": 12, "description": "排列、组合的概念、公式和应用"},
            {"name": "计数原理-二项式定理", "grade_level": 12, "description": "二项式定理及其应用"},
            {"name": "概率-条件概率", "grade_level": 12, "description": "条件概率，事件的独立性"},
            {"name": "概率-离散型随机变量", "grade_level": 12, "description": "离散型随机变量的分布列、期望、方差"},
            {"name": "概率-连续型随机变量", "grade_level": 12, "description": "连续型随机变量的概率密度、期望、方差"},
            {"name": "统计-假设检验", "grade_level": 12, "description": "基本的假设检验方法"},
            {"name": "几何证明-立体几何综合", "grade_level": 12, "description": "立体几何的综合证明问题"},
            {"name": "几何证明-解析几何综合", "grade_level": 12, "description": "解析几何的综合证明问题"},
            {"name": "代数综合-函数与导数", "grade_level": 12, "description": "函数与导数的综合问题"},
            {"name": "代数综合-数列与不等式", "grade_level": 12, "description": "数列与不等式的综合问题"},

            # 特殊专题
            {"name": "数学思想-分类讨论", "grade_level": 12, "description": "分类讨论思想方法"},
            {"name": "数学思想-数形结合", "grade_level": 12, "description": "数形结合思想方法"},
            {"name": "数学思想-转化与化归", "grade_level": 12, "description": "转化与化归思想方法"},
            {"name": "数学思想-函数与方程", "grade_level": 12, "description": "函数与方程思想方法"},
        ]

        created_count = 0
        updated_count = 0

        for kp_data in math_knowledge_points:
            kp, created = KnowledgePoint.objects.get_or_create(
                subject=math_subject,
                name=kp_data["name"],
                defaults={
                    'grade_level': kp_data["grade_level"],
                    'description': kp_data["description"]
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'Created: {kp.grade_level}年级 - {kp.name}')
            else:
                # 更新现有知识点
                kp.grade_level = kp_data["grade_level"]
                kp.description = kp_data["description"]
                kp.save()
                updated_count += 1
                self.stdout.write(f'Updated: {kp.grade_level}年级 - {kp.name}')

        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed {created_count} new and {updated_count} updated math knowledge points!'
        ))