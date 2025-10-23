# HLL 服务器日志收集面板

一个用于收集和管理 Hell Let Loose (HLL) 服务器日志的工具，支持多服务器监控、日志分类和实时收集。

## 功能特性

- 🔄 **实时日志收集**: 自动从多个HLL服务器收集管理员日志
- 📊 **智能日志分类**: 自动识别并分类不同类型的日志（击杀、聊天、玩家连接等）
- 🗂️ **结构化存储**: 按日期和服务器组织日志文件，支持原始和分类日志
- 🔧 **多服务器支持**: 同时监控多个HLL服务器
- ⚡ **高性能HTTP客户端**: 优化的连接池和重试机制
- 📈 **性能监控**: 内置请求统计和连接状态监控

## 项目结构

```
HLL_Servers_Panel/
├── log_collector.py           # 主日志收集器
├── hll_http_client.py         # 优化的HTTP客户端
├── log_classifier.py          # 日志分类器
├── categorized_log_manager.py # 分类日志管理器
├── config.json                # 配置文件
├── README.md                  # 项目说明
├── HLL_RCON_API_中文文档.md   # API 文档
└── logs/                      # 日志存储目录
    └── server1/               # 按服务器分组
        └── 25_10/             # 按年月分组
            └── 23/            # 按日分组
                ├── raw_2025-10-23_12.json      # 原始日志
                ├── chat_2025-10-23_12.json     # 聊天日志
                ├── kills_2025-10-23_12.json    # 击杀日志
                ├── players_2025-10-23_12.json  # 玩家日志
                └── teams_2025-10-23_12.json    # 队伍日志
```

## 安装和配置

### 1. 安装依赖

```bash
pip install requests urllib3
```

### 2. 配置服务器

编辑 `config.json` 文件：

```json
{
  "api_config": {
    "default_host": "192.168.1.14",
    "default_port": 17080,
    "timeout": 30,
    "max_retries": 3
  },
  "servers": [
    {
      "name": "server1",
      "host": "your_server_ip",
      "port": 20300,
      "password": "your_password",
      "enabled": true,
      "api_host": "192.168.1.14",
      "api_port": 17080
    }
  ],
  "log_settings": {
    "collection_interval": 5,
    "save_interval": 60,
    "logs_directory": "logs",
    "max_retries": 5,
    "retry_delay": 15
  }
}
```

#### 配置说明

**API配置 (api_config)**：
- `default_host`: 默认API服务器地址
- `default_port`: 默认API服务器端口
- `timeout`: 请求超时时间（秒）
- `max_retries`: 最大重试次数

**服务器配置 (servers)**：
- `name`: 服务器名称
- `host`: HLL服务器地址
- `port`: HLL服务器RCON端口
- `password`: RCON密码
- `enabled`: 是否启用该服务器
- `api_host`: 该服务器专用的API地址（可选，优先级高于默认配置）
- `api_port`: 该服务器专用的API端口（可选，优先级高于默认配置）

**日志设置 (log_settings)**：
- `collection_interval`: 日志收集间隔（秒）
- `save_interval`: 日志保存间隔（秒）
- `logs_directory`: 日志保存目录
- `max_retries`: 最大重试次数
- `retry_delay`: 重试延迟（秒）
```

### 3. 运行日志收集器

```bash
python log_collector.py
```

## 日志分类系统

系统自动识别以下类型的日志：

### 1. 击杀日志 (kills)
- 玩家击杀记录
- 包含击杀者、被击杀者、武器信息
- 示例: `KILL: [AXIS] Player1 -> [ALLIES] Player2 with Kar98k`

### 2. 聊天日志 (chat)
- 玩家聊天消息
- 包含发送者、频道、消息内容
- 示例: `CHAT[Unit]: [AXIS] Player1: Hello team!`

### 3. 玩家连接日志 (players)
- 玩家加入/离开服务器
- 包含玩家信息和连接状态
- 示例: `CONNECTED Player1 (76561198000000000)`

### 4. 比赛状态日志 (match)
- 比赛开始/结束
- 地图切换信息
- 示例: `MATCH START UTAH BEACH WARFARE`

### 5. 队伍切换日志 (teams)
- 玩家队伍变更
- 包含玩家和新队伍信息
- 示例: `TEAM SWITCH Player1 > Allies`

### 6. 其他日志 (other)
- 管理员操作
- 系统消息
- 其他未分类日志

## HTTP客户端优化特性

### 连接池管理
- 自动连接池，支持连接复用
- 智能重试机制，处理网络异常
- 连接状态缓存，减少不必要的检查

### 性能监控
- 请求成功率统计
- 连接成功率监控
- 响应时间跟踪

### 错误处理
- 自动重连机制
- 优雅的错误恢复
- 详细的错误日志

## 使用说明

### 启动收集器

```bash
python log_collector.py
```

### 测试HTTP客户端

```bash
python hll_http_client.py
```

### 查看日志统计

收集器运行时会显示：
- 收集的日志数量
- 分类统计信息
- 连接状态
- 性能指标

## 故障排除

### 常见问题

1. **连接失败**
   - 检查服务器IP和端口
   - 确认密码正确
   - 检查网络连接

2. **日志收集异常**
   - 查看错误日志
   - 检查API服务状态
   - 验证服务器配置

3. **分类错误**
   - 检查日志格式
   - 更新分类规则
   - 查看原始日志内容

## 性能优化

- **连接复用**: 保持HTTP连接，避免频繁连接断开
- **批量处理**: 批量保存日志，提高I/O效率
- **智能缓存**: 缓存连接状态，减少网络请求
- **异步处理**: 支持并发日志收集

## 安全注意事项

- 妥善保管服务器密码，不要提交到版本控制系统
- 定期更换访问密码
- 限制日志文件访问权限
- 监控异常访问行为

## 更新日志

### v2.0.0 (当前版本)
- 移除RCON客户端，统一使用HTTP客户端
- 优化连接池和重试机制
- 增强性能监控功能
- 简化配置文件结构

### v1.0.0
- 初始版本
- 支持RCON和HTTP双模式
- 基础日志收集功能
- 简单的日志分类

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

---

**注意**: 请确保你有权限访问HLL服务器的管理接口，并遵守服务器使用条款。