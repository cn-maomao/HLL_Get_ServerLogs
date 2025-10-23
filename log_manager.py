import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class LogManager:
    """日志文件管理器"""
    
    def __init__(self, logs_directory: str = "logs"):
        self.logs_directory = Path(logs_directory)
        self.logger = logging.getLogger("LogManager")
        self.current_log_files = {}  # 存储当前打开的日志文件句柄
        
        # 确保日志目录存在
        self.logs_directory.mkdir(exist_ok=True)
    
    def get_log_file_path(self, server_name: str, timestamp: datetime = None) -> Path:
        """获取日志文件路径
        
        Args:
            server_name: 服务器名称
            timestamp: 时间戳，默认为当前时间
            
        Returns:
            日志文件路径
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        # 格式化年月：25_10 (2025年10月)
        year_month = timestamp.strftime("%y_%m")
        
        # 格式化日期：23 (23日)
        day = timestamp.strftime("%d")
        
        # 构建目录路径：logs/server1/25_10/23
        log_dir = self.logs_directory / server_name / year_month
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建文件路径：logs/server1/25_10/23/hll_logs_2025-10-23_14.json
        hour = timestamp.strftime("%H")
        filename = f"hll_logs_{timestamp.strftime('%Y-%m-%d')}_{hour}.json"
        
        return log_dir / day / filename
    
    def save_logs(self, server_name: str, logs: List[Dict[str, Any]], timestamp: datetime = None) -> int:
        """保存日志到文件
        
        Args:
            server_name: 服务器名称
            logs: 日志数据列表
            timestamp: 时间戳，默认为当前时间
            
        Returns:
            保存的新日志数量
        """
        if not logs:
            return 0
            
        if timestamp is None:
            timestamp = datetime.now()
            
        log_file_path = self.get_log_file_path(server_name, timestamp)
        
        # 确保目录存在
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 读取现有日志（如果文件存在）
            existing_logs = []
            if log_file_path.exists():
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    try:
                        existing_logs = json.load(f)
                    except json.JSONDecodeError:
                        self.logger.warning(f"日志文件格式错误，将重新创建: {log_file_path}")
                        existing_logs = []
            
            # 合并新日志（避免重复）
            existing_log_ids = set()
            if existing_logs:
                for log in existing_logs:
                    # 使用时间戳和消息内容作为唯一标识（兼容大小写）
                    timestamp = log.get('timestamp', '') or log.get('Timestamp', '')
                    message = log.get('message', '') or log.get('Message', '')
                    log_id = f"{timestamp}_{message}"
                    existing_log_ids.add(log_id)
            
            new_logs = []
            for log in logs:
                # 使用时间戳和消息内容作为唯一标识（兼容大小写）
                timestamp = log.get('timestamp', '') or log.get('Timestamp', '')
                message = log.get('message', '') or log.get('Message', '')
                log_id = f"{timestamp}_{message}"
                if log_id not in existing_log_ids:
                    new_logs.append(log)
                    existing_log_ids.add(log_id)
            
            if new_logs:
                # 添加收集时间戳
                current_time = datetime.now()
                for log in new_logs:
                    log['CollectedAt'] = current_time.isoformat()
                
                # 合并并保存
                all_logs = existing_logs + new_logs
                
                with open(log_file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_logs, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"保存了 {len(new_logs)} 条新日志到 {log_file_path}")
                return len(new_logs)
            else:
                self.logger.debug(f"没有新日志需要保存到 {log_file_path}")
                return 0
                
        except Exception as e:
            self.logger.error(f"保存日志失败 {log_file_path}: {e}")
            return 0
    
    def get_current_log_file_info(self, server_name: str) -> Dict[str, Any]:
        """获取当前日志文件信息
        
        Args:
            server_name: 服务器名称
            
        Returns:
            包含文件路径、大小等信息的字典
        """
        current_time = datetime.now()
        log_file_path = self.get_log_file_path(server_name, current_time)
        
        info = {
            "path": str(log_file_path),
            "exists": log_file_path.exists(),
            "size": 0,
            "log_count": 0
        }
        
        if log_file_path.exists():
            try:
                info["size"] = log_file_path.stat().st_size
                
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    info["log_count"] = len(logs) if isinstance(logs, list) else 0
                    
            except Exception as e:
                self.logger.error(f"读取日志文件信息失败 {log_file_path}: {e}")
        
        return info
    
    def cleanup_old_logs(self, server_name: str, days_to_keep: int = 30):
        """清理旧日志文件
        
        Args:
            server_name: 服务器名称
            days_to_keep: 保留天数
        """
        try:
            server_log_dir = self.logs_directory / server_name
            if not server_log_dir.exists():
                return
            
            current_time = datetime.now()
            deleted_count = 0
            
            # 遍历所有年月目录
            for year_month_dir in server_log_dir.iterdir():
                if not year_month_dir.is_dir():
                    continue
                    
                # 遍历所有日期目录
                for day_dir in year_month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue
                    
                    # 遍历日志文件
                    for log_file in day_dir.glob("*.json"):
                        try:
                            # 从文件名提取日期
                            file_date_str = log_file.stem.split('_')[2]  # hll_logs_2025-10-23_14.json
                            file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                            
                            # 检查是否超过保留期限
                            if (current_time - file_date).days > days_to_keep:
                                log_file.unlink()
                                deleted_count += 1
                                self.logger.info(f"删除旧日志文件: {log_file}")
                                
                        except Exception as e:
                            self.logger.error(f"处理日志文件失败 {log_file}: {e}")
                    
                    # 如果日期目录为空，删除它
                    try:
                        if not any(day_dir.iterdir()):
                            day_dir.rmdir()
                    except:
                        pass
                
                # 如果年月目录为空，删除它
                try:
                    if not any(year_month_dir.iterdir()):
                        year_month_dir.rmdir()
                except:
                    pass
            
            if deleted_count > 0:
                self.logger.info(f"清理完成，删除了 {deleted_count} 个旧日志文件")
                
        except Exception as e:
            self.logger.error(f"清理旧日志失败: {e}")
    
    def get_log_statistics(self, server_name: str) -> Dict[str, Any]:
        """获取日志统计信息
        
        Args:
            server_name: 服务器名称
            
        Returns:
            统计信息字典
        """
        stats = {
            "total_files": 0,
            "total_size": 0,
            "total_logs": 0,
            "date_range": {"start": None, "end": None}
        }
        
        try:
            server_log_dir = self.logs_directory / server_name
            if not server_log_dir.exists():
                return stats
            
            dates = []
            
            # 遍历所有日志文件
            for log_file in server_log_dir.rglob("*.json"):
                stats["total_files"] += 1
                stats["total_size"] += log_file.stat().st_size
                
                try:
                    # 从文件名提取日期
                    file_date_str = log_file.stem.split('_')[2]
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                    dates.append(file_date)
                    
                    # 统计日志条数
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                        if isinstance(logs, list):
                            stats["total_logs"] += len(logs)
                            
                except Exception as e:
                    self.logger.error(f"读取日志文件统计失败 {log_file}: {e}")
            
            # 设置日期范围
            if dates:
                stats["date_range"]["start"] = min(dates).strftime("%Y-%m-%d")
                stats["date_range"]["end"] = max(dates).strftime("%Y-%m-%d")
            
        except Exception as e:
            self.logger.error(f"获取日志统计失败: {e}")
        
        return stats