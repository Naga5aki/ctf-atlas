---
title: Docker 服务器取证首轮定位
summary: 先保全，再确认运行时、容器、日志和持久化数据的位置。
module: Forensics
track: 服务器取证
topic: 主机与服务
tags: [Docker, 日志]
status: 已整理
sourceIds: [2530fdc7be10, c7613f4a6214]
updated: 2026-09-29
---

## 五分钟顺序

1. 记录系统时间、主机信息和已知检材来源，保留原始日志或磁盘副本。
2. 识别实际运行时：Docker、containerd，或 Kubernetes 节点的 CRI。
3. 列出容器、镜像与状态，记录容器 ID、创建和退出时间。
4. 用 `docker inspect` 确认日志驱动、`LogPath`、挂载和网络配置。
5. 将容器、卷、镜像和宿主机路径联系起来，再进入具体文件分析。

```bash
docker ps -a --no-trunc
docker info
docker inspect CONTAINER_ID
```

如果现场没有 Docker daemon，先转到 `crictl` / containerd 视角；不要假定每台 Kubernetes 节点都有 `/var/lib/docker`。
