---
title: 查找容器真实日志路径
summary: 从容器配置读取 LogPath，并核对日志驱动与轮转文件。
module: Forensics
track: 服务器取证
topic: 日志与存储
tags: [Docker, 日志]
status: 已整理
sourceIds: [2530fdc7be10]
updated: 2026-09-29
---

## 先问运行时

Docker 的 `json-file` 日志常见于容器目录，但实际位置受运行时、数据根目录和日志驱动影响。用当前容器的配置取证：

```bash
docker inspect --format '{{.HostConfig.LogConfig.Type}} {{.LogPath}}' CONTAINER_ID
```

再检查所指路径及轮转文件；如果 `LogPath` 为空，查看日志驱动，并寻找 journald、容器运行时或 Kubernetes 日志位置。需要证明“某次请求发生过”时，把日志时间、容器 ID、服务配置和其他证据对应起来。
