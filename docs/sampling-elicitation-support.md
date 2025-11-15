# MCP Sampling and Elicitation Support

## 概要

PostgreSQL MCPサーバーは、MCPプロトコルの拡張機能である**Sampling**と**Elicitation**を完全にサポートしています。これにより、AIアシスタントがより高度なデータ分析と対話型のデータ探索を実行できるようになります。

## Samplingサポート

### 利用可能なSamplingツール

#### 1. 高度なデータ分析ツール
- `request_llm_analysis` - LLMによる包括的なデータ分析
- `generate_normalization_plan` - 正規化計画の生成
- `assess_data_quality` - データ品質評価
- `optimize_schema_with_llm` - スキーマ最適化

#### 2. スキーマ分析ツール
- `get_multiple_table_schemas` - 複数テーブルのスキーマ情報取得
- `analyze_table_relationships` - テーブル間の関係性分析
- `generate_schema_overview` - 包括的なスキーマ概要生成
- `analyze_normalization_state` - 正規化状態分析
- `suggest_normalization_improvements` - 正規化改善提案

### Sampling機能の特徴

- **LLM連携**: MCP Samplingを通じてLLMと連携した高度な分析
- **データ品質評価**: 完全性、正確性、一貫性などの品質次元の評価
- **正規化分析**: データベース正規化レベルの自動評価と改善計画
- **スキーマ最適化**: パフォーマンスと保守性のためのスキーマ改善提案

## Elicitationサポート

### 利用可能なElicitationツール

#### 1. 対話型データ探索
- `interactive_data_exploration` - ガイド付き対話によるデータ探索
- `guided_analysis_workflow` - 段階的な分析ワークフロー
- `clarify_analysis_requirements` - 分析要件の明確化

### Elicitation機能の特徴

- **対話型探索**: ユーザーとの対話を通じたデータ探索
- **ガイド付きワークフロー**: 段階的な分析プロセスの提供
- **要件明確化**: 分析要件の明確化と範囲定義
- **継続的対話**: 会話コンテキストの維持と継続的な分析

## プロトコルサポート

### 初期化レスポンス

サーバーはinitializeレスポンスで以下のcapabilitiesを宣言します：

```json
{
  "experimental": {
    "sampling": true,
    "elicitation": true
  },
  "roots": [],
  "tools": {
    "listChanged": false
  }
}
```

### サポートされる分析タイプ

1. **正規化分析** (`normalization_analysis`)
2. **データ品質評価** (`data_quality_assessment`)
3. **スキーマ最適化** (`schema_optimization`)
4. **関係性分析** (`relationship_analysis`)
5. **パフォーマンスレビュー** (`performance_review`)

## 使用例

### Samplingの使用例

```python
# データ品質評価の実行
result = await request_llm_analysis(
    analysis_type="data_quality_assessment",
    table_names=["users", "orders", "products"],
    quality_dimensions=["completeness", "accuracy", "consistency"]
)

# 正規化計画の生成
plan = await generate_normalization_plan(
    table_names=["customer_orders"],
    normalization_level="3nf",
    include_migration_sql=True
)
```

### Elicitationの使用例

```python
# 対話型データ探索
conversation = await interactive_data_exploration(
    table_names=["sales", "customers", "products"],
    exploration_focus="relationships",
    conversation_context="前回の分析結果"
)

# ガイド付き分析ワークフロー
workflow = await guided_analysis_workflow(
    analysis_type="normalization",
    table_names=["orders"],
    current_step=1,
    user_responses={}
)
```

## 設定

### 環境変数

以下の環境変数でSampling/Elicitation機能を制御できます：

- `MCP_SAMPLING_ENABLED=true` - Sampling機能の有効化
- `MCP_ELICITATION_ENABLED=true` - Elicitation機能の有効化
- `MCP_LLM_MODEL=gpt-4` - 使用するLLMモデルの指定

### ロギング

Sampling/Elicitation操作の詳細なログは以下のファイルに出力されます：

- `mcp_postgres.log` - 一般ログ
- `mcp_protocol.log` - プロトコルレベルの詳細ログ

## ベストプラクティス

1. **段階的な分析**: Elicitationツールを使用して分析要件を明確化
2. **データ品質優先**: 分析前にデータ品質評価を実施
3. **適切なサンプリング**: 大規模データセットでは適切なサンプルサイズを設定
4. **継続的な改善**: 分析結果に基づいて継続的にスキーマを改善

## 制限事項

- 現在の実装では、実際のMCP Sampling API呼び出しはシミュレーションされています
- 本番環境では適切なLLM APIキーの設定が必要です
- 大規模データセットではパフォーマンスに注意が必要です

## 今後の拡張

- 実際のMCP Sampling APIとの完全な統合
- 追加の分析タイプのサポート
- カスタム分析プロンプトのサポート
- リアルタイムデータ分析機能
