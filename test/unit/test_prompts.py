"""
Unit tests for prompt management system
"""

from src.mcp_postgres_duwenji.prompts import PromptManager, get_prompt_manager


class TestPromptManager:
    """Test cases for PromptManager class"""

    def test_prompt_manager_initialization(self):
        """Test that PromptManager initializes correctly"""
        manager = PromptManager()
        assert manager is not None
        assert len(manager.prompts) > 0

    def test_list_prompts(self):
        """Test listing all available prompts"""
        manager = PromptManager()
        prompts = manager.list_prompts()

        assert len(prompts) > 0
        assert all(prompt.name for prompt in prompts)
        assert all(prompt.description for prompt in prompts)

    def test_get_existing_prompt(self):
        """Test getting an existing prompt"""
        manager = PromptManager()
        prompt = manager.get_prompt("data_analysis_basic")

        assert prompt is not None
        assert prompt.name == "基本的なデータ分析"
        assert prompt.description == "テーブルデータの基本的な統計分析を実行"
        assert len(prompt.arguments) > 0

    def test_get_nonexistent_prompt(self):
        """Test getting a non-existent prompt"""
        manager = PromptManager()
        prompt = manager.get_prompt("nonexistent_prompt")

        assert prompt is None

    def test_get_prompt_with_arguments(self):
        """Test getting a prompt with argument substitution"""
        manager = PromptManager()
        arguments = {"table_name": "users"}
        prompt = manager.get_prompt("data_analysis_basic", arguments)

        assert prompt is not None
        # Check that prompt has arguments
        assert len(prompt.arguments) > 0
        assert prompt.arguments[0].name == "table_name"

    def test_prompt_categories(self):
        """Test that all prompt categories are available"""
        manager = PromptManager()
        prompts = manager.list_prompts()

        prompt_names = [prompt.name for prompt in prompts]

        # Check for expected prompt categories
        expected_categories = [
            "基本的なデータ分析",
            "高度なデータ分析",
            "クエリ最適化アドバイス",
            "スキーマ設計アドバイス",
            "データ品質評価",
            "テーブル関係性分析",
            "インデックス最適化",
            "データ移行計画",
            "パフォーマンストラブルシューティング",
            "バックアップと復旧計画",
        ]

        for category in expected_categories:
            assert category in prompt_names

    def test_global_prompt_manager(self):
        """Test the global prompt manager instance"""
        manager = get_prompt_manager()
        assert manager is not None

        # Verify it's the same instance
        manager2 = get_prompt_manager()
        assert manager is manager2


class TestPromptContent:
    """Test cases for prompt content validation"""

    def test_prompt_message_structure(self):
        """Test that prompt messages have correct structure"""
        manager = PromptManager()

        for prompt_id, prompt_config in manager.prompts.items():
            messages = prompt_config["messages"]
            assert len(messages) > 0, f"Prompt {prompt_id} has no messages"

            for message in messages:
                assert hasattr(message, "role"), f"Message in {prompt_id} missing role"
                assert hasattr(
                    message, "content"
                ), f"Message in {prompt_id} missing content"
                assert hasattr(
                    message.content, "text"
                ), f"Message content in {prompt_id} missing text"
                assert (
                    message.content.text.strip()
                ), f"Message text in {prompt_id} is empty"

    def test_prompt_argument_consistency(self):
        """Test that prompt arguments are consistent with message templates"""
        manager = PromptManager()

        for prompt_id, prompt_config in manager.prompts.items():
            arguments = prompt_config["arguments"]
            messages = prompt_config["messages"]

            # Check that all arguments are used in messages
            for arg in arguments:
                arg_used = False
                for message in messages:
                    if f"{{{arg}}}" in message.content.text:
                        arg_used = True
                        break

                assert (
                    arg_used
                ), f"Argument '{arg}' in prompt '{prompt_id}' is not used in any message"

    def test_prompt_descriptions(self):
        """Test that all prompts have meaningful descriptions"""
        manager = PromptManager()

        for prompt_id, prompt_config in manager.prompts.items():
            description = prompt_config["description"]
            assert description, f"Prompt {prompt_id} has empty description"
            assert len(description) > 10, f"Prompt {prompt_id} description is too short"


def test_prompt_manager_integration():
    """Integration test for prompt manager with actual MCP types"""
    manager = PromptManager()

    # Test that all prompts can be converted to MCP Prompt objects
    prompts = manager.list_prompts()

    for prompt in prompts:
        assert prompt.name
        assert prompt.description
        assert isinstance(prompt.arguments, list)
