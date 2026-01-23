"""
配置加载工具类
用于加载和管理环境变量配置
"""

import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """配置加载器"""

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            env_file: 环境变量文件路径，默认为项目根目录下的 .env 文件
        """
        # 加载环境变量
        if env_file:
            load_dotenv(env_file)
        else:
            # 尝试加载项目根目录下的 .env 文件
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env_path = os.path.join(project_root, '.env')
            load_dotenv(env_path)

    @property
    def zentao_base_url(self) -> str:
        """获取禅道基础URL"""
        return os.getenv('ZENTAO_BASE_URL', 'https://zentao.example.com/zentao/')

    @property
    def zentao_account(self) -> str:
        """获取禅道账号"""
        account = os.getenv('ZENTAO_ACCOUNT')
        if not account:
            raise ValueError("环境变量 ZENTAO_ACCOUNT 未设置")
        return account

    @property
    def zentao_password(self) -> str:
        """获取禅道密码"""
        password = os.getenv('ZENTAO_PASSWORD')
        if not password:
            raise ValueError("环境变量 ZENTAO_PASSWORD 未设置")
        return password

    @property
    def llm_api_key(self) -> str:
        """获取LLM API密钥"""
        return os.getenv('LLM_API_KEY', '')

    @property
    def llm_api_base(self) -> str:
        """获取LLM API基础URL"""
        return os.getenv('LLM_API_BASE', 'https://api.openai.com/v1')

    @property
    def llm_model(self) -> str:
        """获取LLM模型名称"""
        return os.getenv('LLM_MODEL', 'gpt-4')

    @property
    def llm_temperature(self) -> float:
        """获取LLM温度参数"""
        return float(os.getenv('LLM_TEMPERATURE', '0.3'))


# 创建全局配置实例
config = Config()
