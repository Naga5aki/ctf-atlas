// 题型入口保持少而明确；原有 topic 仍用于文章归档和检索。
export const forensicsTaxonomy = [
  {
    id: 'computer', name: '计算机取证', summary: '磁盘、系统痕迹与程序。',
    lead: 'forensic-guide-computer',
    route: ['确认镜像与分区', '定位系统和用户痕迹', '用日志、内存交叉核验'],
    clusters: [
      { name: '磁盘与文件系统', topics: ['镜像与文件系统'] },
      { name: '文件系统取证', topics: ['卷与引导扇区', 'NTFS', 'FAT', 'exFAT', 'ext', '其他文件系统', '图形工具'] },
      { name: '系统行为与程序', topics: ['系统与用户痕迹', '程序与恶意代码'] },
    ],
  },
  {
    id: 'memory', name: '内存取证', summary: '采集识别、运行行为、对象恢复与工具速查。',
    lead: 'forensic-memory',
    route: ['固定采集条件并匹配符号', '关联进程、连接和内存对象', '恢复数据并与磁盘、日志互证'],
    clusters: [
      { name: '采集与识别', topics: ['采集与识别'] },
      { name: '进程与攻击行为', topics: ['进程与攻击行为'] },
      { name: '对象与数据恢复', topics: ['对象与数据恢复'] },
      { name: 'Linux 与 macOS', topics: ['Linux 与 macOS'] },
      { name: '工具参数与插件', topics: ['工具参数与插件'] },
      { name: '综合实战', topics: ['综合实战'] },
    ],
  },
  {
    id: 'server', name: '服务器取证', summary: '主机、应用、容器、集群与云端。',
    lead: 'forensic-guide-server',
    route: ['确定主机与服务范围', '关联容器、集群与持久数据', '复核日志、业务与云记录'],
    clusters: [
      { name: '主机与应用', topics: ['主机与服务', 'Web 与数据库'] },
      { name: '网站重构', topics: ['网站重构'] },
      { name: 'Docker 与容器', topics: ['Docker 与容器'] },
      { name: '服务器集群', topics: ['服务器集群'] },
      { name: '版本与云环境', topics: ['版本与源码', '云与虚拟化'] },
    ],
  },
  {
    id: 'mobile', name: '手机取证', summary: '设备、备份与应用通信。',
    lead: 'forensic-guide-mobile',
    route: ['确定设备和提取方式', '还原备份及应用数据', '校准账号、时间和同步范围'],
    clusters: [
      { name: 'Android 取证', topics: ['Android 原理与流程', 'Android', 'Android 工具与实战'] },
      { name: 'iOS 取证', topics: ['iOS 原理与流程', 'iOS 与备份', 'iOS 工具与实战'] },
      { name: '应用与通信', topics: ['应用与通信'] },
    ],
  },
  {
    id: 'network', name: '网络取证', summary: '流量、连接与协议。',
    lead: 'forensic-guide-network',
    route: ['校准抓包覆盖范围', '梳理会话和协议字段', '与终端、服务器记录互证'],
    clusters: [
      { name: '流量与协议', topics: ['流量与协议'] },
      { name: '连接与隧道', topics: ['连接与隧道'] },
    ],
  },
  {
    id: 'crypto-assets', name: '虚拟币取证', summary: '钱包、链上交易、平台账本与资金追踪。',
    lead: 'fic-case-12',
    route: ['固定设备与钱包证据', '核对网络、资产及有效移动', '追踪资金并复核账本与归属'],
    clusters: [
      { name: '基础与证据', topics: ['基础与证据'] },
      { name: '钱包与控制权', topics: ['钱包与本地痕迹'] },
      { name: '链上交易', topics: ['UTXO 交易', '账户链与代币'] },
      { name: '资金追踪与实战', topics: ['平台与资金追踪', '账本复核与实战'] },
    ],
  },
  {
    id: 'files', name: '文件与多媒体取证', summary: '恢复文件，检查文档与媒体。',
    lead: 'forensic-guide-files',
    route: ['识别真实格式与结构', '恢复或提取目标内容', '验证完整性与关联证据'],
    clusters: [
      { name: '文件与文档', topics: ['文件恢复与格式', '文档与隐写'] },
      { name: '图像、音频与视频', topics: ['图像音视频'] },
    ],
  },
] as const;

// 跨题型内容独立放在页面末尾。
export const forensicsMethods = {
  id: 'methods', name: '通用方法', sourceTrack: '综合取证',
  summary: '证据保全、时间线与速查。',
  clusters: [
    { name: '方法与索引', topics: ['证据保全与流程', '时间线与关联'] },
    { name: '密码与资金', topics: ['密码与资金'] },
    { name: '工具与路径', topics: ['工具与路径'] },
  ],
} as const;

// 六类独立操作稿共享已有专题ID；分类入口直接跳到对应正文，不复制知识点。
export const websiteRecoveryRoutes = [
  { label: 'PHP：恢复宝塔商城', anchor: '01-php恢复宝塔商城' },
  { label: 'Java：恢复站点机与数据库机', anchor: '02-java恢复站点机与数据库机' },
  { label: 'Python：恢复原虚拟环境与业务入口', anchor: '03-python恢复原虚拟环境与业务入口' },
  { label: 'Node.js：分清静态前端与真正后端', anchor: '04-nodejs分清静态前端与真正后端' },
  { label: 'IIS：恢复绑定、应用程序池与数据库', anchor: '05-iis恢复绑定应用程序池与数据库' },
  { label: '静态站：恢复页面，并识别它背后的接口', anchor: '06-静态站恢复页面并识别它背后的接口' },
] as const;
