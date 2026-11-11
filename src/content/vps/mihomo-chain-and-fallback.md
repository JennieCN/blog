---
title: Mihomo 链式与回退：三个配置陷阱
description: 对照 Mihomo v1.19.34 源码，分清组级 dialer-proxy 不生效、节点全失败与空列表回退，避免把配置加载成功当成路径正确。
pubDate: 2026-11-12
tags: [VPS, Mihomo, 链式代理, 源码]
---

配置能加载、节点能测速，并不代表请求真的经过预想的前置，也不代表失败时一定拒绝连接。

这篇对照 **Mihomo 官方发布标签 `v1.19.34`** 的实现，讲三个容易混淆的分支。它不表示所有客户端或旧版本都有相同行为。拓扑选择见[线路与落地搭配](/vps/relay-and-egress-guide/)，测速判断见[测评与成本](/vps/reading-vps-reviews/)。

## 陷阱一：把 dialer-proxy 写在策略组上

Mihomo 文档的用法是：让具体出站节点通过另一个出站或策略组建立连接。下面只示意字段位置，不是可直接运行的完整配置：

```yaml
proxies:
  - name: 落地节点
    # 这里省略节点类型和认证参数
    dialer-proxy: 前置选择

proxy-groups:
  - name: 前置选择
    type: select
    proxies:
      - 前置节点
```

不要将 `dialer-proxy` 移到 `前置选择` 这个组的字段中，以为它会给整组加一层前置。

在 `v1.19.34` 的 `ParseProxyGroup` 中，遇到组级 `dialer-proxy` 会记录错误日志，但该分支本身没有返回解析错误，也不建立预期链路。**因此，配置可能继续加载，但这个字段没有实现你想要的链式。**

同一版本遇到旧 `relay` 组类型，则直接返回不支持错误。两个问题的处理方式不同。[组字段处理源码](https://github.com/MetaCubeX/mihomo/blob/v1.19.34/adapter/outboundgroup/parser.go#L44-L76)、[relay 类型处理](https://github.com/MetaCubeX/mihomo/blob/v1.19.34/adapter/outboundgroup/parser.go#L171-L204)

链式还需要前置支持后置协议所需的传输。字段位置正确，不等于任意 TCP、UDP 协议组合都能工作。[官方链式文档](https://wiki.metacubex.one/config/proxies/dialer-proxy/)

## 陷阱二：把全部探测失败当成自动拒绝

通常未指定固定选择时，fallback 按顺序寻找探测可用的节点。但如果节点列表仍非空，而全部节点的健康状态都不通过，`findAliveProxy` 最终返回的是列表首项。

这不是自动返回 REJECT，也不是对当前业务请求逐一尝试所有节点。后续连接结果仍取决于被选中的出站。[fallback 源码](https://github.com/MetaCubeX/mihomo/blob/v1.19.34/adapter/outboundgroup/fallback.go#L98-L117)

因此，健康检查与业务请求要分开理解。某个探测网址可用，不保证另一个目标服务、UDP 连接或账号功能可用。

## 陷阱三：忽略组内节点列表为空

过滤条件没有匹配节点，或订阅更新后没有可用的列表项，与“列表存在但节点全部探测失败”不同。

在 `v1.19.34` 中：

1. `GroupBase.GetProxies` 发现最终列表为空，返回 `empty-fallback`；
2. 未填写该选项时，解析器默认使用 `COMPATIBLE`；
3. `NewCompatible` 返回 Direct 实现，可能产生直连。

所以，**没有在代理组列表中写 DIRECT，不足以证明组为空时不会直出。** 如果这个组用于中间拨号，直连还可能表现为绕过原定前置，而不是直接访问最终网站。[空列表处理](https://github.com/MetaCubeX/mihomo/blob/v1.19.34/adapter/outboundgroup/groupbase.go#L184-L220)、[默认值](https://github.com/MetaCubeX/mihomo/blob/v1.19.34/adapter/outboundgroup/parser.go#L63-L76)、[Direct 实现](https://github.com/MetaCubeX/mihomo/blob/v1.19.34/adapter/outbound/direct.go#L21-L99)

要求空列表时拒绝，可在支持该选项的版本给对应组显式设置：

```yaml
empty-fallback: REJECT
```

这个字段只约束空列表分支，不修复组级 `dialer-proxy`，也不替代规则、其他回退组和应用自身连接方式的检查。

## 把出口策略写清楚

普通浏览可能优先要求能连上；需要特定地区或固定出口的服务，则应使用指定出口或明确允许的备用。两类用途可以有不同的失败策略。

同样，自动切换也不自动保存原有会话，更不等于带宽叠加。出口 IP 改变后，应用连接可能需要重新建立。

采用论坛配置时，先核对客户端核心版本和字段语义，再确认生效路径。一次 YAML 检查或测速成功，只证明它实际检查的那一部分，不能代替链路与失败分支验证。
