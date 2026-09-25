---
layout: page
title: 基本的な思想
permalink: /philosophy.html
---

# 基本的な思想

* TOC
{:toc}

## Packmol を「配置エンジン」として使う

このコードでは Packmol に材料科学上の意味まで持たせません。Packmol が担当するのは、与えられた XYZ テンプレートを、指定した個数だけ、指定したセル内へ重なりを避けながら配置することです。

一方、化学量論比、密度、総原子数、セルサイズ、分子ユニットの形状、VASP 形式への変換、FNC の生成は Python 側の責務です。

この分離により、Packmol の入力ファイルを直接編集するのではなく、「どの材料を、どの密度で、何原子程度のセルとして作るか」を Python の入力として扱えます。

## 外部入力の基準

`AmorphousBuilder` の高レベル API は、主として次の条件から構造生成を開始します。

1. 元素列 `symbols` と化学量論比 `ratios`
2. 希望する総原子数 `total_atom_count`
3. 質量密度 `mass_density` または数密度 `number_density`
4. Packmol の最小分離距離 `minimum_separation`

総原子数が化学量論比の合計で割り切れない場合、`AmorphousBuilder` は組成を維持できる最も近い整数倍へ総原子数を補正します。その倍率は `multiplier` として公開され、各テンプレートの複製数を決めるために利用できます。

## テンプレートと配置条件を分離する

`model.py` は Packmol に渡すテンプレート XYZ の形を作ります。単原子なら `write_single_atom_xyz()`、正四面体ユニットなら `write_tetrahedral_unit_xyz()` のような関数を使います。

重要なのは、分子ユニット内部の幾何と Packmol の packing 半径を別物として扱うことです。

- テンプレート内部の距離: P–O や O–O のような、ユニットそのものの形状。
- packing radius: 既に作られたテンプレート同士が配置時に近づきすぎないための排除条件。
- `minimum_separation`: Packmol 全体に与える `tolerance`。

この区別を維持することで、「ユニットの形を決めるパラメータ」と「ランダム配置を成立させるパラメータ」が混在しません。

## モジュールの責務

### `builder.py`

利用側から見た高レベル API です。密度からセル長を決め、テンプレート群を登録し、Packmol 入力生成・実行・POSCAR 変換・必要に応じた FNC 出力までを接続します。

### `model.py`

Packmol に渡す構造テンプレートと材料レシピの表現を担当します。物質固有の数値を共通モジュールへ埋め込まず、`make_*.py` 側から条件を与える設計です。

### `packmol_inp.py`

Python 側のテンプレート情報を Packmol の `.inp` 文法へ変換します。元素記号で指定された packing radius を、XYZ 内の 1 始まり atom index に変換する処理もここで行います。

### `packmol.py`

Packmol 実行、密度と数密度の換算、セル長計算、XYZ の読み取り、POSCAR 変換などを担当する低レベル処理です。

### `config.py` / `param.py`

`config.py` は設定値、`param.py` は Avogadro 定数、Å³–cm³ 換算係数、原子量表などの定数を保持します。

## 高レベル API と低レベル API

通常の材料生成では `AmorphousBuilder` を入口とします。`PackmolInp` や `Packmol` は、その内部処理を個別に使いたい場合の低レベル API です。

したがって、利用側の `make_*.py` は Packmol 入力ファイルの文法を知る必要をできるだけ減らし、材料固有条件の記述に集中する構成になっています。
