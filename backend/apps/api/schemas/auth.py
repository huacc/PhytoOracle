"""
认证API Schema模型

功能：
- 定义认证相关的API请求和响应模型
- 用于管理员登录、API密钥管理等
- 遵循P1.1的OpenAPI规范定义

模型清单：
- LoginRequest: 登录请求Schema
- LoginResponse: 登录响应Schema
- TokenData: JWT Token数据Schema
"""

from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """
    登录请求Schema

    用于管理员登录接口的请求数据

    字段说明：
    - username: 用户名
    - password: 密码（明文，通过HTTPS传输）

    使用示例：
    ```python
    login_data = LoginRequest(
        username="admin",
        password="admin123"
    )
    ```

    注意：
    - 密码通过HTTPS加密传输
    - 后端使用bcrypt验证密码哈希
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名"
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=50,
        description="密码"
    )


class LoginResponse(BaseModel):
    """
    登录响应Schema

    用于管理员登录接口的响应数据

    字段说明：
    - access_token: JWT访问令牌
    - token_type: Token类型（默认：Bearer）
    - expires_in: Token过期时间（秒）
    - username: 用户名

    使用示例：
    ```python
    response = LoginResponse(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        token_type="Bearer",
        expires_in=604800,
        username="admin"
    )
    ```

    注意：
    - 客户端需要在后续请求中携带Token：Authorization: Bearer {access_token}
    - Token过期后需要重新登录
    """
    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = Field(default="Bearer", description="Token类型")
    expires_in: int = Field(..., description="Token过期时间（秒）")
    username: str = Field(..., description="用户名")


class TokenData(BaseModel):
    """
    JWT Token数据Schema

    用于JWT Token的payload数据

    字段说明：
    - username: 用户名
    - user_id: 用户ID（UUID）

    使用示例：
    ```python
    token_data = TokenData(
        username="admin",
        user_id="550e8400-e29b-41d4-a716-446655440000"
    )
    ```

    注意：
    - 此模型仅用于后端内部JWT编解码
    - 不直接暴露给API
    """
    username: str = Field(..., description="用户名")
    user_id: Optional[str] = Field(None, description="用户ID（UUID）")
