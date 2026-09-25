# Phigros 4.0.0 包结构逆向研究笔记（非官方）

> 本项目为非官方玩家项目，与南京鸽游网络有限公司及《Phigros》官方不存在授权、合作或运营关系。

- 性质：个人学习研究 / 非商业 / 无付费功能 / 无广告变现 / 无商业导流
- 内容范围：仅包体结构、IL2CPP 方法学、章节与剧情概述
- **不含**：游戏资源文件、音乐、音频、曲绘、界面素材、谱面、程序本体
- **不提供**：解密工具、通行密钥、资源提取产物
- 剧透警告：包含剧情与彩蛋机制的概括性讨论
- AI 使用：本文由 AI 辅助生成，已由作者逐条核对；AI 可能出错，责任由发布者承担
- 权利归属：《Phigros》相关权利归南京鸽游网络有限公司；游戏内音乐、曲绘等归各自权利人

## 目录

- [研究笔记](docs/research-note.md)
- [发布合规检查清单](docs/compliance.md)
- [关于本站](docs/about.md)
- [部署说明](DEPLOY.md)

## 本地预览

```bash
pip install -r requirements.txt
mkdocs serve          # 打开 http://127.0.0.1:8000
```

## 发布

```powershell
python scripts/publish.py      # 替换占位符 → 配置身份 → 合规检查 → 提交 → 推送
```

推送后 GitHub Actions 会自动构建并发布到 GitHub Pages。
首次使用需在仓库 **Settings → Pages → Source** 选择 **GitHub Actions**。

详细步骤见 [DEPLOY.md](DEPLOY.md)。

## ⚠️ 提交前必读

本仓库是**公开**仓库。`.gitignore` 中已内置针对游戏资源、密钥与解密脚本的拦截规则，
CI 中另有一道产物扫描门禁。**请勿**通过 `git add -f` 等方式绕过这些规则。
发布范围与依据见 [发布合规检查清单](docs/compliance.md)。
