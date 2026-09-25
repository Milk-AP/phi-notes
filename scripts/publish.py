#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键发布站点到 GitHub Pages。

它会自动完成从「占位符」到「推送」的全部准备步骤：

  1. 收集 GitHub 用户名 / 仓库名 / 提交邮箱
  2. 替换 mkdocs.yml 与 docs/about.md 中的 USERNAME、REPO 占位符
  3. 配置本仓库的 Git 身份（使用 --local，不影响你其它仓库）
  4. 运行内容合规检查（scripts/check_assets.py），不通过则不提交
  5. git add -A 并提交
  6. 配置 origin 并尝试推送

推送所需的 GitHub 凭据由 VS Code / Git 凭据管理器弹出授权窗口，脚本不接触任何令牌。

如果推送失败，几乎都是因为「GitHub 上还没有这个仓库」。此时改用 VS Code：
    源代码管理面板 → 「发布分支 / Publish Branch」
VS Code 会用你已登录的 GitHub 账号自动创建仓库并推送，无需再输入任何信息。

用法：
    python scripts/publish.py --user 用户名 --repo 仓库名
    python scripts/publish.py                  # 交互式逐个询问
    python scripts/publish.py --no-push        # 只提交，不推送
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - 仅用于兼容异常终端
    pass

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_FILES = (ROOT / "mkdocs.yml", ROOT / "docs" / "about.md")
COMMIT_MESSAGE = "初始化：Phigros 4.0.0 包结构逆向研究笔记站点"
DEFAULT_REPO = "phi-notes"


def sh(args: list[str], quiet: bool = False) -> int:
    """在仓库根目录执行命令并回显，返回退出码。"""
    if not quiet:
        print("  $ " + " ".join(args))
    return subprocess.run(
        args, cwd=str(ROOT), text=True, encoding="utf-8", errors="replace",
    ).returncode


def out(args: list[str]) -> str:
    """执行命令并安静地取回输出。"""
    r = subprocess.run(
        args, cwd=str(ROOT), text=True, encoding="utf-8",
        errors="replace", capture_output=True,
    )
    return ((r.stdout or "") + (r.stderr or "")).strip()


def ask(prompt: str, default: str = "") -> str:
    hint = f"（默认 {default}）" if default else ""
    try:
        value = input(f"{prompt}{hint}：").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""
    return value or default


def replace_placeholders(user: str, repo: str) -> int:
    """把站点文件里的 USERNAME / REPO 占位符换成真实值，返回替换处数。"""
    total = 0
    for path in PLACEHOLDER_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        text, n_user = re.subn(r"\bUSERNAME\b", user, text)
        text, n_repo = re.subn(r"\bREPO\b", repo, text)
        if n_user or n_repo:
            path.write_text(text, encoding="utf-8")
            rel = path.relative_to(ROOT)
            print(f"  ✓ {rel}：USERNAME×{n_user}、REPO×{n_repo}")
            total += n_user + n_repo
    return total


def print_push_help(user: str, repo: str) -> None:
    bar = "=" * 66
    print(
        f"""
{bar}
 推送失败 —— 最常见的原因是 GitHub 上还没有这个仓库
{bar}

 方式 A（推荐）：用 VS Code 已登录的 GitHub 账号自动建仓库
     1. 打开左侧「源代码管理」面板（Ctrl+Shift+G）
     2. 点击蓝色按钮「发布分支 / Publish Branch」
     VS Code 会自动创建 {repo} 并推送，无需再输入用户名或密码。

 方式 B：手动建仓库后再推送
     1. 打开 https://github.com/new
     2. 仓库名填 {repo}，可见性选 Public，
        不要勾选 "Add a README file" / ".gitignore" / "License"
     3. 回到终端重跑：
        git push -u origin main
"""
    )


def print_next_steps(user: str, repo: str) -> None:
    bar = "=" * 66
    print(
        f"""
{bar}
 还差两步（都在 GitHub 网页上完成）
{bar}

 1) 仓库 → Settings → Pages → Source 选择「GitHub Actions」

 2) 等 Actions 跑完（约 1~2 分钟），访问站点：
      https://{user}.github.io/{repo}/

 私密仓库（分析全量资料）另见 d:\\phi\\PRIVATE_REPO.md
"""
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="一键发布站点到 GitHub Pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--user", help="GitHub 用户名")
    parser.add_argument("--repo", help=f"GitHub 仓库名（默认 {DEFAULT_REPO}）")
    parser.add_argument("--email", help="Git 提交邮箱（默认用 GitHub noreply 邮箱）")
    parser.add_argument("--no-push", action="store_true", help="只提交，不推送")
    args = parser.parse_args()

    bar = "=" * 66
    print(f"{bar}\n 站点发布向导 —— {ROOT}\n{bar}")

    # --- 1/6 收集信息 --------------------------------------------------
    print("\n[1/6] 收集信息……")
    user = args.user or ask("  GitHub 用户名")
    if not user:
        print("\n[中止] 必须提供 GitHub 用户名。")
        return 2
    repo = args.repo or ask("  仓库名", DEFAULT_REPO)
    email = args.email or ask("  提交邮箱", f"{user}@users.noreply.github.com")

    # --- 2/6 检查环境 --------------------------------------------------
    print("\n[2/6] 检查环境……")
    version = out(["git", "--version"])
    if not version:
        print("\n[中止] 找不到 git，请先安装 Git for Windows。")
        return 2
    print(f"      {version}")
    sh(["git", "config", "core.quotepath", "false"], quiet=True)

    if not (ROOT / ".git").exists():
        print("      尚未初始化仓库，正在 git init……")
        if sh(["git", "init", "-b", "main"]) != 0:
            return 1
    else:
        print("      仓库已初始化。")

    # --- 3/6 替换占位符 ------------------------------------------------
    print("\n[3/6] 替换占位符……")
    if replace_placeholders(user, repo) == 0:
        print("  （没有找到占位符，可能之前已经替换过）")

    # --- 4/6 配置身份 + 合规检查 ---------------------------------------
    print("\n[4/6] 配置身份并做合规检查……")
    sh(["git", "config", "--local", "user.name", user], quiet=True)
    sh(["git", "config", "--local", "user.email", email], quiet=True)
    print(f"      提交身份：{user} <{email}>")

    checker = ROOT / "scripts" / "check_assets.py"
    if checker.exists():
        if subprocess.run([sys.executable, str(checker), "docs"], cwd=str(ROOT)).returncode != 0:
            print("\n[中止] docs/ 中存在不允许公开的文件，未执行提交。")
            return 1
    else:
        print("      （未找到 check_assets.py，跳过）")

    # --- 5/6 提交 ------------------------------------------------------
    print("\n[5/6] 提交……")
    sh(["git", "add", "-A"])
    if subprocess.run(
        ["git", "commit", "-m", COMMIT_MESSAGE],
        cwd=str(ROOT), text=True, encoding="utf-8", errors="replace",
    ).returncode != 0:
        print("      （没有新的变更需要提交）")

    # --- 6/6 推送 ------------------------------------------------------
    if args.no_push:
        print("\n[6/6] 已按 --no-push 跳过推送。")
        print_next_steps(user, repo)
        return 0

    print("\n[6/6] 推送……")
    url = f"https://github.com/{user}/{repo}.git"
    if out(["git", "remote", "get-url", "origin"]):
        sh(["git", "remote", "set-url", "origin", url], quiet=True)
    else:
        sh(["git", "remote", "add", "origin", url], quiet=True)
    print(f"      origin → {url}")
    print("      （若弹出 GitHub 授权窗口，请完成登录）")

    if subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=str(ROOT), text=True, encoding="utf-8", errors="replace",
    ).returncode == 0:
        print("      ✓ 推送成功")
    else:
        print("      ✗ 推送失败")
        print_push_help(user, repo)
        return 1

    print_next_steps(user, repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
