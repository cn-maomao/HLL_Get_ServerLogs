import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from hll_http_client import HLLHttpClient
from log_manager import LogManager
from categorized_log_manager import CategorizedLogManager

class LogCollector:
    """HLL日志收集器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_manager = LogManager(config.get("log_settings", {}).get("logs_directory", "logs"))
        self.categorized_log_manager = CategorizedLogManager()
        self.clients: Dict[str, HLLHttpClient] = {}  # 只使用HTTP客户端
        self.running = False
        self.collection_thread = None
        self.save_thread = None
        self.logger = logging.getLogger("LogCollector")
        
        # 配置参数
        self.collection_interval = config.get("log_settings", {}).get("collection_interval", 5)
        self.save_interval = config.get("log_settings", {}).get("save_interval", 3600)
        self.max_retries = config.get("log_settings", {}).get("max_retries", 3)
        self.retry_delay = config.get("log_settings", {}).get("retry_delay", 10)
        
        # 内存中的日志缓存
        self.log_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.cache_lock = threading.Lock()
        
        # 初始化客户端
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化HTTP客户端"""
        servers = self.config.get("servers", [])
        api_config = self.config.get("api_config", {})
        
        for server in servers:
            if server.get("enabled", True):
                server_name = server["name"]
                
                # 获取服务器特定的API配置，如果没有则使用全局配置
                api_host = server.get("api_host")
                api_port = server.get("api_port")
                
                # 使用HTTP客户端
                client = HLLHttpClient(
                    host=server["host"],
                    port=server["port"],
                    password=server["password"],
                    api_host=api_host,
                    api_port=api_port,
                    api_config=api_config
                )
                self.logger.info(f"初始化HTTP客户端: {server_name} (API: {client.api_host}:{client.api_port})")
                
                self.clients[server_name] = client
                self.log_cache[server_name] = []
    
    def start(self):
        """启动日志收集"""
        if self.running:
            self.logger.warning("日志收集器已经在运行")
            return
        
        self.running = True
        self.logger.info("启动日志收集器")
        
        # 启动收集线程
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        # 启动保存线程
        self.save_thread = threading.Thread(target=self._save_loop, daemon=True)
        self.save_thread.start()
    
    def stop(self):
        """停止日志收集"""
        if not self.running:
            return
        
        self.logger.info("停止日志收集器")
        self.running = False
        
        # 等待线程结束
        if self.collection_thread:
            self.collection_thread.join(timeout=10)
        if self.save_thread:
            self.save_thread.join(timeout=10)
        
        # 保存剩余的缓存日志
        self._save_all_cached_logs()
        
        # 断开所有连接
        for client in self.clients.values():
            client.disconnect()
        
        self.logger.info("日志收集器已停止")
    
    def _collection_loop(self):
        """日志收集主循环"""
        self.logger.info(f"开始日志收集循环，间隔: {self.collection_interval}秒")
        
        while self.running:
            try:
                start_time = time.time()
                
                # 并行收集所有服务器的日志
                self._collect_logs_from_all_servers()
                
                # 计算睡眠时间
                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.collection_interval - elapsed_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"日志收集耗时 {elapsed_time:.2f}秒，超过间隔时间")
                    
            except Exception as e:
                self.logger.error(f"日志收集循环出错: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_logs_from_all_servers(self):
        """并行收集所有服务器的日志"""
        if not self.clients:
            return
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=len(self.clients)) as executor:
            future_to_server = {
                executor.submit(self._collect_server_logs, server_name, client): server_name
                for server_name, client in self.clients.items()
            }
            
            for future in as_completed(future_to_server):
                server_name = future_to_server[future]
                try:
                    logs = future.result(timeout=30)  # 30秒超时
                    if logs:
                        with self.cache_lock:
                            self.log_cache[server_name].extend(logs)
                        self.logger.debug(f"收集到 {len(logs)} 条日志 from {server_name}")
                except Exception as e:
                    self.logger.error(f"收集服务器 {server_name} 日志失败: {e}")
    
    def _collect_server_logs(self, server_name: str, client: HLLHttpClient) -> List[Dict[str, Any]]:
        """收集单个服务器的日志"""
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # 确保连接有效
                if not client.ensure_connection():
                    raise Exception("无法建立连接")
                
                # HTTP客户端获取日志
                logs = client.get_admin_logs(seconds=180)  # 获取3分钟的日志
                if logs is not None:
                    # 转换格式以保持一致性
                    formatted_logs = []
                    for log_entry in logs:
                        formatted_logs.append({
                            'timestamp': log_entry.get('timestamp', ''),
                            'server': server_name,
                            'message': log_entry.get('message', ''),
                            'raw_data': log_entry
                        })
                    logs = formatted_logs
                    self.logger.debug(f"HTTP客户端收集到 {server_name} 的 {len(logs)} 条日志")
                    return logs
                else:
                    raise Exception("获取日志返回None")
                    
            except Exception as e:
                retry_count += 1
                self.logger.warning(f"收集 {server_name} 日志失败 (尝试 {retry_count}/{self.max_retries}): {e}")
                
                if retry_count < self.max_retries:
                    # 增加重试间隔，给服务器更多恢复时间
                    sleep_time = self.retry_delay * retry_count  # 递增延迟
                    self.logger.info(f"等待 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)
                else:
                    # 重置连接状态
                    client.disconnect()
                    self.logger.error(f"收集 {server_name} 日志最终失败，已断开连接")
        
        return []
    
    def _save_loop(self):
        """日志保存主循环"""
        self.logger.info(f"开始日志保存循环，间隔: {self.save_interval}秒")
        
        last_save_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # 检查是否到了保存时间或者有新日志需要保存
                should_save = current_time - last_save_time >= self.save_interval
                
                # 如果有缓存的日志，也触发保存
                with self.cache_lock:
                    has_cached_logs = any(logs for logs in self.log_cache.values())
                
                if should_save or has_cached_logs:
                    self._save_all_cached_logs()
                    last_save_time = current_time
                
                # 每5秒检查一次（更频繁）
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"日志保存循环出错: {e}")
                time.sleep(5)
    
    def _save_all_cached_logs(self):
        """保存所有缓存的日志"""
        with self.cache_lock:
            for server_name, logs in self.log_cache.items():
                if logs:
                    try:
                        # 保存原始日志
                        self.log_manager.save_logs(server_name, logs)
                        self.logger.info(f"保存了 {len(logs)} 条缓存日志 for {server_name}")
                        
                        # 保存分类日志
                        save_counts = self.categorized_log_manager.save_categorized_logs(server_name, logs)
                        if save_counts:
                            self.logger.info(f"分类保存完成 for {server_name}: {save_counts}")
                        
                        logs.clear()  # 清空缓存
                    except Exception as e:
                        self.logger.error(f"保存 {server_name} 缓存日志失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取收集器状态"""
        status = {
            "running": self.running,
            "servers": {},
            "cache_status": {}
        }
        
        # 服务器连接状态
        for server_name, client in self.clients.items():
            status["servers"][server_name] = {
                "connected": client.connected,
                "host": client.host,
                "port": client.port
            }
        
        # 缓存状态
        with self.cache_lock:
            for server_name, logs in self.log_cache.items():
                status["cache_status"][server_name] = {
                    "cached_logs": len(logs),
                    "log_file_info": self.log_manager.get_current_log_file_info(server_name)
                }
        
        return status
    
    def force_save(self):
        """强制保存所有缓存日志"""
        self.logger.info("强制保存缓存日志")
        self._save_all_cached_logs()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "servers": {},
            "total_files": 0,
            "total_size": 0,
            "total_logs": 0
        }
        
        for server_name in self.clients.keys():
            server_stats = self.log_manager.get_log_statistics(server_name)
            stats["servers"][server_name] = server_stats
            stats["total_files"] += server_stats["total_files"]
            stats["total_size"] += server_stats["total_size"]
            stats["total_logs"] += server_stats["total_logs"]
        
        return stats
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """清理旧日志"""
        self.logger.info(f"开始清理 {days_to_keep} 天前的旧日志")
        for server_name in self.clients.keys():
            self.log_manager.cleanup_old_logs(server_name, days_to_keep)