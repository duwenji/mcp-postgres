#!/usr/bin/env python3
"""
バージョン管理スクリプト

このスクリプトはpyproject.tomlのバージョン番号を更新します。
セマンティックバージョニングに従って、メジャー、マイナー、パッチの更新が可能です。
"""

import re
import sys
import argparse
from pathlib import Path


def get_current_version():
    """現在のバージョン番号を取得"""
    pyproject_path = Path("pyproject.toml")
    
    if not pyproject_path.exists():
        print("エラー: pyproject.tomlが見つかりません")
        sys.exit(1)
    
    content = pyproject_path.read_text(encoding="utf-8")
    
    # バージョン番号の抽出
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not version_match:
        print("エラー: バージョン番号が見つかりません")
        sys.exit(1)
    
    return version_match.group(1)


def update_version(new_version):
    """バージョン番号を更新"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")
    
    # バージョン番号の更新
    old_content = content
    content = re.sub(
        r'version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        content
    )
    
    if content == old_content:
        print("エラー: バージョン番号の更新に失敗しました")
        sys.exit(1)
    
    # ファイルへの書き込み
    pyproject_path.write_text(content, encoding="utf-8")
    print(f"バージョンを {get_current_version()} から {new_version} に更新しました")


def parse_version(version_str):
    """バージョン文字列をパース"""
    try:
        parts = version_str.split(".")
        if len(parts) != 3:
            raise ValueError("バージョンは major.minor.patch 形式である必要があります")
        
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
        
        return major, minor, patch
    except ValueError as e:
        print(f"エラー: 無効なバージョン形式 - {e}")
        sys.exit(1)


def increment_version(current_version, increment_type):
    """バージョン番号をインクリメント"""
    major, minor, patch = parse_version(current_version)
    
    if increment_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif increment_type == "minor":
        minor += 1
        patch = 0
    elif increment_type == "patch":
        patch += 1
    else:
        print(f"エラー: 無効なインクリメントタイプ: {increment_type}")
        sys.exit(1)
    
    return f"{major}.{minor}.{patch}"


def validate_new_version(new_version):
    """新しいバージョン番号の検証"""
    try:
        parse_version(new_version)
        return True
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="pyproject.tomlのバージョン番号を更新",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --current                   現在のバージョンを表示
  %(prog)s --patch                     パッチバージョンをインクリメント (0.1.0 → 0.1.1)
  %(prog)s --minor                     マイナーバージョンをインクリメント (0.1.0 → 0.2.0)
  %(prog)s --major                     メジャーバージョンをインクリメント (0.1.0 → 1.0.0)
  %(prog)s --set 1.2.3                 特定のバージョンに設定
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--current", action="store_true", help="現在のバージョンを表示")
    group.add_argument("--patch", action="store_true", help="パッチバージョンをインクリメント")
    group.add_argument("--minor", action="store_true", help="マイナーバージョンをインクリメント")
    group.add_argument("--major", action="store_true", help="メジャーバージョンをインクリメント")
    group.add_argument("--set", metavar="VERSION", help="特定のバージョンに設定")
    
    args = parser.parse_args()
    
    # 現在のバージョンを取得
    current_version = get_current_version()
    
    if args.current:
        print(f"現在のバージョン: {current_version}")
        return
    
    if args.set:
        new_version = args.set
        if not validate_new_version(new_version):
            print(f"エラー: 無効なバージョン形式: {new_version}")
            print("バージョンは major.minor.patch 形式である必要があります (例: 1.2.3)")
            sys.exit(1)
    elif args.patch:
        new_version = increment_version(current_version, "patch")
    elif args.minor:
        new_version = increment_version(current_version, "minor")
    elif args.major:
        new_version = increment_version(current_version, "major")
    else:
        parser.print_help()
        return
    
    # バージョン更新の確認
    print(f"現在のバージョン: {current_version}")
    print(f"新しいバージョン: {new_version}")
    
    if args.set:
        confirm = input("バージョンを更新しますか？ (y/N): ")
    else:
        confirm = input(f"バージョンを {current_version} → {new_version} に更新しますか？ (y/N): ")
    
    if confirm.lower() in ["y", "yes"]:
        update_version(new_version)
        
        # 変更履歴の更新を促す
        changelog_path = Path("CHANGELOG.md")
        if not changelog_path.exists():
            print("\n注意: CHANGELOG.mdが見つかりません。変更履歴の作成を検討してください。")
        else:
            print("\nCHANGELOG.mdを更新して、このバージョンの変更内容を記載してください。")
    else:
        print("バージョン更新をキャンセルしました")


if __name__ == "__main__":
    main()
