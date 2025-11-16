#!/usr/bin/env python3
"""
Dockerコンテナとボリュームのクリーンアップスクリプト
修正後のDockerマネージャーをテストする前に実行してください
"""

import subprocess


def run_command(cmd, description):
    """コマンドを実行して結果を表示"""
    print(f"実行中: {description}")
    print(f"コマンド: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ 成功: {description}")
            if result.stdout:
                print(f"出力: {result.stdout}")
        else:
            print(f"✗ 失敗: {description}")
            if result.stderr:
                print(f"エラー: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"✗ 例外: {description} - {e}")
        return False


def main():
    print("Dockerコンテナとボリュームのクリーンアップを開始します...")

    # コンテナ名とボリューム名
    container_name = "mcp-postgres-auto"
    volume_name = "mcp_postgres_data"

    # コンテナの停止と削除
    commands = [
        (f"docker stop {container_name}", f"コンテナ {container_name} の停止"),
        (f"docker rm {container_name}", f"コンテナ {container_name} の削除"),
        (f"docker volume rm {volume_name}", f"ボリューム {volume_name} の削除"),
    ]

    all_success = True
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            all_success = False
            # 一部のコマンドは存在しない場合もあるので、続行
            print(f"警告: {desc} に失敗しましたが、続行します")

    # 確認: コンテナとボリュームが存在しないことを確認
    print("\nクリーンアップ後の状態確認:")
    run_command(
        f"docker ps -a --filter name={container_name}",
        f"コンテナ {container_name} の存在確認",
    )
    run_command(
        f"docker volume ls --filter name={volume_name}",
        f"ボリューム {volume_name} の存在確認",
    )

    if all_success:
        print("\n✓ クリーンアップ完了！")
        print("新しいDockerコンテナを起動する準備ができました。")
        print("MCPサーバーを再起動するか、以下のコマンドでテストしてください:")
        print("python -m src.mcp_postgres_duwenji.main")
    else:
        print("\n⚠ 一部のクリーンアップに失敗しました。")
        print("手動で確認してください:")
        print("docker ps -a")
        print("docker volume ls")


if __name__ == "__main__":
    main()
