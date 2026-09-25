# リファレンス

このページは主要コンポーネントの役割を人間向けに整理したものです。

クラス、メソッド、引数、型注釈、docstring の完全な一覧は {doc}`api/modules` に自動生成されます。

## `AmorphousBuilder`

構造生成全体をまとめる高レベル I/F です。

主な役割:

- 元素と組成比の保持
- 総原子数と組成比の整合
- 組成単位倍率の決定
- 質量密度または数密度からセルサイズを決定
- Packmol template の登録
- Packmol 入力生成
- Packmol 実行
- POSCAR 変換

通常の利用ではこのクラスを入口にします。

## `Packmol`

Packmol の実行と、その周辺の数値処理を担当します。

主な役割:

- 原子量・平均原子量
- 質量密度と数密度の変換
- 原子数と数密度からセルサイズを計算
- Packmol 実行
- XYZ から POSCAR への変換

## `PackmolInp`

Packmol 入力ファイルの構築を担当します。

構造 template、配置数、配置領域、packing radius などを Packmol の入力文法へ変換します。

## `model`

Packmol に渡す構造 template と recipe を扱います。

単原子 template のほか、複数原子からなる構造ユニットの XYZ template を生成できます。

## `Config`

設定ファイルから `packmol_util` の設定値を読み込むためのクラスです。

## `param`

原子量など、密度・セルサイズ計算に利用する定数を保持します。

## API Reference

```{toctree}
:maxdepth: 2

api/modules
```

この部分は手書きではありません。`docs/build.sh` が `src/packmol_util` を走査してビルド時に生成します。
