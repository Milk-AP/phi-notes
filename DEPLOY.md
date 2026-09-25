# 部署说明

本站是 **MkDocs Material** 静态站点，通过 **GitHub Actions** 自动构建并发布到 **GitHub Pages**。
推送 `main` 分支即自动上线，无需手动构建。

---

## 一、上线前：替换 6 处占位符

> `scripts/publish.py` 会自动完成这一步（见第三节），本节保留供手动操作与核对。

项目里所有需要改成你自己账号的地方都用了 `USERNAME` / `REPO` 占位。

| 文件 | 出现位置 | 说明 |
|---|---|---|
| `mkdocs.yml` | `site_author` | 替换 `USERNAME` |
| `mkdocs.yml` | `site_url` | 形如 `https://你的用户名.github.io/仓库名/` |
| `mkdocs.yml` | `repo_url` | 形如 `https://github.com/你的用户名/仓库名` |
| `mkdocs.yml` | `repo_name` | 形如 `你的用户名/仓库名`（显示在右上角） |
| `mkdocs.yml` | `extra.social[0].link` | 同 `repo_url` |
| `docs/about.md` | Issue 链接 | 同 `repo_url` + `/issues` |

> 站点路径必须与仓库名一致：若仓库名是 `phi-notes`，
> 则 `site_url` 为 `https://USERNAME.github.io/phi-notes/`。
> 若你把仓库命名为 `USERNAME.github.io`，则改为 `https://USERNAME.github.io/`。

---

## 二、本地预览（可选，推荐先看一眼）

```powershell
cd d:\boke
python -m pip install -r requirements.txt
python -m mkdocs serve
```

浏览器打开 <http://127.0.0.1:8000> 即可实时预览，改文件会自动刷新。

只构建不启动服务器：

```powershell
python -m mkdocs build --clean     # 产物在 site\
```

---

## 三、发布（一条命令 + 点一下按钮）

全程使用 **VS Code 已登录的 GitHub 账号**，不需要安装 `gh` CLI，也不需要手工创建 PAT。

### 1. 运行发布向导

```powershell
cd d:\boke
python scripts/publish.py
```

它会依次询问 **GitHub 用户名**、**仓库名**（默认 `phi-notes`）、**提交邮箱**
（默认 `用户名@users.noreply.github.com`），然后自动完成：

| 步骤 | 动作 |
|---|---|
| 1 | 把 `mkdocs.yml`（5 处）与 `docs/about.md`（1 处）里的 `USERNAME` / `REPO` 换成你的信息 |
| 2 | 用 `--local` 配置本仓库的 Git 身份，**不影响你其它仓库** |
| 3 | 运行 `scripts/check_assets.py` 做内容合规检查，不通过就中止 |
| 4 | `git add -A` 并提交 |
| 5 | 配置 `origin` 并尝试推送 |

不想交互也可以直接传参：

```powershell
python scripts/publish.py --user 你的用户名 --repo phi-notes
python scripts/publish.py --user 你的用户名 --repo phi-notes --no-push   # 只提交不推送
```

### 2. 若推送失败：用 VS Code 发布分支

推送失败**几乎只有一个原因**：GitHub 上还没有这个仓库。这是唯一需要你动手的地方：

1. 打开左侧 **源代码管理** 面板（`Ctrl+Shift+G`）
2. 点击蓝色按钮 **「发布分支 / Publish Branch」**
3. VS Code 会用你已登录的 GitHub 账号**自动创建仓库并推送**

> 想手动也可以：到 <https://github.com/new> 建仓库（名字与脚本里填的一致，
> 可见性选 **Public**，**不要**勾选 README / .gitignore / License），
> 然后重跑 `git push -u origin main`。

### 3. 开启 Pages

推送完成后进入仓库 **Settings → Pages**：

- **Source** 选择 **GitHub Actions**（不要选 "Deploy from a branch"）

随后到 **Actions** 标签页，可以看到「构建并部署站点到 GitHub Pages」工作流正在运行。
首次执行约 1–2 分钟，完成后访问：

```
https://你的用户名.github.io/仓库名/
```

---

## 四、日常更新

```powershell
cd d:\boke
# 改文档……
git add -A
git commit -m "更新：xxx"
git push
```

推送后 Actions 会自动重新构建发布。

---

## 五、内容安全门禁

本项目有三道防线，确保公开站点**只包含白名单内容**：

| # | 防线 | 位置 |
|---|---|---|
| 1 | `.gitignore` 拦截资源扩展名、密钥文件名、`analysis/`、`extracted/` | 仓库根目录 |
| 2 | `scripts/check_assets.py` 扫描 `docs/`，发现资源文件即退出码 1 | 本地手动跑 / CI 自动跑 |
| 3 | GitHub Actions 在 **构建前**调用该脚本，不通过则流水线失败、不会发布 | `.github/workflows/deploy.yml` |

本地推送前建议先跑一次：

```powershell
python scripts/check_assets.py docs
```

预期输出：`[通过] 未发现资源文件或含敏感特征的文件名。`

> 依据见 [发布合规检查清单](docs/compliance.md)。
> **请勿**用 `git add -f` 绕过 `.gitignore` —— 那会让 CI 门禁成为唯一防线，
> 而一旦推送到公开仓库，内容就可能已被缓存或 fork，无法撤回。

---

## 六、私密仓库（分析全量资料）

分析过程中产生的**密钥、解密实现、资源导出、未公开数据**等，
**不在**本仓库中，也不会随站点发布。

如需把这些资料也纳入版本管理，请使用**独立的 Private 仓库**，
详见 `d:\phi\PRIVATE_REPO.md`（含体积分析、`.gitignore` 与初始化脚本）。

要点：

- `d:\phi` 全量 10.36 GB，其中 APK（2.67 GB）超 GitHub 单文件 100 MB 限制，必须排除；
- 2606 个 bundle 被存了三份，去重后可省约 4.9 GB；
- 处理后约 **2.8 GB**，可放入私有仓库；
- **两边的 `.gitignore` 规则相反，绝不要合并成一个仓库。**

---

## 七、常见问题

**Q：Actions 报 `python scripts/check_assets.py` 失败？**
说明 `docs/` 里混入了图片或其他资源文件。检查是不是把截图、示意图当作图片放了进去。
本站的示意图全部是 **Mermaid 文本图**，不需要任何位图文件。

**Q：页面 404 / 样式丢失？**
多半是 `site_url` 与仓库名不一致。GitHub Pages 的站点在子路径下，
`site_url` 必须包含仓库名那一段。

**Q：Mermaid 图不显示？**
`mkdocs.yml` 中已配置 `pymdownx.superfences` 的 `custom_fences`，
Material 主题会把它渲染成图表。若被改动请对照原始配置恢复。

**Q：想加文章？**
把 Markdown 放进 `docs/`，再到 `mkdocs.yml` 的 `nav:` 里加一行即可。
建议在 `docs/` 内新建子目录分类，例如 `docs/posts/`。
