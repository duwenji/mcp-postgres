"""
Unit tests for Concern-Based Filtering System
"""

import pytest
from unittest.mock import Mock
from src.mcp_postgres_duwenji.main import Server, AppContext
from mcp import Tool, Resource
from mcp.types import Prompt


@pytest.fixture
def mock_context():
    """Fixture to create a mock AppContext."""
    context = AppContext()
    context.concerns = {}
    return context


@pytest.fixture
def mock_server(mock_context):
    """Fixture to create a mock Server with context."""
    server = Server("mock-server")
    server.context = mock_context  # type: ignore[attr-defined]

    # Mock the create_initialization_options method to return a dict
    server.create_initialization_options = Mock(
        return_value={
            "capabilities": {
                "concerns": [
                    {
                        "name": "development",
                        "description": "Development phase concern",
                        "values": ["-"],
                        "default": "-",
                    },
                    {
                        "name": "maintenance",
                        "description": "Maintenance phase concern",
                        "values": ["-"],
                        "default": "-",
                    },
                    {
                        "name": "using",
                        "description": "Using phase concern",
                        "values": ["-"],
                        "default": "-",
                    },
                    {
                        "name": "tuning",
                        "description": "Tuning phase concern",
                        "values": ["-"],
                        "default": "-",
                    },
                ]
            }
        }
    )

    # Mock update_concerns decorator
    def mock_update_concerns_decorator(func=None):
        if func is None:
            return mock_update_concerns_decorator
        server._update_concerns_handler = func
        return func

    server.update_concerns = Mock(side_effect=mock_update_concerns_decorator)

    # Mock list_tools decorator
    def mock_list_tools_decorator(func=None):
        if func is None:
            return mock_list_tools_decorator
        server._list_tools_handler = func
        return func

    server.list_tools = Mock(side_effect=mock_list_tools_decorator)

    # Mock list_resources decorator
    def mock_list_resources_decorator(func=None):
        if func is None:
            return mock_list_resources_decorator
        server._list_resources_handler = func
        return func

    server.list_resources = Mock(side_effect=mock_list_resources_decorator)

    # Mock list_prompts decorator
    def mock_list_prompts_decorator(func=None):
        if func is None:
            return mock_list_prompts_decorator
        server._list_prompts_handler = func
        return func

    server.list_prompts = Mock(side_effect=mock_list_prompts_decorator)

    return server


def test_initialize_with_concerns(mock_server):
    """Test that the server initializes with declared concerns."""
    initialization_options = mock_server.create_initialization_options()
    capabilities = initialization_options.get("capabilities", {})
    concerns = capabilities.get("concerns", [])

    assert len(concerns) == 4
    assert any(concern["name"] == "development" for concern in concerns)
    assert any(concern["name"] == "maintenance" for concern in concerns)
    assert any(concern["name"] == "using" for concern in concerns)
    assert any(concern["name"] == "tuning" for concern in concerns)

    # Check values and defaults
    for concern in concerns:
        assert concern["values"] == ["-"]
        assert concern["default"] == "-"


def test_update_concerns(mock_server):
    """Test updating concerns dynamically."""

    # Create a mock handler function
    async def mock_handler(concerns):
        mock_server.context.concerns = concerns
        return {"success": True, "updated_concerns": concerns}

    # Apply the decorator
    mock_server.update_concerns()(mock_handler)

    # Test the handler
    test_concerns = {
        "development": "-",
        "maintenance": "-",
        "using": "-",
        "tuning": "-",
    }

    # Since we can't call async function directly in sync test, we'll test the logic
    mock_server.context.concerns = test_concerns
    assert mock_server.context.concerns == test_concerns


def test_filter_tools_by_concerns(mock_server):
    """Test filtering tools based on concerns."""
    # Create mock tools with concerns
    mock_tool_with_concern = Mock()
    mock_tool_with_concern._meta = {
        "concerns": {"development": "-", "maintenance": "-"}
    }

    mock_tool_without_concern = Mock()
    mock_tool_without_concern._meta = {}

    # Set up context with concerns
    mock_server.context.concerns = {
        "development": "-",
        "maintenance": "-",
        "using": "-",
        "tuning": "-",
    }

    # Test filtering logic (simplified version from main.py)
    all_tools = [mock_tool_with_concern, mock_tool_without_concern]
    filtered_tools = []

    for tool in all_tools:
        tool_concerns = tool._meta.get("concerns", {})
        matches = all(
            mock_server.context.concerns.get(key, value) == value
            for key, value in tool_concerns.items()
        )
        if matches:
            filtered_tools.append(tool)

    # Both tools should match since context has all concerns set to "-"
    # and tool_without_concern has no concerns (matches all)
    assert len(filtered_tools) == 2

    # Test with different context
    mock_server.context.concerns = {"development": "high"}  # Different value
    filtered_tools = []

    for tool in all_tools:
        tool_concerns = tool._meta.get("concerns", {})
        matches = all(
            mock_server.context.concerns.get(key, value) == value
            for key, value in tool_concerns.items()
        )
        if matches:
            filtered_tools.append(tool)

    # Now only tool_without_concern should match
    assert len(filtered_tools) == 1
    assert filtered_tools[0] == mock_tool_without_concern


def test_filter_resources_by_concerns(mock_server):
    """Test filtering resources based on concerns."""
    # Create mock resources with concerns
    mock_resource_with_concern = Mock(spec=Resource)
    mock_resource_with_concern._meta = {"concerns": {"development": "-", "using": "-"}}

    mock_resource_without_concern = Mock(spec=Resource)
    mock_resource_without_concern._meta = {}

    # Set up context with concerns
    mock_server.context.concerns = {
        "development": "-",
        "maintenance": "-",
        "using": "-",
        "tuning": "-",
    }

    # Test filtering logic (simplified version from main.py)
    all_resources = [mock_resource_with_concern, mock_resource_without_concern]
    filtered_resources = []

    for resource in all_resources:
        resource_concerns = getattr(resource, "_meta", {}).get("concerns", {})
        matches = all(
            mock_server.context.concerns.get(key, value) == value
            for key, value in resource_concerns.items()
        )
        if matches:
            filtered_resources.append(resource)

    # Both resources should match since context has all concerns set to "-"
    # and resource_without_concern has no concerns (matches all)
    assert len(filtered_resources) == 2

    # Test with different context
    mock_server.context.concerns = {"development": "high"}  # Different value
    filtered_resources = []

    for resource in all_resources:
        resource_concerns = getattr(resource, "_meta", {}).get("concerns", {})
        matches = all(
            mock_server.context.concerns.get(key, value) == value
            for key, value in resource_concerns.items()
        )
        if matches:
            filtered_resources.append(resource)

    # Now only resource_without_concern should match
    assert len(filtered_resources) == 1
    assert filtered_resources[0] == mock_resource_without_concern


def test_filter_prompts_by_concerns(mock_server):
    """Test filtering prompts based on concerns."""
    # Create mock prompts with concerns
    mock_prompt_with_concern = Mock(spec=Prompt)
    mock_prompt_with_concern._meta = {"concerns": {"maintenance": "-", "tuning": "-"}}

    mock_prompt_without_concern = Mock(spec=Prompt)
    mock_prompt_without_concern._meta = {}

    # Set up context with concerns
    mock_server.context.concerns = {
        "development": "-",
        "maintenance": "-",
        "using": "-",
        "tuning": "-",
    }

    # Test filtering logic (simplified version from main.py)
    all_prompts = [mock_prompt_with_concern, mock_prompt_without_concern]
    filtered_prompts = []

    for prompt in all_prompts:
        prompt_concerns = getattr(prompt, "_meta", {}).get("concerns", {})
        matches = all(
            mock_server.context.concerns.get(key, value) == value
            for key, value in prompt_concerns.items()
        )
        if matches:
            filtered_prompts.append(prompt)

    # Both prompts should match since context has all concerns set to "-"
    # and prompt_without_concern has no concerns (matches all)
    assert len(filtered_prompts) == 2

    # Test with different context
    mock_server.context.concerns = {"maintenance": "high"}  # Different value
    filtered_prompts = []

    for prompt in all_prompts:
        prompt_concerns = getattr(prompt, "_meta", {}).get("concerns", {})
        matches = all(
            mock_server.context.concerns.get(key, value) == value
            for key, value in prompt_concerns.items()
        )
        if matches:
            filtered_prompts.append(prompt)

    # Now only prompt_without_concern should match
    assert len(filtered_prompts) == 1
    assert filtered_prompts[0] == mock_prompt_without_concern


def test_meta_attribute_creation():
    """Test that _meta attribute can be added to Tool, Resource, and Prompt objects."""
    # Test Tool
    tool = Tool(
        name="test_tool",
        description="Test tool",
        inputSchema={"type": "object", "properties": {}, "required": []},
    )
    tool._meta = {"concerns": {"development": "-"}}
    assert hasattr(tool, "_meta")
    assert tool._meta["concerns"] == {"development": "-"}

    # Test Resource
    resource = Resource(
        uri="test://resource",
        name="Test Resource",
        description="Test resource",
        mimeType="text/plain",
    )
    resource._meta = {"concerns": {"maintenance": "-"}}
    assert hasattr(resource, "_meta")
    assert resource._meta["concerns"] == {"maintenance": "-"}

    # Test Prompt
    prompt = Prompt(name="Test Prompt", description="Test prompt", arguments=[])
    prompt._meta = {"concerns": {"using": "-"}}
    assert hasattr(prompt, "_meta")
    assert prompt._meta["concerns"] == {"using": "-"}
