---
layout: default
title: 手書きリファレンス
---

# 手書きリファレンス

* TOC
{:toc}

このページは API 自動生成ページとは別の、人間向けの入口です。厳密なシグネチャ、型注釈、docstring は [API Reference](api/) を参照してください。

## `builder`

`AmorphousBuilder` は通常利用する高レベル API です。組成比、希望原子数、密度から構造生成までの一連の処理をまとめます。

## `packmol`

`Packmol` は密度と数密度の変換、原子数、セルサイズ、Packmol 実行、XYZ/POSCAR 変換などの低レベル処理を担当します。

## `packmol_inp`

`PackmolInp` は Packmol の入力ファイルを組み立てます。structure ブロックや packing radius の指定を扱います。

## `model`

物質に依存しない構造テンプレートとレシピを扱います。単原子 XYZ、四面体ユニット、packing 半径、FNC 用情報などを共通化します。

## `config` / `param`

設定値と物理定数・原子量を保持します。
