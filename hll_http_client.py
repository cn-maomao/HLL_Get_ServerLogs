#!/usr/bin/env python3
"""
HLL RCON HTTP客户端
基于发现的API v2端点实现，优化版本
"""

import requests
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HLLHttpClient:
    """HLL RCON HTTP客户端 - 优化版本"""
    
    def __init__(self, host: str, port: int, password: str, api_host: str = None, api_port: int = None, api_config: Dict[str, Any] = None):
        """
        初始化HTTP客户端
        
        Args:
            host: HLL服务器地址
            port: HLL服务器RCON端口
            password: RCON密码
            api_host: API服务器地址（可选，优先级高于api_config）
            api_port: API服务器端口（可选，优先级高于api_config）
            api_config: API配置字典（包含default_host, default_port等）
        """
        self.host = host
        self.port = port
        self.password = password
        
        # 确定API服务器地址和端口
        if api_host and api_port:
            # 直接指定的参数优先级最高
            self.api_host = api_host
            self.api_port = api_port
        elif api_config:
            # 使用配置文件中的默认值
            self.api_host = api_config.get('default_host', '192.168.1.14')
            self.api_port = api_config.get('default_port', 17080)
        else:
            # 使用硬编码的默认值
            self.api_host = '192.168.1.14'
            self.api_port = 17080
            
        self.api_base_url = f"http://{self.api_host}:{self.api_port}"
        
        # 创建优化的会话
        self.session = self._create_optimized_session()
        self.session_id: Optional[str] = None
        self.connected = False
        self.last_used = None
        self.connection_cache_time = None
        self.connection_cache_duration = 30  # 连接状态缓存30秒
        
        # 设置日志
        self.logger = logging.getLogger(f"HLLHttpClient-{host}:{port}")
        
        # 设置请求超时
        self.timeout = (10, 30)  # (连接超时, 读取超时)
        
        # 性能统计
        self.stats = {
            'requests_sent': 0,
            'requests_failed': 0,
            'connection_attempts': 0,
            'connection_failures': 0
        }
        
    def _create_optimized_session(self) -> requests.Session:
        """创建优化的HTTP会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 总重试次数
            backoff_factor=0.5,  # 退避因子
            status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
            allowed_methods=["HEAD", "GET", "POST"]  # 允许重试的方法
        )
        
        # 配置HTTP适配器
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # 连接池大小
            pool_maxsize=20,  # 最大连接数
            pool_block=False  # 非阻塞模式
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认头部
        session.headers.update({
            'User-Agent': 'HLL-Log-Collector/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'
        })
        
        return session
        
    def connect(self) -> bool:
        """连接到HLL服务器"""
        try:
            self.stats['connection_attempts'] += 1
            self.logger.info(f"尝试连接到 {self.host}:{self.port}")
            
            response = self.session.post(
                f"{self.api_base_url}/api/v2/connect",
                json={
                    'host': self.host,
                    'port': self.port,
                    'password': self.password
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                # 检查是否有session_id，表示连接成功
                if 'session_id' in result:
                    self.session_id = result.get('session_id')
                    self.connected = True
                    self.last_used = datetime.now()
                    self.connection_cache_time = datetime.now()
                    self.logger.info(f"连接成功，会话ID: {self.session_id}")
                    return True
            
            self.stats['connection_failures'] += 1
            self.logger.error(f"连接失败: {response.text}")
            return False
            
        except Exception as e:
            self.stats['connection_failures'] += 1
            self.logger.error(f"连接异常: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开连接"""
        try:
            if not self.connected:
                return True
                
            response = self.session.post(
                f"{self.api_base_url}/api/v2/disconnect",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.connected = False
                self.session_id = None
                self.connection_cache_time = None
                self.logger.info("断开连接成功")
                return True
            else:
                self.logger.warning(f"断开连接失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"断开连接异常: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查连接状态（带缓存优化）"""
        # 如果有缓存且未过期，直接返回缓存结果
        if (self.connection_cache_time and 
            datetime.now() - self.connection_cache_time < timedelta(seconds=self.connection_cache_duration)):
            return self.connected
            
        try:
            response = self.session.get(
                f"{self.api_base_url}/api/v2/connection/status",
                timeout=(5, 10)  # 快速检查
            )
            
            if response.status_code == 200:
                data = response.json()
                self.connected = data.get("connected", False)
                self.connection_cache_time = datetime.now()
                return self.connected
            else:
                self.connected = False
                self.connection_cache_time = datetime.now()
                return False
                
        except Exception as e:
            self.logger.error(f"检查连接状态异常: {e}")
            self.connected = False
            self.connection_cache_time = datetime.now()
            return False
    
    def ensure_connection(self) -> bool:
        """确保连接有效（优化版本）"""
        if not self.is_connected():
            self.logger.info("连接已断开，尝试重新连接")
            return self.connect()
        return True
    
    def send_command(self, command: str, **params) -> Optional[str]:
        """
        发送RCON命令（优化版本）
        
        Args:
            command: 命令名称
            **params: 命令参数
            
        Returns:
            命令响应或None
        """
        try:
            self.stats['requests_sent'] += 1
            
            if not self.ensure_connection():
                self.logger.error("无法建立连接")
                self.stats['requests_failed'] += 1
                return None
            
            # 构建请求URL
            url = f"{self.api_base_url}/api/v2/command/{command}"
            
            # 发送请求
            if params:
                response = self.session.post(url, json=params, timeout=self.timeout)
            else:
                response = self.session.get(url, timeout=self.timeout)
            
            self.last_used = datetime.now()
            
            if response.status_code == 200:
                return response.text
            else:
                self.logger.error(f"命令执行失败: {command}, 状态码: {response.status_code}")
                self.stats['requests_failed'] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"发送命令异常: {command}, 错误: {e}")
            self.stats['requests_failed'] += 1
            return None
    
    def get_admin_logs(self, seconds: int = 300) -> Optional[List[Dict[str, Any]]]:
        """
        获取管理员日志（优化版本）
        
        Args:
            seconds: 获取最近几秒的日志
            
        Returns:
            日志列表或None
        """
        try:
            self.stats['requests_sent'] += 1
            
            if not self.ensure_connection():
                self.logger.error("无法建立连接")
                self.stats['requests_failed'] += 1
                return None
            
            # 使用发现的正确端点
            response = self.session.get(
                f"{self.api_base_url}/api/v2/logs?seconds={seconds}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.last_used = datetime.now()
                data = response.json()
                if 'entries' in data:
                    self.logger.debug(f"获取到 {len(data['entries'])} 条日志")
                    return data['entries']
                else:
                    self.logger.warning("响应中没有找到日志条目")
                    return []
            else:
                self.logger.error(f"获取日志失败: {response.status_code} - {response.text}")
                self.stats['requests_failed'] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"获取管理员日志异常: {e}")
            self.stats['requests_failed'] += 1
            return None
    
    def _get_admin_log_via_command(self, seconds: int) -> Optional[List[str]]:
        """通过命令获取管理员日志（备用方法）"""
        try:
            response = self.send_command("showlog", seconds=seconds)
            if response:
                # 解析日志响应
                lines = response.strip().split('\n')
                return [line for line in lines if line.strip()]
            return None
        except Exception as e:
            self.logger.error(f"通过命令获取日志异常: {e}")
            return None
    
    def get_players(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取玩家列表（优化版本）
        
        Returns:
            玩家列表或None
        """
        try:
            self.stats['requests_sent'] += 1
            
            if not self.ensure_connection():
                self.logger.error("无法建立连接")
                self.stats['requests_failed'] += 1
                return None
            
            response = self.session.get(
                f"{self.api_base_url}/api/v2/players",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.last_used = datetime.now()
                data = response.json()
                return data.get('players', [])
            else:
                self.logger.error(f"获取玩家列表失败: {response.status_code}")
                self.stats['requests_failed'] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"获取玩家列表异常: {e}")
            self.stats['requests_failed'] += 1
            return None
    
    def get_commands(self) -> Optional[List[str]]:
        """
        获取可用命令列表（优化版本）
        
        Returns:
            命令列表或None
        """
        try:
            self.stats['requests_sent'] += 1
            
            if not self.ensure_connection():
                self.logger.error("无法建立连接")
                self.stats['requests_failed'] += 1
                return None
            
            response = self.session.get(
                f"{self.api_base_url}/api/v2/commands",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.last_used = datetime.now()
                data = response.json()
                return data.get('commands', [])
            else:
                self.logger.error(f"获取命令列表失败: {response.status_code}")
                self.stats['requests_failed'] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"获取命令列表异常: {e}")
            self.stats['requests_failed'] += 1
            return None
    
    def test_connection(self) -> bool:
        """测试连接"""
        return self.connect() and self.is_connected()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        success_rate = 0
        if self.stats['requests_sent'] > 0:
            success_rate = (self.stats['requests_sent'] - self.stats['requests_failed']) / self.stats['requests_sent'] * 100
            
        connection_success_rate = 0
        if self.stats['connection_attempts'] > 0:
            connection_success_rate = (self.stats['connection_attempts'] - self.stats['connection_failures']) / self.stats['connection_attempts'] * 100
            
        return {
            **self.stats,
            'success_rate': f"{success_rate:.2f}%",
            'connection_success_rate': f"{connection_success_rate:.2f}%",
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'connected': self.connected
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        if self.connect():
            return self
        else:
            raise ConnectionError("无法连接到HLL服务器")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
        self.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试客户端
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 找到第一个启用的服务器
        server_config = None
        for server in config['servers']:
            if server.get('enabled', False):
                server_config = server
                break

        if not server_config:
            print("未找到启用的服务器配置")
            exit(1)
        
        # 创建客户端
        client = HLLHttpClient(
            host=server_config['host'],
            port=server_config['port'],
            password=server_config['password']
        )

        print("测试优化版HTTP RCON客户端...")
        
        # 测试连接
        if client.connect():
            print("✓ 连接成功")
            
            # 测试获取命令
            commands = client.get_commands()
            if commands:
                print(f"✓ 获取到 {len(commands)} 个命令")
            
            # 测试获取玩家
            players = client.get_players()
            if players:
                print(f"✓ 获取到玩家信息")
            
            # 测试获取日志
            logs = client.get_admin_logs(300)
            if logs:
                print(f"✓ 获取到 {len(logs)} 条日志")
                print(f"  最新日志: {logs[0]['message'][:100]}..." if logs else "")
            else:
                print("✗ 未获取到日志")
            
            # 显示性能统计
            stats = client.get_stats()
            print(f"✓ 性能统计: 请求成功率 {stats['success_rate']}, 连接成功率 {stats['connection_success_rate']}")
            
            # 断开连接
            client.disconnect()
            print("✓ 断开连接成功")
        else:
            print("✗ 连接失败")
    
    except Exception as e:
        print(f"测试失败: {e}")