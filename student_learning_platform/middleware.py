"""
自定义中间件 - 用于调试和日志记录
"""
import logging
import traceback
from django.http import HttpResponse

logger = logging.getLogger(__name__)


class DebugMediaMiddleware:
    """调试媒体文件服务的中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 记录媒体文件请求
        if request.path.startswith('/media/'):
            logger.info(f"Media request: {request.method} {request.path}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"Origin: {request.META.get('HTTP_ORIGIN', 'None')}")
        
        response = self.get_response(request)
        
        # 记录响应状态
        if request.path.startswith('/media/'):
            logger.info(f"Media response status: {response.status_code}")
            if response.status_code >= 400:
                logger.error(f"Media error: {response.status_code} - {response}")
        
        return response


class CorsDebugMiddleware:
    """CORS调试中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 处理OPTIONS预检请求
        if request.method == 'OPTIONS':
            logger.info(f"CORS preflight: {request.path}")
            logger.info(f"Access-Control-Request-Headers: {request.META.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS')}")
        
        response = self.get_response(request)
        
        # 添加CORS头
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, Accept, Origin, X-Requested-With'
            response['Access-Control-Expose-Headers'] = '*'
        
        if request.path.startswith('/media/'):
            logger.info(f"CORS headers added for: {request.path}")
        
        return response
