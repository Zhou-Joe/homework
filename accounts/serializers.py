from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    # 创建自定义的年级字段，接受数字并转换为对应的字符串
    grade_level = serializers.CharField()

    class Meta:
        model = User
        fields = ('username', 'password', 'password_confirm', 'nickname', 'birth_date', 'grade_level', 'email')
        extra_kwargs = {
            'email': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码不匹配")
        return attrs

    def validate_grade_level(self, value):
        # 处理前端传递的数字值，转换为对应的年级字符串
        grade_mapping = {
            '1': '小学1年级', '2': '小学2年级', '3': '小学3年级',
            '4': '小学4年级', '5': '小学5年级', '6': '小学6年级',
            '7': '初一', '8': '初二', '9': '初三',
            '10': '高一', '11': '高二', '12': '高三',
        }
        
        # 去除可能的空格
        value = str(value).strip()
        
        if value in grade_mapping:
            return grade_mapping[value]
        
        # 如果已经是正确的字符串格式，直接返回
        valid_grades = [choice[0] for choice in User._meta.get_field('grade_level').choices]
        if value in valid_grades:
            return value
            
        raise serializers.ValidationError("年级无效，请选择1-12之间的数字")

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('用户名或密码错误')
            if not user.is_active:
                raise serializers.ValidationError('用户账号已被禁用')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('用户名和密码都是必填项')


class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'nickname', 'email', 'birth_date', 'grade_level', 'user_type', 'created_at')
        read_only_fields = ('id', 'username', 'user_type', 'created_at')


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器"""
    class Meta:
        model = User
        fields = ('nickname', 'email', 'birth_date', 'grade_level')
        extra_kwargs = {
            'email': {'required': False}
        }

    def validate_grade_level(self, value):
        # 如果是数字，转换为对应的年级字符串
        grade_mapping = {
            '1': '小学1年级', '2': '小学2年级', '3': '小学3年级',
            '4': '小学4年级', '5': '小学5年级', '6': '小学6年级',
            '7': '初一', '8': '初二', '9': '初三',
            '10': '高一', '11': '高二', '12': '高三',
            1: '小学1年级', 2: '小学2年级', 3: '小学3年级',
            4: '小学4年级', 5: '小学5年级', 6: '小学6年级',
            7: '初一', 8: '初二', 9: '初三',
            10: '高一', 11: '高二', 12: '高三',
        }
        
        if value in grade_mapping:
            return grade_mapping[value]
        
        # 如果已经是正确的字符串格式，直接返回
        valid_grades = [choice[0] for choice in User._meta.get_field('grade_level').choices]
        if value in valid_grades:
            return value
            
        raise serializers.ValidationError("年级无效")


class WechatLoginSerializer(serializers.Serializer):
    """微信登录序列化器"""
    code = serializers.CharField(max_length=100, write_only=True)
    user_info = serializers.DictField(write_only=True, required=False)

    def validate(self, attrs):
        code = attrs.get('code')
        if not code:
            raise serializers.ValidationError('微信授权码不能为空')
        return attrs


class WechatUserSerializer(serializers.ModelSerializer):
    """微信用户信息序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'wechat_nickname', 'wechat_avatar', 'wechat_unionid', 'login_way', 'user_type', 'created_at')
        read_only_fields = ('id', 'username', 'login_way', 'user_type', 'created_at')


class WechatBindSerializer(serializers.Serializer):
    """微信绑定序列化器"""
    code = serializers.CharField(max_length=100, write_only=True)
    password = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        code = attrs.get('code')
        if not code:
            raise serializers.ValidationError('微信授权码不能为空')
        return attrs


class UnifiedLoginSerializer(serializers.Serializer):
    """统一登录序列化器 - 支持密码登录和微信登录"""
    login_type = serializers.ChoiceField(choices=['password', 'wechat'], required=True)

    # 密码登录字段
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)

    # 微信登录字段
    code = serializers.CharField(required=False)
    user_info = serializers.DictField(required=False)

    def validate(self, attrs):
        login_type = attrs.get('login_type')

        if login_type == 'password':
            username = attrs.get('username')
            password = attrs.get('password')
            if not username or not password:
                raise serializers.ValidationError('密码登录需要用户名和密码')
        elif login_type == 'wechat':
            code = attrs.get('code')
            if not code:
                raise serializers.ValidationError('微信登录需要授权码')

        return attrs
