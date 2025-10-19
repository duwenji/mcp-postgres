"""
pytestの実践的な使用例

このファイルはpytestの様々な機能を実践的に示す例です。
実際のプロジェクトで参考にしてください。
"""

import pytest
from unittest.mock import patch, MagicMock
import os


# ============================================================================
# 基本的なテスト関数の例
# ============================================================================


def test_basic_assertions():
    """基本的なアサーションの例"""
    # 等価性のテスト
    assert 1 + 1 == 2
    assert "hello" + " world" == "hello world"

    # 真偽値のテスト
    assert True is True
    assert False is False
    assert not False

    # 包含関係のテスト
    assert "hello" in "hello world"
    assert 1 in [1, 2, 3]
    assert "key" in {"key": "value"}


def test_exception_handling():
    """例外処理のテスト例"""
    # 例外が発生することをテスト
    with pytest.raises(ValueError):
        int("invalid")

    # 例外メッセージの検証
    with pytest.raises(ValueError) as exc_info:
        int("not_a_number")
    assert "invalid literal" in str(exc_info.value)


# ============================================================================
# テストクラスの例
# ============================================================================


class TestStringOperations:
    """文字列操作のテストクラス例"""

    def test_concatenation(self):
        """文字列連結のテスト"""
        result = "hello" + " " + "world"
        assert result == "hello world"

    def test_upper_case(self):
        """大文字変換のテスト"""
        result = "hello".upper()
        assert result == "HELLO"

    def test_string_length(self):
        """文字列長のテスト"""
        text = "hello world"
        assert len(text) == 11


class TestListOperations:
    """リスト操作のテストクラス例"""

    def test_list_append(self):
        """リストへの要素追加テスト"""
        my_list = [1, 2, 3]
        my_list.append(4)
        assert my_list == [1, 2, 3, 4]

    def test_list_slicing(self):
        """リストのスライス操作テスト"""
        my_list = [0, 1, 2, 3, 4, 5]
        assert my_list[1:4] == [1, 2, 3]
        assert my_list[:3] == [0, 1, 2]
        assert my_list[3:] == [3, 4, 5]


# ============================================================================
# Fixtureを使用したテストの例
# ============================================================================


@pytest.fixture
def sample_user_data():
    """サンプルユーザーデータを提供するfixture"""
    return {"id": 1, "name": "Test User", "email": "test@example.com", "age": 30}


@pytest.fixture
def empty_list():
    """空のリストを提供するfixture"""
    return []


@pytest.fixture(scope="function")
def setup_and_teardown():
    """セットアップとクリーンアップを行うfixture"""
    # セットアップ処理
    print("Setting up test environment...")
    test_data = {"status": "ready"}

    yield test_data  # テストで使用するデータを提供

    # クリーンアップ処理
    print("Cleaning up test environment...")


def test_with_user_data_fixture(sample_user_data):
    """fixtureを使用したテスト例"""
    assert sample_user_data["name"] == "Test User"
    assert sample_user_data["email"] == "test@example.com"
    assert isinstance(sample_user_data["age"], int)


def test_with_empty_list_fixture(empty_list):
    """空リストfixtureを使用したテスト例"""
    assert len(empty_list) == 0
    empty_list.append("item")
    assert len(empty_list) == 1
    assert empty_list[0] == "item"


def test_with_setup_teardown(setup_and_teardown):
    """セットアップ/クリーンアップfixtureを使用したテスト例"""
    # fixtureからデータを受け取る
    test_data = setup_and_teardown
    assert test_data["status"] == "ready"


# ============================================================================
# マーカーを使用したテストの例
# ============================================================================


@pytest.mark.slow
def test_slow_operation():
    """時間のかかる操作のテスト（slowマーカー付き）"""
    # 実際の遅い処理をシミュレート
    import time

    time.sleep(0.1)  # 実際のテストではもっと長い時間がかかる場合がある
    assert True


@pytest.mark.parametrize(
    "input_value,expected", [(1, 2), (2, 4), (5, 10), (0, 0), (-1, -2)]
)
def test_double_function(input_value, expected):
    """パラメータ化テストの例"""

    def double(x):
        return x * 2

    result = double(input_value)
    assert result == expected


# ============================================================================
# モックとパッチの使用例
# ============================================================================


def test_with_magic_mock():
    """MagicMockを使用したテスト例"""
    # モックオブジェクトの作成
    mock_service = MagicMock()
    mock_service.get_data.return_value = {"result": "mocked_data"}
    mock_service.process.return_value = "processed_result"

    # テスト対象の関数（実際には別のモジュールにあると想定）
    def business_logic(service):
        data = service.get_data()
        result = service.process(data)
        return result

    # テスト実行
    result = business_logic(mock_service)

    # 検証
    assert result == "processed_result"
    mock_service.get_data.assert_called_once()
    mock_service.process.assert_called_once_with({"result": "mocked_data"})


@patch("os.getenv")
def test_with_patch_decorator(mock_getenv):
    """@patchデコレータを使用したテスト例"""
    # モックの設定
    mock_getenv.return_value = "test_database"

    # テスト対象の関数
    def get_database_name():
        return os.getenv("DATABASE_NAME")

    # テスト実行と検証
    result = get_database_name()
    assert result == "test_database"
    mock_getenv.assert_called_once_with("DATABASE_NAME")


def test_with_patch_context_manager():
    """patchコンテキストマネージャを使用したテスト例"""
    # 元の関数を保存
    original_getenv = os.getenv

    with patch("os.getenv") as mock_getenv:
        # モックの設定
        mock_getenv.return_value = "mocked_value"

        # テスト実行
        result = os.getenv("TEST_VAR")

        # 検証
        assert result == "mocked_value"
        mock_getenv.assert_called_once_with("TEST_VAR")

    # コンテキストマネージャの外では元の関数が復元されている
    assert os.getenv is original_getenv


@patch.dict(os.environ, {"TEST_VAR": "test_value", "ANOTHER_VAR": "another_value"})
def test_with_patch_dict():
    """環境変数のモックテスト例"""
    assert os.environ["TEST_VAR"] == "test_value"
    assert os.environ["ANOTHER_VAR"] == "another_value"

    # 元の環境変数は変更されていないことを確認
    with pytest.raises(KeyError):
        _ = os.environ["NONEXISTENT_VAR"]


# ============================================================================
# 非同期テストの例（このプロジェクトで使用されているパターン）
# ============================================================================

# 非同期テストの例（このプロジェクトではpytest-asyncioが利用可能）
# 実際のプロジェクトでは以下のように記述します：

# import asyncio
#
# @pytest.mark.asyncio
# async def test_async_operation():
#     """非同期関数のテスト例"""
#     async def async_hello():
#         await asyncio.sleep(0.01)  # 非同期処理をシミュレート
#         return "hello async world"
#
#     result = await async_hello()
#     assert result == "hello async world"


def test_async_concept_example():
    """非同期テストの概念を示す例（実際の非同期テストではない）"""

    # 非同期テストの概念を説明するための例
    # 実際のプロジェクトでは@pytest.mark.asyncioを使用
    def simulate_async_operation():
        return "hello async world"

    result = simulate_async_operation()
    assert result == "hello async world"


# ============================================================================
# データベース関連のテスト例（このプロジェクトのパターンに基づく）
# ============================================================================


class TestDatabasePatterns:
    """データベーステストのパターン例"""

    def test_database_connection_success(self, test_database_config):
        """データベース接続成功のテスト（実際のプロジェクトのパターン）"""
        # このプロジェクトでは実際のデータベース設定を使用
        config = test_database_config
        assert "host" in config
        assert "port" in config
        assert "database" in config
        assert isinstance(config["port"], int)

    def test_database_connection_failure(self):
        """データベース接続失敗のテスト"""
        # 無効な設定で接続が失敗することをテスト
        invalid_config = {
            "host": "invalid-host",
            "port": 9999,
            "database": "invalid-db",
            "username": "invalid-user",
            "password": "invalid-pass",
        }

        # 実際のプロジェクトではDatabaseConnectionクラスを使用
        # ここでは概念的なテストを示す
        def test_connection(config):
            # 実際の実装ではデータベース接続を試みる
            return False  # 接続失敗をシミュレート

        result = test_connection(invalid_config)
        assert result is False


# ============================================================================
# 統合テストの例（このプロジェクトのマーカーを使用）
# ============================================================================


@pytest.mark.integration
class TestIntegrationPatterns:
    """統合テストのパターン例"""

    def test_integration_operation(self):
        """統合テストの例"""
        # 実際の統合テストでは外部サービスやデータベースと連携
        # ここでは概念的なテストを示す
        assert True  # 統合テストが成功したことを示す

    @pytest.fixture
    def integration_setup(self):
        """統合テスト用のセットアップ"""
        # 実際の統合テストではデータベース接続などをセットアップ
        setup_data = {"connected": True}
        yield setup_data
        # クリーンアップ処理

    def test_with_integration_setup(self, integration_setup):
        """統合テストセットアップを使用したテスト"""
        assert integration_setup["connected"] is True


# ============================================================================
# エラーハンドリングの高度な例
# ============================================================================


def test_multiple_exception_types():
    """複数の例外タイプのテスト"""
    # いずれかの例外が発生することをテスト
    with pytest.raises((ValueError, TypeError)):
        # 状況に応じて異なる例外が発生する関数を想定
        def risky_operation(x):
            if x < 0:
                raise ValueError("Negative value")
            elif x > 100:
                raise TypeError("Too large")
            return x * 2

        risky_operation(-1)  # ValueErrorが発生


def test_exception_with_message():
    """特定のメッセージを含む例外のテスト"""
    with pytest.raises(ValueError, match=".*required.*"):
        # "required"という文字列を含むメッセージの例外を期待
        def validate_input(data):
            if not data:
                raise ValueError("Input data is required")
            return data

        validate_input(None)


# ============================================================================
# カスタムアサーションの例
# ============================================================================


def assert_user_data(user_data):
    """ユーザーデータのカスタムアサーション"""
    required_fields = ["id", "name", "email"]
    for field in required_fields:
        assert field in user_data, f"Missing required field: {field}"

    assert isinstance(user_data["id"], int), "ID must be integer"
    assert "@" in user_data["email"], "Email must contain @"


def test_with_custom_assertion(sample_user_data):
    """カスタムアサーションを使用したテスト"""
    assert_user_data(sample_user_data)
    # 追加の検証
    assert sample_user_data["name"] == "Test User"


if __name__ == "__main__":
    # このファイルを直接実行してテストを実行
    pytest.main([__file__, "-v"])
