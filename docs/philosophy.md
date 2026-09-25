---
layout: default
title: 基本的な思想
---

# 基本的な思想

* TOC
{:toc}

## Packmol が扱わない情報を Python 側で扱う

Packmol 自体は、化学量論比、質量密度、数密度、原子量からセルサイズを決める仕組みを持ちません。`packmol_util` はこれらを Python 側で計算し、最終的に Packmol が理解する `structure` と `inside box` に落とします。

## 高レベル API と低レベル API を分離する

通常の構造生成では `AmorphousBuilder` を入口にします。これは原子数の調整、セルサイズ計算、テンプレート登録、Packmol 入力生成、Packmol 実行などのファイルの受け渡しを隠蔽するための層です。

一方、個別処理を制御したい場合には `Packmol`、`PackmolInp`、`model` の関数を直接使用できます。

## 物質固有情報を共通モジュールに埋め込まない

`model` は単原子テンプレート、四面体ユニット、structure レシピなどの共通表現を提供します。Li3PO4 や FeSiB のような物質固有の組成、距離、packing 半径は利用側から与える設計です。

## 組成比を壊さない

`AmorphousBuilder` は希望総原子数が組成比の合計で割り切れない場合、そのまま不整合な原子数を使用せず、組成比を維持できる近傍の総原子数へ補正します。補正後の倍率は `multiplier` として参照できます。

## API 文書を二重管理しない

クラス、関数、引数、型、docstring の一次情報は `src/packmol_util` に置きます。API Reference は GitHub Pages のビルド時に pdoc がソースから生成します。したがって API の変更時に `docs/api` を人間が書き換える必要はありません。
