#!/usr/bin/env python3
"""
Синхронизирует React build из admin-panel/build в frontend/build,
не удаляя frontend/build/miniapp.

Почему так:
- frontend/build используется как корень статики
- miniapp хранится внутри frontend/build/miniapp и должен сохраняться при обновлении панели
"""

import os
import shutil
import sys


def copy_any(src: str, dst: str) -> None:
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_dir = os.path.join(root, "admin-panel", "build")
    dst_dir = os.path.join(root, "frontend", "build")

    if not os.path.isdir(src_dir):
        print(f"❌ Source build folder not found: {src_dir}")
        return 2
    if not os.path.isdir(dst_dir):
        print(f"❌ Destination folder not found: {dst_dir}")
        return 2

    keep_name = "miniapp"

    # Удаляем всё в dst, кроме miniapp
    for name in os.listdir(dst_dir):
        if name == keep_name:
            continue
        path = os.path.join(dst_dir, name)
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except FileNotFoundError:
            pass

    # Копируем build
    for name in os.listdir(src_dir):
        src = os.path.join(src_dir, name)
        dst = os.path.join(dst_dir, name)
        copy_any(src, dst)

    print(f"✅ Synced {src_dir} -> {dst_dir} (preserved {keep_name}/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

