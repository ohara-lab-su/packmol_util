# CHANGELOG

## 2026.06.29, v0.2.2

- FNC 出力機能を拡張
  - `builder.py` の `add_template()` に `fnc_output_constraint_types` オプションを追加
  - Packmol 用テンプレート形状は変更せず、RMC 用 `.fnc` に出力する constraint type のみ選択できるように改修
  - 従来は定義した全 FNC が出力されていたが、必要な constraint type のみ出力可能となった
  - デフォルト (`None`) は従来と同じ動作とし、既存コードとの互換性を維持

- Li3PO4 サンプルを更新
  - `make_Li3PO4.py` に `fnc_output_constraint_types` の利用例を追加
  - P–O のみを FNC とし、O–O を FNC から除外する設定例を追加
  - Packmol 初期構造はそのまま利用し、RMC 側のみ拘束条件を切り替える使用方法をコメントで説明

## 2026.06.07, v0.2.1

コメント・マニュアル調整

## 2026.06.07, v0.2.0

- builder 改修 / make 系をあわせて改修
  - `builder.py` 内の `add_template` メソッドの引数を `number` に再統一し、汎用的な複製個数指定のインターフェースとして固定
  - `make_FeSiB.py` および `make_Li3PO4.py` を改修し、利用側のデータ構造として単原子系・分子ユニット混在系を明確に峻別・整理
  - `builder.multiplier`（全体のスケール倍率）のプロパティを外部公開し、構成単位（ユニット）ごとの配置個数の自動計算・一元管理に対応
- README整備

## 2026.06.07, v0.1.0

- スクリプト側の複雑さの緩和のための Builder クラス作成

## 2026-06.07, v0.0.1

- 実用フェーズ
  - 主に PO4 ユニットの距離などの指定方法の改善

## 2026-06.06, v0.0.0

- テストフェーズ