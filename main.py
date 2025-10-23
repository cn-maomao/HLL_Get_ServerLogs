#!/usr/bin/env python3
"""
Hell Let Loose 日志收集器主程序
自动收集HLL服务器的管理员日志并按时间分类保存
"""

import os
import sys
import json
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime

from log_collector import LogCollector

class HLLLogCollectorApp:
    """HLL日志收集器应用程序"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = None
        self.collector = None
        self.logger = None
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n收到信号 {signum}，正在优雅关闭...")
        self.stop()
        sys.exit(0)
    
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                print(f"错误: 配置文件 {self.config_file} 不存在")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            print(f"成功加载配置文件: {self.config_file}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件格式错误: {e}")
            return False
        except Exception as e:
            print(f"错误: 加载配置文件失败: {e}")
            return False
    
    def setup_logging(self):
        """设置日志系统"""
        log_config = self.config.get("logging", {})
        
        # 创建日志目录
        log_file = log_config.get("file", "hll_log_collector.log")
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志格式
        log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        log_level = getattr(logging, log_config.get("level", "INFO").upper())
        
        # 设置根日志记录器
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger("HLLLogCollectorApp")
        self.logger.info("日志系统初始化完成")
    
    def validate_config(self) -> bool:
        """验证配置文件"""
        if not self.config:
            print("错误: 配置未加载")
            return False
        
        # 检查服务器配置
        servers = self.config.get("servers", [])
        if not servers:
            print("错误: 没有配置任何服务器")
            return False
        
        enabled_servers = [s for s in servers if s.get("enabled", True)]
        if not enabled_servers:
            print("错误: 没有启用的服务器")
            return False
        
        # 验证服务器配置
        for i, server in enumerate(servers):
            required_fields = ["name", "host", "port", "password"]
            for field in required_fields:
                if field not in server:
                    print(f"错误: 服务器 {i+1} 缺少必需字段: {field}")
                    return False
        
        # 检查日志设置
        log_settings = self.config.get("log_settings", {})
        collection_interval = log_settings.get("collection_interval", 5)
        if collection_interval < 1:
            print("错误: collection_interval 必须大于等于1秒")
            return False
        
        save_interval = log_settings.get("save_interval", 3600)
        if save_interval < 60:
            print("错误: save_interval 必须大于等于60秒")
            return False
        
        self.logger.info("配置验证通过")
        return True
    
    def start(self):
        """启动应用程序"""
        try:
            self.logger.info("启动HLL日志收集器")
            
            # 创建并启动收集器
            self.collector = LogCollector(self.config)
            self.collector.start()
            
            # 显示启动信息
            self._show_startup_info()
            
            # 主循环
            self._main_loop()
            
        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            raise
    
    def stop(self):
        """停止应用程序"""
        if self.collector:
            self.collector.stop()
            self.collector = None
        
        if self.logger:
            self.logger.info("HLL日志收集器已停止")
    
    def _show_startup_info(self):
        """显示启动信息"""
        enabled_servers = [s for s in self.config["servers"] if s.get("enabled", True)]
        
        print("\n" + "="*60)
        print("HLL日志收集器已启动")
        print("="*60)
        print(f"配置文件: {self.config_file}")
        print(f"启用服务器数量: {len(enabled_servers)}")
        
        for server in enabled_servers:
            print(f"  - {server['name']}: {server['host']}:{server['port']}")
        
        log_settings = self.config.get("log_settings", {})
        print(f"收集间隔: {log_settings.get('collection_interval', 5)}秒")
        print(f"保存间隔: {log_settings.get('save_interval', 3600)}秒")
        print(f"日志目录: {log_settings.get('logs_directory', 'logs')}")
        print("="*60)
        print("按 Ctrl+C 停止程序")
        print("输入 'status' 查看状态，'stats' 查看统计信息，'help' 查看帮助")
        print("="*60 + "\n")
    
    def _main_loop(self):
        """主循环，处理用户输入"""
        try:
            while True:
                try:
                    user_input = input().strip().lower()
                    
                    if user_input == "status":
                        self._show_status()
                    elif user_input == "stats":
                        self._show_statistics()
                    elif user_input == "save":
                        self._force_save()
                    elif user_input == "cleanup":
                        self._cleanup_logs()
                    elif user_input == "help":
                        self._show_help()
                    elif user_input in ["quit", "exit", "stop"]:
                        break
                    elif user_input:
                        print(f"未知命令: {user_input}，输入 'help' 查看帮助")
                        
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            self.logger.error(f"主循环出错: {e}")
    
    def _show_status(self):
        """显示状态信息"""
        if not self.collector:
            print("收集器未运行")
            return
        
        status = self.collector.get_status()
        
        print("\n" + "-"*40)
        print("收集器状态")
        print("-"*40)
        print(f"运行状态: {'运行中' if status['running'] else '已停止'}")
        
        print("\n服务器连接状态:")
        for server_name, server_status in status["servers"].items():
            conn_status = "已连接" if server_status["connected"] else "未连接"
            print(f"  {server_name}: {conn_status} ({server_status['host']}:{server_status['port']})")
        
        print("\n缓存状态:")
        for server_name, cache_status in status["cache_status"].items():
            cached_logs = cache_status["cached_logs"]
            log_file_info = cache_status["log_file_info"]
            print(f"  {server_name}: {cached_logs} 条缓存日志")
            print(f"    当前日志文件: {log_file_info['log_count']} 条记录, {log_file_info['size']} 字节")
        
        print("-"*40 + "\n")
    
    def _show_statistics(self):
        """显示统计信息"""
        if not self.collector:
            print("收集器未运行")
            return
        
        stats = self.collector.get_statistics()
        
        print("\n" + "-"*40)
        print("统计信息")
        print("-"*40)
        print(f"总文件数: {stats['total_files']}")
        print(f"总大小: {stats['total_size'] / 1024 / 1024:.2f} MB")
        print(f"总日志条数: {stats['total_logs']}")
        
        print("\n各服务器统计:")
        for server_name, server_stats in stats["servers"].items():
            print(f"  {server_name}:")
            print(f"    文件数: {server_stats['total_files']}")
            print(f"    大小: {server_stats['total_size'] / 1024 / 1024:.2f} MB")
            print(f"    日志条数: {server_stats['total_logs']}")
            if server_stats["date_range"]["start"]:
                print(f"    日期范围: {server_stats['date_range']['start']} ~ {server_stats['date_range']['end']}")
        
        print("-"*40 + "\n")
    
    def _force_save(self):
        """强制保存"""
        if not self.collector:
            print("收集器未运行")
            return
        
        print("正在强制保存缓存日志...")
        self.collector.force_save()
        print("保存完成")
    
    def _cleanup_logs(self):
        """清理旧日志"""
        if not self.collector:
            print("收集器未运行")
            return
        
        try:
            days = input("请输入要保留的天数 (默认30天): ").strip()
            days = int(days) if days else 30
            
            if days < 1:
                print("天数必须大于0")
                return
            
            print(f"正在清理 {days} 天前的日志...")
            self.collector.cleanup_old_logs(days)
            print("清理完成")
            
        except ValueError:
            print("请输入有效的数字")
        except KeyboardInterrupt:
            print("操作已取消")
    
    def _show_help(self):
        """显示帮助信息"""
        print("\n" + "-"*40)
        print("可用命令:")
        print("-"*40)
        print("status  - 显示收集器状态")
        print("stats   - 显示统计信息")
        print("save    - 强制保存缓存日志")
        print("cleanup - 清理旧日志文件")
        print("help    - 显示此帮助信息")
        print("quit    - 退出程序")
        print("-"*40 + "\n")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Hell Let Loose 日志收集器")
    parser.add_argument("-c", "--config", default="config.json", help="配置文件路径")
    parser.add_argument("--test", action="store_true", help="测试配置并退出")
    
    args = parser.parse_args()
    
    # 创建应用程序实例
    app = HLLLogCollectorApp(args.config)
    
    try:
        # 加载配置
        if not app.load_config():
            sys.exit(1)
        
        # 设置日志
        app.setup_logging()
        
        # 验证配置
        if not app.validate_config():
            sys.exit(1)
        
        # 如果是测试模式，只验证配置
        if args.test:
            print("配置测试通过")
            sys.exit(0)
        
        # 启动应用程序
        app.start()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)
    finally:
        app.stop()

if __name__ == "__main__":
    main()