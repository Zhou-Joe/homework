from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.conf import settings
import requests
import json
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    WechatLoginSerializer,
    WechatUserSerializer,
    WechatBindSerializer,
    UnifiedLoginSerializer
)


class RegisterView(generics.CreateAPIView):
    """用户注册视图"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        # 同时设置Django session认证
        login(request, user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """用户登录视图"""
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']
    refresh = RefreshToken.for_user(user)

    # 同时设置Django session认证
    login(request, user)

    return Response({
        'user': UserProfileSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def unified_login(request):
    """统一登录接口 - 支持密码登录和微信登录"""
    serializer = UnifiedLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    login_type = serializer.validated_data['login_type']

    try:
        if login_type == 'password':
            # 密码登录
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)
            if not user:
                return Response({
                    'error': '登录失败',
                    'message': '用户名或密码错误'
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not user.is_active:
                return Response({
                    'error': '登录失败',
                    'message': '用户账号已被禁用'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # 设置登录方式为密码登录
            user.login_way = 'password'
            user.save()

        elif login_type == 'wechat':
            # 微信登录
            code = serializer.validated_data['code']
            user_info = serializer.validated_data.get('user_info', {})

            # 调用微信API获取session_key和openid
            wechat_response = requests.get(
                f"https://api.weixin.qq.com/sns/jscode2session?appid={settings.WECHAT_APPID}&secret={settings.WECHAT_SECRET}&js_code={code}&grant_type=authorization_code"
            ).json()

            if 'errcode' in wechat_response:
                return Response({
                    'error': '微信授权失败',
                    'message': wechat_response.get('errmsg', '未知错误'),
                    'errcode': wechat_response.get('errcode')
                }, status=status.HTTP_400_BAD_REQUEST)

            openid = wechat_response.get('openid')
            session_key = wechat_response.get('session_key')
            unionid = wechat_response.get('unionid', '')

            if not openid:
                return Response({
                    'error': '微信授权失败',
                    'message': '未能获取有效的openid'
                }, status=status.HTTP_400_BAD_REQUEST)

            # 查找或创建用户
            User = get_user_model()
            try:
                user = User.objects.get(wechat_openid=openid)
                # 更新用户信息
                if user_info:
                    user.wechat_nickname = user_info.get('nickName', user.wechat_nickname)
                    user.wechat_avatar = user_info.get('avatarUrl', user.wechat_avatar)
                    user.save()
            except User.DoesNotExist:
                # 创建新用户
                user = User.objects.create_user(
                    username=f"wx_{openid[:20]}",  # 微信openID作为用户名
                    password='',  # 设置为空密码
                    wechat_openid=openid,
                    wechat_unionid=unionid,
                    wechat_nickname=user_info.get('nickName', f'微信用户_{openid[:8]}'),
                    wechat_avatar=user_info.get('avatarUrl', ''),
                    login_way='wechat',
                    is_active=True
                )
                # 设置不可用的密码，因为使用微信登录
                user.set_unusable_password()
                user.save()

        # 生成JWT token
        refresh = RefreshToken.for_user(user)

        # 根据登录方式选择序列化器
        if login_type == 'wechat':
            user_serializer = WechatUserSerializer(user)
        else:
            user_serializer = UserProfileSerializer(user)

        # 设置Django session认证
        login(request, user)

        return Response({
            'user': user_serializer.data,
            'login_type': login_type,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': '登录失败',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出视图"""
    try:
        # 清除Django session认证
        logout(request)

        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "登出成功"}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"message": "登出失败"}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """用户资料视图"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserProfileSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(ProfileView.serializer_class(instance).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    """获取当前用户信息"""
    user = request.user
    return Response(UserProfileSerializer(user).data)


# 微信小程序登录相关视图
@api_view(['POST'])
@permission_classes([AllowAny])
def wechat_login(request):
    """微信小程序登录"""
    serializer = WechatLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data['code']
    user_info = serializer.validated_data.get('user_info', {})

    try:
        # 调用微信API获取session_key和openid
        wechat_response = requests.get(
            f"https://api.weixin.qq.com/sns/jscode2session?appid={settings.WECHAT_APPID}&secret={settings.WECHAT_SECRET}&js_code={code}&grant_type=authorization_code"
        ).json()

        if 'errcode' in wechat_response:
            return Response({
                'error': '微信授权失败',
                'message': wechat_response.get('errmsg', '未知错误'),
                'errcode': wechat_response.get('errcode')
            }, status=status.HTTP_400_BAD_REQUEST)

        openid = wechat_response.get('openid')
        session_key = wechat_response.get('session_key')
        unionid = wechat_response.get('unionid', '')

        if not openid:
            return Response({
                'error': '微信授权失败',
                'message': '未能获取有效的openid'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 查找或创建用户
        User = get_user_model()
        try:
            user = User.objects.get(wechat_openid=openid)
            # 更新用户信息
            if user_info:
                user.wechat_nickname = user_info.get('nickName', user.wechat_nickname)
                user.wechat_avatar = user_info.get('avatarUrl', user.wechat_avatar)
                user.save()
        except User.DoesNotExist:
            # 创建新用户
            user = User.objects.create_user(
                username=f"wx_{openid[:20]}",  # 微信openID作为用户名
                password='',  # 设置为空密码
                wechat_openid=openid,
                wechat_unionid=unionid,
                wechat_nickname=user_info.get('nickName', f'微信用户_{openid[:8]}'),
                wechat_avatar=user_info.get('avatarUrl', ''),
                login_way='wechat',
                is_active=True
            )
            # 设置不可用的密码，因为使用微信登录
            user.set_unusable_password()
            user.save()

        # 生成JWT token
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': WechatUserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': '微信登录失败',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wechat_bind(request):
    """微信账号绑定"""
    user = request.user

    # 检查是否已经绑定
    if user.wechat_openid:
        return Response({
            'error': '账号已经绑定微信',
            'message': '该账号已绑定微信'
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = WechatBindSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data['code']

    try:
        # 调用微信API获取session_key和openid
        wechat_response = requests.get(
            f"https://api.weixin.qq.com/sns/jscode2session?appid={settings.WECHAT_APPID}&secret={settings.WECHAT_SECRET}&js_code={code}&grant_type=authorization_code"
        ).json()

        if 'errcode' in wechat_response:
            return Response({
                'error': '微信授权失败',
                'message': wechat_response.get('errmsg', '未知错误'),
                'errcode': wechat_response.get('errcode')
            }, status=status.HTTP_400_BAD_REQUEST)

        openid = wechat_response.get('openid')
        unionid = wechat_response.get('unionid', '')

        if not openid:
            return Response({
                'error': '微信授权失败',
                'message': '未能获取有效的openid'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查openid是否已被其他用户绑定
        if User.objects.filter(wechat_openid=openid).exclude(id=user.id).exists():
            return Response({
                'error': '微信已被绑定',
                'message': '该微信账号已被其他用户绑定'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 绑定微信信息
        user.wechat_openid = openid
        user.wechat_unionid = unionid
        user.login_way = 'wechat'
        user.save()

        return Response({
            'message': '微信账号绑定成功',
            'user': WechatUserSerializer(user).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': '微信绑定失败',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wechat_unbind(request):
    """解绑微信账号"""
    user = request.user

    if not user.wechat_openid:
        return Response({
            'error': '未绑定微信账号',
            'message': '该账号未绑定微信'
        }, status=status.HTTP_400_BAD_REQUEST)

    user.wechat_openid = ''
    user.wechat_unionid = ''
    user.wechat_nickname = ''
    user.wechat_avatar = ''
    user.save()

    return Response({
        'message': '微信账号解绑成功'
    }, status=status.HTTP_200_OK)
