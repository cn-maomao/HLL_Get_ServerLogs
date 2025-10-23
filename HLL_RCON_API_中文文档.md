# Hell Let Loose - RCON V2 API 中文文档

## 概述

Hell Let Loose RCON V2 是一个用于远程控制和管理 Hell Let Loose 游戏服务器的 API 接口。本文档详细介绍了 API 的使用方法、命令格式和所有可用的命令。

## 请求格式

### JSON 请求格式
```json
{
  "AuthToken": "bc711e97-e32e-4033-bf97-a8028a10cb94",
  "Version": 2,
  "Name": "command_name",
  "ContentBody": "command_data"
}
```

### 请求参数说明

| 参数名 | 类型 | 描述 |
|--------|------|------|
| AuthToken | string | 认证令牌，是一个 GUID 格式的字符串，通过登录请求获得。除了 ServerConnect 和 Login 命令外，所有服务器请求都必须包含此令牌。如果未发送令牌或令牌无效，服务器将返回 401 状态码。 |
| Version | integer | API 版本号，随着 RCON 工具的扩展，命令可能需要更新。 |
| Name | string | 要在服务器上执行的命令名称。 |
| ContentBody | string | 请求所需的任何数据。 |

## 响应格式

### JSON 响应格式
```json
{
  "StatusCode": 200,
  "StatusMessage": "Successfully performed request.",
  "Version": 2,
  "Name": "command_name",
  "ContentBody": "command_response_data"
}
```

### 响应参数说明

| 参数名 | 类型 | 描述 |
|--------|------|------|
| StatusCode | integer | 服务器执行命令时的响应状态码。 |
| StatusMessage | string | 状态响应的描述信息。 |
| Version | integer | 处理的命令版本。 |
| Name | string | 处理的命令名称。 |
| ContentBody | string | 服务器的任何响应数据都将分配在此字段中。 |

## 数据包头部

### 固定数据包头部
头部是一个 8 字节的固定头部，包含 ID 和 JSON 包的内容长度。

| 名称 | 类型 | 描述 |
|------|------|------|
| ID | unsigned integer | 每个响应都有自己的 ID，此 ID 在响应中返回。 |
| Content Length | unsigned integer | JSON 包的长度，不包括固定头部。 |

## 状态码

服务器响应包含状态码，状态取决于命令是否在服务器上成功执行或命令是否遇到错误。

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 401 | 未授权 |
| 400 | 错误请求 |
| 500 | 内部错误 |

## 连接到 RCON V2

### 服务器连接
服务器连接命令将允许服务器开始处理 RCON V2 命令。服务器响应体中将包含用于加密/解密请求和响应的 XOR 密钥。服务器连接命令目前是唯一的非加密命令。

#### 请求示例
```json
{
  "AuthToken": "",
  "Version": 2,
  "Name": "ServerConnect",
  "ContentBody": ""
}
```

#### 响应示例
```json
{
  "statusCode": 200,
  "StatusMessage": "Successfully performed request.",
  "version": 2,
  "name": "ServerConnect",
  "contentBody": "OlguIHEAa4arqoOcaT0GbA=="
}
```

### XOR 加密
XOR 是服务器、客户端之间加密消息的方法。向服务器发送请求时，字节数据必须在发送前使用 XOR 密钥进行编码，接收到的任何响应都必须在读取前进行解码，但 ServerConnect 命令例外，该命令用于获取 XOR 密钥。

**注意：** XOR 密钥从服务器检索时格式为 Base64，在用于加密请求之前需要从 Base64 转换。

#### C# 示例
```csharp
public static byte[] XORCipher(byte[] bytes)
{
    for (int i = 0; i < bytes.Length; i++)
    {
        bytes[i] ^= m_XORKey[i % m_XORKey.Length];
    }
    return bytes;
}
```

## 登录到 RCON

大多数命令在执行前需要身份验证。使用相应的密码调用登录命令将验证服务器并生成身份验证令牌，该令牌包含在响应体中。

### 请求示例
```json
{
  "AuthToken": "",
  "Version": 2,
  "Name": "Login",
  "ContentBody": "[PASSWORD]"
}
```

### 响应示例
```json
{
  "statusCode": 200,
  "StatusMessage": "Successfully performed request.",
  "version": 2,
  "name": "Login",
  "contentBody": "F95C9BC14AA1D8AE8BC328BEF230DF52"
}
```

## RCON 命令详细说明

### 管理员管理命令

#### 添加管理员 (AddAdmin)
将玩家添加到管理员组。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |
| AdminGroup | string | 管理员组名 |
| Comment | string | 备注信息 |

#### 移除管理员 (RemoveAdmin)
移除玩家的管理员权限。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |

#### 获取管理员日志 (GetAdminLog)
检索指定时间间隔（秒）的管理员日志。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| LogBackTrackTime | Int32 | 日志回溯时间（秒） |
| Filters | string | 过滤器 |

#### 获取管理员组 (GetAdminGroups)
检索所有管理员组的列表。

**响应：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| GroupNames | String array | 管理员组名列表 |

#### 获取管理员用户 (GetAdminUsers)
检索所有管理员用户详细信息的列表。

**响应：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| AdminUsers | array | 管理员用户详细信息列表 |

**管理员用户条目：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| UserId | string | 管理员用户ID |
| Group | string | 管理员所属组 |
| Comment | string | 用户备注 |

### 地图管理命令

#### 更换地图 (ChangeMap)
触发服务器上的地图更换。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| MapName | string | 地图名称 |

#### 设置区域布局 (SetSectorLayout)
触发地图重启并将目标设置为指定区域。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| Sector_1 | string | 区域1 |
| Sector_2 | string | 区域2 |
| Sector_3 | string | 区域3 |
| Sector_4 | string | 区域4 |
| Sector_5 | string | 区域5 |

#### 添加地图到轮换 (AddMapToRotation)
在指定索引处向地图轮换添加地图。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| MapName | string | 地图名称 |
| Index | Int32 | 索引位置 |

#### 从轮换中移除地图 (RemoveMapFromRotation)
在指定索引处从轮换列表中移除地图。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| Index | Int32 | 索引位置 |

#### 添加地图到序列 (AddMapToSequence)
在指定索引处向地图序列添加地图。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| MapName | string | 地图名称 |
| Index | Int32 | 索引位置 |

#### 从序列中移除地图 (RemoveMapFromSequence)
在指定索引处从地图序列中移除地图。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| Index | Int32 | 索引位置 |

#### 设置地图随机播放 (SetMapShuffleEnabled)
随机化地图序列。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| Enable | boolean | 是否启用 |

#### 在序列中移动地图 (MoveMapInSequence)
将序列中的当前地图移动到另一个位置。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| CurrentIndex | Int32 | 当前索引 |
| NewIndex | Int32 | 新索引 |

### 服务器信息查询

#### 获取服务器信息 (GetServerInformation)
检索各种服务器信息。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| Name | string | 信息类型名称 |
| Value | string | 查询值（某些查询需要） |

**请求示例：**
```json
{
  "AuthToken": "f95c9bc1-4aa1-d8ae-8bc3-28bef230df52",
  "Version": 2,
  "Name": "ServerInformation",
  "ContentBody": {
    "Name": "players",
    "Value": ""
  }
}
```

**响应示例：**
```json
{
  "statusCode": 200,
  "StatusMessage": "Successfully performed request.",
  "version": 2,
  "name": "ServerInformation",
  "contentBody": "{
    \"players\": [
      {
        \"name\": \"John Doe\",
        \"iD\": \"76561197960287930\",
        \"platform\": \"steam\"
      }
    ]
  }"
}
```

#### 信息查询类型

| 查询名称 | 查询值 | 描述 |
|----------|--------|------|
| players | N/A | 检索服务器中的玩家列表 |
| player | Player ID | 检索玩家的详细信息 |
| maprotation | N/A | 检索轮换中的地图列表 |
| mapsequence | N/A | 检索序列中的地图列表 |
| session | N/A | 检索当前服务器会话信息 |
| serverconfig | N/A | 检索服务器配置信息 |
| bannedwords | N/A | 检索所有自定义亵渎词汇 |
| vipplayers | N/A | 检索VIP玩家列表 |

#### 玩家信息结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| Name | string | 玩家平台名称 |
| ClanTag | string | 玩家战队标签 |
| Id | string | 玩家平台ID |
| Platform | string | 玩家平台 |
| EosId | string | 玩家EOS ID |
| Level | Int32 | 玩家职业等级 |
| Team | Int32 | 玩家当前队伍 |
| Role | Int32 | 玩家当前角色 |
| Platoon | string | 玩家当前小队 |
| Kills | Int32 | 玩家当前击杀数 |
| Deaths | Int32 | 玩家当前死亡数 |
| ScoreData | PlayerScoreData | 玩家当前分数 |
| Loadout | string | 玩家当前装备 |
| WorldPosition | vector | 玩家当前世界位置 |

#### 地图信息结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| Name | string | 地图名称 |
| GameMode | string | 游戏模式名称 |
| TimeOfDay | string | 地图时间变体 |
| Id | string | 地图ID |
| Position | Int32 | 在轮换或序列中的位置 |

#### 会话信息结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| ServerName | string | 服务器名称 |
| MapName | string | 当前服务器正在运行的地图 |
| GameMode | string | 当前服务器正在运行的游戏模式 |
| RemainingMatchTime | Int32 | 比赛剩余时间 |
| MatchTime | Int32 | 比赛总时长 |
| AlliedFaction | Int32 | 盟军阵营索引 |
| AxisFaction | Int32 | 轴心国阵营索引 |
| MaxPlayerCount | Int32 | 服务器允许的最大玩家数 |
| AlliedScore | Int32 | 盟军队伍当前分数 |
| AxisScore | Int32 | 轴心国队伍当前分数 |
| PlayerCount | Int32 | 服务器当前玩家数 |
| AlliedPlayerCount | Int32 | 盟军队伍当前玩家数 |
| AxisPlayerCount | Int32 | 轴心国队伍当前玩家数 |
| MaxQueueCount | Int32 | 允许排队的最大玩家数 |
| QueueCount | Int32 | 当前排队的玩家数 |
| MaxVipQueueCount | Int32 | 允许排队的最大VIP数量 |
| VipQueueCount | Int32 | 当前排队的VIP玩家数 |

#### 服务器配置信息结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| ServerName | string | 服务器名称 |
| BuildNumber | string | 服务器当前构建号 |
| BuildRevision | string | 服务器当前构建修订版 |
| SupportedPlatforms | Array<string> | 服务器支持的平台 |
| PasswordProtected | boolean | 确定服务器是否受密码保护 |

#### 禁用词汇信息结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| BannedWords | Array<string> | 自定义禁用词汇列表 |

#### VIP玩家信息结构

| 字段名 | 类型 | 描述 |
|--------|------|------|
| VipPlayerIds | Array<string> | VIP玩家ID列表 |

### 玩家管理命令

#### 强制队伍切换 (ForceTeamSwitch)
强制玩家切换队伍。可以强制玩家在死亡时或立即切换。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | String | 玩家ID |
| ForceMode | UInt8 | 0 = 死亡时强制切换<br>1 = 立即强制切换 |

#### 设置队伍切换冷却时间 (SetTeamSwitchCooldown)
设置允许玩家切换队伍的冷却时间。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| TeamSwitchTimer | Int32 | 队伍切换计时器（秒） |

#### 设置最大排队玩家数 (SetMaxQueuedPlayers)
设置允许排队进入服务器的最大玩家数。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| MaxQueuedPlayers | Int32 | 最大排队玩家数 |

#### 设置空闲踢出时长 (SetIdleKickDuration)
设置踢出空闲玩家的时长。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| IdleTimeoutMinutes | Int32 | 空闲超时时间（分钟） |

#### 发送服务器消息 (SendServerMessage)
向服务器上的所有玩家显示消息。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| Message | string | 消息内容 |

#### 服务器广播 (ServerBroadcast)
向服务器广播消息。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| Message | string | 广播消息内容 |

#### 设置高延迟阈值 (SetHighPingThreshold)
设置高延迟玩家的阈值。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| HighPingThresholdMs | Int32 | 高延迟阈值（毫秒） |

#### 向玩家发送消息 (MessagePlayer)
向特定玩家发送消息。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| Message | string | 消息内容 |
| PlayerId | string | 玩家ID |

#### 惩罚玩家 (PunishPlayer)
通过击杀玩家角色来惩罚玩家。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |
| Reason | string | 惩罚原因 |

#### 踢出玩家 (KickPlayer)
从服务器踢出玩家。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |
| Reason | string | 踢出原因 |

### 封禁管理命令

#### 获取永久封禁 (GetPermanentBans)
检索所有永久玩家封禁的列表。

**响应：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| BanList | array | 永久封禁玩家列表 |

**封禁条目结构：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| UserId | String | 玩家ID |
| UserName | String | 被封禁玩家的用户名 |
| TimeOfBanning | String | 封禁时间 |
| DurationHours | Int32 | 封禁时长 |
| BanReason | String | 封禁原因 |
| AdminName | String | 设置封禁的管理员名称 |

#### 获取临时封禁 (GetTemporaryBans)
检索所有临时玩家封禁的列表。

**响应：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| BanList | array | 临时封禁玩家列表 |

**封禁条目结构：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| UserId | String | 玩家ID |
| UserName | String | 被封禁玩家的用户名 |
| TimeOfBanning | String | 封禁时间 |
| DurationHours | Int32 | 封禁时长 |
| BanReason | String | 封禁原因 |
| AdminName | String | 设置封禁的管理员名称 |

#### 临时封禁玩家 (TemporaryBanPlayer)
在一定时间内封禁玩家。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |
| Duration | Int32 | 封禁时长（小时） |
| Reason | string | 封禁原因 |
| AdminName | string | 管理员名称 |

#### 移除临时封禁 (RemoveTemporaryBan)
移除玩家的临时封禁。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |

#### 永久封禁玩家 (PermanentBanPlayer)
永久封禁玩家。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |
| Reason | string | 封禁原因 |
| AdminName | string | 管理员名称 |

#### 移除永久封禁 (RemovePermanentBan)
移除玩家的永久封禁。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |

### 游戏平衡命令

| 命令名称 | 命令ID | 描述 |
|----------|--------|------|
| 设置自动平衡启用 | SetAutoBalanceEnabled | 启用或禁用自动平衡。 |
| 设置自动平衡阈值 | SetAutoBalanceThreshold | 设置使用自动平衡时队伍的阈值。 |
| 重置踢出投票阈值 | ResetVoteKickThreshold | 移除自定义踢出投票阈值并恢复为默认值。 |
| 设置踢出投票启用 | SetVoteKickEnabled | 启用或禁用踢出投票功能。 |
| 设置踢出投票阈值 | SetVoteKickThreshold | 设置踢出投票阈值。 |

### 内容过滤命令

| 命令名称 | 命令ID | 描述 |
|----------|--------|------|
| 添加禁用词汇 | AddBannedWords | 将词汇添加到自定义亵渎词汇列表。 |
| 移除禁用词汇 | RemoveBannedWords | 从自定义亵渎词汇列表中移除词汇。 |

### VIP 管理命令

| 命令名称 | 命令ID | 描述 |
|----------|--------|------|
| 添加 VIP | AddVip | 给予玩家 VIP 状态。 |
| 移除 VIP | RemoveVip | 移除玩家的 VIP 状态。 |
| 设置 VIP 槽位数量 | SetVipSlotCount | 设置服务器的 VIP 槽位数量。 |

### 其他重要命令

#### 获取可显示命令 (GetDisplayableCommands)
检索 RCON V2 中所有命令的列表。

**响应：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| Entries | array | V2 中可用的命令列表 |

**命令条目结构：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| Id | string | 命令ID |
| FriendlyName | string | 命令友好名称 |
| IsClientSupported | boolean | 此命令是否支持 ClientReferenceData |

#### 获取客户端参考数据 (GetClientReferenceData)
获取用于创建客户端支持命令的对话框选项的数据。

**请求示例：**
```json
{
  "AuthToken": "f95c9bc1-4aa1-d8ae-8bc3-28bef230df52",
  "Version": 2,
  "Name": "ClientReferenceData",
  "ContentBody": "[Command ID]"
}
```

**响应内容体：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| Name | string | 请求的命令ID |
| Text | string | 请求的命令友好名称 |
| Description | string | 请求的命令描述文本 |
| DialogueParameters | array | 检索指定命令的参数信息 |

**对话框参数结构：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| Type | string | 参数的对话框类型。可以是：Combo、MultiSelect、Text 或 Number |
| Name | string | 参数名称 |
| Id | string | 参数ID。用于为服务器创建请求数据 |
| DisplayMember | string | 参数的对话框选项。用于客户端视图 |
| ValueMember | string | 参数的对话框选项。用于服务器请求 |

#### 获取服务器变更列表 (GetServerChangelist)
检索服务器的变更列表构建号。

**响应：**
| 字段名 | 类型 | 描述 |
|--------|------|------|
| Changelist | string | 变更列表号 |

### 游戏时间和环境管理

#### 设置比赛计时器 (SetMatchTimer)
设置指定游戏模式的比赛时间（分钟）。对于攻防模式，比赛计时器是每个控制点阶段的长度。

**比赛计时器限制范围：**
- 战争模式：30-180 分钟
- 攻防模式：10-60 分钟
- 遭遇战：10-60 分钟

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| GameMode | string | 游戏模式 |
| MatchLength | Int32 | 比赛时长（分钟） |

#### 移除比赛计时器 (RemoveMatchTimer)
移除指定游戏模式的自定义比赛计时器。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| GameMode | string | 游戏模式 |

#### 设置热身计时器 (SetWarmupTimer)
为指定游戏模式设置热身计时器（分钟）。仅支持战争模式和遭遇战。

**热身计时器限制范围：** 1-10 分钟

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| GameMode | string | 游戏模式 |
| WarmupLength | Int32 | 热身时长（分钟） |

#### 移除热身计时器 (RemoveWarmupTimer)
移除指定游戏模式的自定义热身计时器。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| GameMode | string | 游戏模式 |

#### 设置动态天气启用 (SetDynamicWeatherEnabled)
为特定地图启用或禁用动态天气。命令仅对使用动态天气系统的地图有效。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| MapId | string | 地图ID |
| Enable | boolean | 是否启用 |

### 小队管理命令

#### 从小队中移除玩家 (RemovePlayerFromPlatoon)
查找并将玩家从其小队（班组）中移除。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| PlayerId | string | 玩家ID |
| Reason | string | 移除原因 |

#### 解散小队 (DisbandPlatoon)
查找并将所有玩家从小队（班组）中移除。

**参数：**
| 参数名 | 类型 | 描述 |
|--------|------|------|
| TeamIndex | uint8 | 队伍索引 |
| SquadIndex | Int32 | 班组索引 |
| Reason | string | 解散原因 |

## 使用注意事项

1. **认证要求**：所有命令都需要有效的 AuthToken，通过 Login 命令获取。
2. **版本兼容性**：确保使用正确的版本号（Version: 2）。
3. **数据加密**：所有通信都使用 XOR 加密，密钥为 "HLLRconV2"。
4. **错误处理**：始终检查响应中的 Status 字段以确认命令执行状态。
5. **连接管理**：保持连接活跃，避免超时断开。
6. **参数验证**：确保所有必需参数都已提供且格式正确。
7. **权限控制**：某些命令需要特定的管理员权限。
8. **数据类型**：注意参数的数据类型，特别是数字类型的区别（Int32、uint8等）。

## Python 连接示例

```python
import socket
import json
import struct

class HLLRconClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.auth_token = None
        self.xor_key = b"HLLRconV2"
    
    def connect(self):
        """连接到 RCON 服务器"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
    
    def xor_encrypt_decrypt(self, data):
        """XOR 加密/解密"""
        key_len = len(self.xor_key)
        return bytes([data[i] ^ self.xor_key[i % key_len] for i in range(len(data))])
    
    def send_command(self, command_name, content_body=""):
        """发送命令到服务器"""
        # 构建请求
        request = {
            "AuthToken": self.auth_token,
            "Version": 2,
            "Name": command_name,
            "ContentBody": content_body
        }
        
        # 转换为 JSON 并编码
        json_data = json.dumps(request).encode('utf-8')
        
        # XOR 加密
        encrypted_data = self.xor_encrypt_decrypt(json_data)
        
        # 添加包头（数据长度）
        packet_length = len(encrypted_data)
        header = struct.pack('<I', packet_length)
        
        # 发送数据
        self.socket.send(header + encrypted_data)
        
        # 接收响应
        response_header = self.socket.recv(4)
        response_length = struct.unpack('<I', response_header)[0]
        
        encrypted_response = self.socket.recv(response_length)
        decrypted_response = self.xor_encrypt_decrypt(encrypted_response)
        
        return json.loads(decrypted_response.decode('utf-8'))
    
    def login(self, password):
        """登录到 RCON 服务器"""
        response = self.send_command("Login", password)
        if response.get("Status") == "Success":
            self.auth_token = response.get("AuthToken")
            return True
        return False
    
    def get_server_info(self, info_type="players"):
        """获取服务器信息"""
        return self.send_command("GetServerInformation", info_type)
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()

# 使用示例
if __name__ == "__main__":
    client = HLLRconClient("localhost", 20300)
    
    try:
        # 连接服务器
        client.connect()
        print("已连接到服务器")
        
        # 登录
        if client.login("your_rcon_password"):
            print("登录成功")
            
            # 获取玩家信息
            players_info = client.get_server_info("players")
            print(f"当前在线玩家数: {len(players_info.get('Players', []))}")
            
            # 获取服务器配置
            server_config = client.get_server_info("serverconfig")
            print(f"服务器名称: {server_config.get('ServerName', 'Unknown')}")
            
        else:
            print("登录失败")
            
    except Exception as e:
        print(f"连接错误: {e}")
    
    finally:
        client.disconnect()
        print("连接已断开")
```

## 常见错误代码

| 状态码 | 描述 | 解决方案 |
|--------|------|----------|
| Success | 命令执行成功 | - |
| InvalidLogin | 登录失败 | 检查密码是否正确 |
| InvalidAuthToken | 认证令牌无效 | 重新登录获取新的令牌 |
| InvalidCommand | 无效命令 | 检查命令名称是否正确 |
| InvalidParameters | 参数无效 | 检查参数格式和类型 |
| InsufficientPermissions | 权限不足 | 确保管理员账户有相应权限 |
| ServerError | 服务器内部错误 | 检查服务器状态，稍后重试 |

## 最佳实践

1. **连接池管理**：对于频繁的 RCON 操作，考虑使用连接池来管理连接。
2. **异常处理**：始终包含适当的异常处理机制。
3. **日志记录**：记录所有 RCON 操作以便调试和审计。
4. **超时设置**：为网络操作设置合理的超时时间。
5. **数据验证**：在发送命令前验证所有输入数据。
6. **安全考虑**：保护 RCON 密码和认证令牌的安全。

---

**文档版本**：基于 Hell Let Loose RCON V2-1 API  
**最后更新**：2024年  
**适用版本**：Hell Let Loose RCON V2

这份文档提供了 Hell Let Loose RCON V2 API 的完整中文说明，包括所有命令的详细描述和使用方法。开发者可以根据这份文档来实现自己的 RCON 客户端应用程序。