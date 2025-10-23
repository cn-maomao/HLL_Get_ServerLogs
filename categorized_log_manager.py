"""
分类日志管理器
实现按类别保存日志的功能，将不同类型的日志保存到不同的文件中
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from log_classifier import LogClassifier, LogType

class CategorizedLogManager:
    """分类日志管理器"""
    
    def __init__(self, base_logs_dir: str = "logs"):
        """
        初始化分类日志管理器
        
        Args:
            base_logs_dir: 日志基础目录
        """
        self.base_logs_dir = base_logs_dir
        self.classifier = LogClassifier()
        
        # 为每种日志类型定义文件名前缀
        self.type_prefixes = {
            LogType.KILL: "kills",
            LogType.CHAT: "chat", 
            LogType.PLAYER_CONNECTION: "players",
            LogType.MATCH_STATUS: "matches",
            LogType.TEAM_SWITCH: "teams",
            LogType.OTHER: "other"
        }
    
    def _get_log_file_path(self, server_name: str, log_type: LogType, timestamp: datetime = None) -> str:
        """
        获取指定类型日志的文件路径
        
        Args:
            server_name: 服务器名称
            log_type: 日志类型
            timestamp: 时间戳，默认使用当前时间
            
        Returns:
            str: 日志文件路径
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 创建目录结构: logs/server1/25_10/23/kills_2025-10-23_12.json
        year_month = timestamp.strftime("%y_%m")
        day = timestamp.strftime("%d")
        hour = timestamp.strftime("%H")
        date_str = timestamp.strftime("%Y-%m-%d")
        
        log_dir = os.path.join(self.base_logs_dir, server_name, year_month, day)
        os.makedirs(log_dir, exist_ok=True)
        
        prefix = self.type_prefixes[log_type]
        filename = f"{prefix}_{date_str}_{hour}.json"
        
        return os.path.join(log_dir, filename)
    
    def save_categorized_logs(self, server_name: str, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        按类别保存日志
        
        Args:
            server_name: 服务器名称
            logs: 日志列表
            
        Returns:
            Dict[str, int]: 各类型保存的日志数量
        """
        if not logs:
            return {}
        
        # 分类日志
        classified_logs = self.classifier.classify_logs(logs)
        save_counts = {}
        
        # 为每种类型的日志保存到对应文件
        for log_type, type_logs in classified_logs.items():
            if not type_logs:  # 跳过空的日志类型
                continue
                
            file_path = self._get_log_file_path(server_name, log_type)
            
            # 读取现有日志（如果文件存在）
            existing_logs = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_logs = json.load(f)
                except (json.JSONDecodeError, IOError):
                    existing_logs = []
            
            # 合并新日志
            all_logs = existing_logs + type_logs
            
            # 保存到文件
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_logs, f, ensure_ascii=False, indent=2)
                
                save_counts[log_type.value] = len(type_logs)
                print(f"保存了 {len(type_logs)} 条{log_type.value}到 {file_path}")
                
            except IOError as e:
                print(f"保存{log_type.value}失败: {e}")
        
        return save_counts
    
    def get_categorized_logs(self, server_name: str, log_type: LogType, 
                           date: datetime = None) -> List[Dict[str, Any]]:
        """
        获取指定类型的日志
        
        Args:
            server_name: 服务器名称
            log_type: 日志类型
            date: 日期，默认使用当前日期
            
        Returns:
            List[Dict]: 指定类型的日志列表
        """
        file_path = self._get_log_file_path(server_name, log_type, date)
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def get_log_statistics(self, server_name: str, date: datetime = None) -> Dict[str, int]:
        """
        获取日志统计信息
        
        Args:
            server_name: 服务器名称
            date: 日期，默认使用当前日期
            
        Returns:
            Dict[str, int]: 各类型日志的数量统计
        """
        statistics = {}
        
        for log_type in LogType:
            logs = self.get_categorized_logs(server_name, log_type, date)
            statistics[log_type.value] = len(logs)
        
        return statistics
    
    def cleanup_old_logs(self, server_name: str, days_to_keep: int = 30):
        """
        清理旧日志文件
        
        Args:
            server_name: 服务器名称
            days_to_keep: 保留天数
        """
        # 这里可以实现清理逻辑，删除超过指定天数的日志文件
        pass

def main():
    """测试分类日志管理器"""
    import json
    
    # 创建管理器实例
    manager = CategorizedLogManager()
    
    # 测试样本日志
    test_logs = [
        {
            "timestamp": "2025-10-23T04:34:21.310Z",
            "server": "server1",
            "message": "[2:58 min (1761193883)] KILL: esc—5(Allies/76561198287323037) -> ICE Tea(Axis/76561199130443107) with M1 GARAND",
            "CollectedAt": "2025-10-23T12:35:18.533589"
        },
        {
            "timestamp": "2025-10-23T04:34:21.310Z",
            "server": "server1", 
            "message": "[2:47 min (1761193893)] CHAT[Team][mrgeorge06824(Axis/02339d3b7647c9bfd89cca2ce1fa9813)]: KKKKK",
            "CollectedAt": "2025-10-23T12:35:18.533589"
        },
        {
            "timestamp": "2025-10-23T04:34:21.310Z",
            "server": "server1",
            "message": "[2:49 min (1761193891)] CONNECTED 美术特长生 (76561199404917656)",
            "CollectedAt": "2025-10-23T12:35:18.533589"
        },
        {
            "timestamp": "2025-10-23T04:34:21.310Z",
            "server": "server1",
            "message": "[2:55 min (1761193886)] TEAMSWITCH javito (None > Allies)",
            "CollectedAt": "2025-10-23T12:35:18.533589"
        }
    ]
    
    # 测试保存分类日志
    print("=== 测试分类日志保存 ===")
    save_counts = manager.save_categorized_logs("test_server", test_logs)
    
    for log_type, count in save_counts.items():
        print(f"保存了 {count} 条{log_type}")
    
    # 测试获取统计信息
    print(f"\n=== 日志统计信息 ===")
    stats = manager.get_log_statistics("test_server")
    for log_type, count in stats.items():
        print(f"{log_type}: {count}条")

if __name__ == "__main__":
    main()