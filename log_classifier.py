"""
HLL日志分类器
根据日志内容将其分为不同类型：击杀、聊天、玩家进出、比赛状态、选阵营和其他
"""

import re
from typing import Dict, List, Any
from enum import Enum

class LogType(Enum):
    """日志类型枚举"""
    KILL = "击杀日志"
    CHAT = "聊天日志"
    PLAYER_CONNECTION = "玩家进出日志"
    MATCH_STATUS = "比赛状态日志"
    TEAM_SWITCH = "选阵营日志"
    OTHER = "其他日志"

class LogClassifier:
    """日志分类器"""
    
    def __init__(self):
        """初始化分类器，定义各种日志类型的匹配模式"""
        self.patterns = {
            LogType.KILL: [
                r'KILL:.*->.*with',  # 普通击杀
                r'TEAM KILL:.*->.*with',  # 友军误伤
            ],
            LogType.CHAT: [
                r'CHAT\[.*\]\[.*\]:',  # 聊天消息
            ],
            LogType.PLAYER_CONNECTION: [
                r'CONNECTED.*\(',  # 玩家连接
                r'DISCONNECTED.*\(',  # 玩家断开
            ],
            LogType.MATCH_STATUS: [
                r'MATCH.*START',  # 比赛开始
                r'MATCH.*END',  # 比赛结束
                r'ROUND.*START',  # 回合开始
                r'ROUND.*END',  # 回合结束
                r'GAME.*START',  # 游戏开始
                r'GAME.*END',  # 游戏结束
                r'VICTORY',  # 胜利
                r'DEFEAT',  # 失败
                r'WIN',  # 获胜
            ],
            LogType.TEAM_SWITCH: [
                r'TEAMSWITCH.*\(.*>.*\)',  # 队伍切换
            ]
        }
        
        # 编译正则表达式以提高性能
        self.compiled_patterns = {}
        for log_type, patterns in self.patterns.items():
            self.compiled_patterns[log_type] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def classify_log(self, log_entry: Dict[str, Any]) -> LogType:
        """
        分类单条日志
        
        Args:
            log_entry: 日志条目字典，包含message字段
            
        Returns:
            LogType: 日志类型
        """
        message = log_entry.get('message', '')
        
        # 按优先级检查各种日志类型
        for log_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(message):
                    return log_type
        
        # 如果没有匹配到任何模式，归类为其他
        return LogType.OTHER
    
    def classify_logs(self, logs: List[Dict[str, Any]]) -> Dict[LogType, List[Dict[str, Any]]]:
        """
        批量分类日志
        
        Args:
            logs: 日志列表
            
        Returns:
            Dict[LogType, List]: 按类型分组的日志字典
        """
        classified_logs = {log_type: [] for log_type in LogType}
        
        for log_entry in logs:
            log_type = self.classify_log(log_entry)
            classified_logs[log_type].append(log_entry)
        
        return classified_logs
    
    def get_statistics(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        获取日志分类统计信息
        
        Args:
            logs: 日志列表
            
        Returns:
            Dict[str, int]: 各类型日志的数量统计
        """
        classified_logs = self.classify_logs(logs)
        statistics = {}
        
        for log_type, log_list in classified_logs.items():
            statistics[log_type.value] = len(log_list)
        
        return statistics
    
    def filter_logs_by_type(self, logs: List[Dict[str, Any]], log_type: LogType) -> List[Dict[str, Any]]:
        """
        根据类型过滤日志
        
        Args:
            logs: 日志列表
            log_type: 要过滤的日志类型
            
        Returns:
            List[Dict]: 指定类型的日志列表
        """
        filtered_logs = []
        
        for log_entry in logs:
            if self.classify_log(log_entry) == log_type:
                filtered_logs.append(log_entry)
        
        return filtered_logs

def main():
    """测试分类器功能"""
    import json
    
    # 创建分类器实例
    classifier = LogClassifier()
    
    # 测试样本日志
    test_logs = [
        {"message": "[2:58 min (1761193883)] KILL: esc—5(Allies/76561198287323037) -> ICE Tea(Axis/76561199130443107) with M1 GARAND"},
        {"message": "[2:47 min (1761193893)] CHAT[Team][mrgeorge06824(Axis/02339d3b7647c9bfd89cca2ce1fa9813)]: KKKKK"},
        {"message": "[2:49 min (1761193891)] CONNECTED 美术特长生 (76561199404917656)"},
        {"message": "[2:46 min (1761192274)] DISCONNECTED 晟循 (76561199887669374)"},
        {"message": "[2:55 min (1761193886)] TEAMSWITCH javito (None > Allies)"},
        {"message": "[2:33 min (1761193907)] TEAM KILL: 於罔yu(Axis/9cd56a1d6578e8d911076b0933b3d1b6) -> World's End Dancehall(Axis/76561199244154157) with 150MM HOWITZER [sFH 18]"},
    ]
    
    # 分类测试
    classified = classifier.classify_logs(test_logs)
    
    print("=== 日志分类测试结果 ===")
    for log_type, logs in classified.items():
        print(f"\n{log_type.value} ({len(logs)}条):")
        for log in logs:
            print(f"  - {log['message']}")
    
    # 统计测试
    stats = classifier.get_statistics(test_logs)
    print(f"\n=== 统计信息 ===")
    for log_type, count in stats.items():
        print(f"{log_type}: {count}条")

if __name__ == "__main__":
    main()