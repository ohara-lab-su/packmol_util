# CHANGELOG

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/CHANGELOG.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/CHANGELOG.ja.md)

## 2026.10.08, v0.2.5

- LICENSE 追加
 
## 2026.10.07, v0.2.4

- public 用に微調整

## 2026.07.06, v0.2.3

- Config 機能を追加
  - `config.py` を導入し、ライブラリ全体で設定情報を一元管理できるようにした
  - サンプルスクリプトから `config.yml` を利用できるようにした
  - `config.yml` を利用しない場合は、スクリプト内で設定値を直接指定できる構成とした

- 密度変換サンプルを追加
  - `make_number_density.py` を追加
    - 質量密度から数密度を計算するサンプル
    - `Packmol.number_density_from_mass_density()` を利用
  - `make_mass_density.py` を追加
    - 数密度から質量密度を計算するサンプル
    - `Packmol.mass_density_from_number_density()` を利用

- サンプルコード整理
  - 密度変換処理を既存ライブラリのメソッドを利用する構成へ変更
  - 密度変換式の重複実装を廃止
  - サンプルコードを簡潔化し、`config.yml` と直接指定の切り替えをコメントアウトのみで行えるよう整理

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