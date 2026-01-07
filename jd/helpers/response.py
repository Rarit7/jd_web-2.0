"""API 响应辅助函数"""
from flask import jsonify
from typing import Any, Optional


def api_response(
    payload: Optional[Any] = None,
    err_code: int = 0,
    err_msg: str = '',
    status_code: int = 200
):
    """
    标准 API 响应格式

    Args:
        payload: 响应数据，可以是任意类型
        err_code: 错误代码（0=成功，>0=应用错误）
        err_msg: 错误消息
        status_code: HTTP 状态码

    Returns:
        Flask Response 对象
    """
    response = {
        'err_code': err_code,
        'err_msg': err_msg,
    }

    # 只有在 err_code 为 0 时才返回 payload
    if err_code == 0:
        response['payload'] = payload or {}
    else:
        response['payload'] = {}

    return jsonify(response), status_code
