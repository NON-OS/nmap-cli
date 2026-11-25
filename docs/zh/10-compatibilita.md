# 兼容性与测试

🌐 [Italiano](../10-compatibilita.md) · [English](../en/10-compatibilita.md) · **中文**

> ⚠️ 本页为机器翻译草稿，正式发布前需母语者校对。

本页说明哪些内容已针对真实的 nmap 验证过，哪些没有。这不是一份承诺清单。

**测试版本：** nmap 7.993，通过 Homebrew 安装于 macOS arm64。

## 已验证的内容

1. **配置中的标志确实存在。** 配置中用到的每个标志都在 nmap 7.993 的帮助信息和手册页中查证过：没有未知标志。
2. **被禁标志确实存在。** 被禁列表同样经过比对。其中两个名称是凭空编造的（`--proxy`、`--interactive`），已被删除。另一方面，`-sC` 和 `-A` 会启用 `default` 脚本，从而绕过对 `--script` 的拦截：现已列为被禁。
3. **真实运行可用。** `scoperta`、`rapido`、`servizi` 和 `script-sicuri` 均以 `--esegui` 在 `127.0.0.1` 上实际运行过；`rapporto` 读取了真实的 XML，`confronta` 对两次相同的扫描给出了“Nessuna differenza”（无差异）。
4. **审计。** 真实运行之后，哈希链校验完整。
5. **stdin 已关闭。** 子进程不继承 stdin。nmap 只有在使用 `-iL -` 时才从 stdin 读取目标，而该标志已被禁，但这条规则依然适用；有一个使用伪造可执行文件的测试。
6. **Python 与安装。** 测试在 macOS 上的 Python 3.11.18 和 3.13、Linux 上的 3.12.3 下通过。在全新 venv 中用 `pip install .` 干净安装，包括命令进入 PATH。
7. **类型。** `mypy --strict` 在 `src/` 中未发现错误。这不能证明正确性，但能额外检查参数或返回值实际可能是什么；它已纳入 CI，因此一旦出问题就会有测试报出来。
8. **二进制文件是对的。** `doctor` 和 `--esegui` 会检查 `--version` 的输出中确实包含“Nmap version”：PATH 中可能混进另一个名为 `nmap` 的程序。已分别用真实可执行文件（接受）和一个输出其他字符串的伪造程序（拒绝，退出码 5，审计日志中不写入任何内容）测试过。
9. **报告中的目标数据。** 主机名、服务和版本来自目标的响应，而不是来自发起扫描的人。`rapporto` 在把它们写入文本或 Markdown 报告之前，会去掉控制字符（包括换行符）并转义 `|`，因此恶意 banner 无法注入伪造的行、标题或列。已用包含换行符和伪造标题 `## ...` 的主机名和版本测试过：它们仍是单行文本。详见 [08-rapporti.md](08-rapporti.md#hostname-servizi-e-versioni-sono-dati-del-bersaglio-non-testo-fidato)。
10. **CI 本身。** GitHub Action 固定到提交的 SHA，而不是 `@v4` 这样可变动的标签：控制某个 action 上游仓库的人，无法在我们的 workflow 不改一行的情况下让它指向别处。`ruff format --check` 防止代码风格随时间漂移。`coverage` 衡量测试实际覆盖了多少代码：低于 85% 时 CI 失败，实际值为 89%。

## 未验证的内容

`os` 和 `udp-top` 需要 root，未运行过。`tcp-completo` 未完整运行过。各配置只在 `127.0.0.1` 上测试过，因此我不知道它们在有防火墙和速率限制的真实网络上表现如何。报告不读取 NSE 脚本的输出。

## 如果你使用其他版本

标志和 XML 格式在不同版本之间会有变化。在信任它之前，先运行 `make check`，并在你自己的目标上做一次试运行。如果你发现某个标志能绕过作用域却不在被禁列表中，那就是一个漏洞：参见 [SECURITY.md](../../SECURITY.md)。
