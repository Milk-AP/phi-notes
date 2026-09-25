#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
站点内容合规门禁：确保 docs/ 中不含任何游戏资源文件。

依据《Phigros》同人创作及第三方项目规范（2026 版）第三条、第五条、第六条：
本仓库为**公开**站点，不得包含或分发游戏资源文件、音乐、音频、曲绘、界面素材、
谱面、程序本体，也不得包含密钥 / 解密实现 / 未公开数据。

这个脚本是「白名单发布」的自动化保障：GitHub Actions 在构建前会调用它，
本机推送前也建议先跑一次。

用法：
    python scripts/check_assets.py            # 默认检查 docs/
    python scripts/check_assets.py <目录>

退出码：0 = 通过，1 = 发现违规文件，2 = 目录不存在
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 一律不得进入公开站点的扩展名
# ---------------------------------------------------------------------------
FORBIDDEN_SUFFIXES: frozenset[str] = frozenset({
    # 图像 / 美术素材（曲绘、插画、界面图、贴图……）
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tga", ".psd", ".tif", ".tiff",
    # 音频
    ".wav", ".ogg", ".mp3", ".flac", ".aiff", ".m4a",
    # 视频
    ".mp4", ".webm", ".mov", ".avi",
    # 资源包 / 程序本体 / 反编译与解包产物
    ".bundle", ".apk", ".xapk", ".obb", ".assets", ".resource",
    ".so", ".dll", ".dex", ".arsc", ".dat",
})

# ---------------------------------------------------------------------------
# 文件名中含这些特征词的，一律拦截（密钥 / 解密实现 / 未公开数据）
# ---------------------------------------------------------------------------
FORBIDDEN_NAME_PARTS: tuple[str, ...] = (
    "decrypt",
    "password",
    "密钥",
    "未公开数据",
    "c9_secret",
)


def main(argv: list[str]) -> int:
    # 控制台可能是 GBK 代码页，显式固定输出编码，避免中文报 UnicodeEncodeError
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

    root = Path(argv[1]) if len(argv) > 1 else Path("docs")
    if not root.is_dir():
        print(f"[错误] 目录不存在：{root}")
        return 2

    violations: list[tuple[Path, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            violations.append((path, f"禁止的扩展名 {path.suffix}"))
            continue
        lowered = path.name.lower()
        for part in FORBIDDEN_NAME_PARTS:
            if part in lowered:
                violations.append((path, f"文件名含敏感特征「{part}」"))
                break

    print(f"检查目录：{root.resolve()}")
    if violations:
        print(f"[失败] 发现 {len(violations)} 个不允许公开的文件：")
        for path, reason in violations:
            print(f"  - {path}  （{reason}）")
        return 1

    print("[通过] 未发现资源文件或含敏感特征的文件名。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
