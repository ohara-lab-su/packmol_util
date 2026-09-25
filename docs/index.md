---
layout: page
title: packmol_util
permalink: /
---

# packmol_util

`packmol_util` は、Packmol を材料系のアモルファス初期構造生成に使うための Python ユーティリティです。
Packmol 自体にはない「化学量論比」「質量密度・数密度」「VASP POSCAR への変換」「分子ユニット」「FNC 出力」を Python 側で扱い、入力生成から Packmol 実行、後処理までを一つの流れとして構成します。

このドキュメントは次の 3 ページに分けています。

- [基本的な思想](philosophy.html) — 何を Packmol に任せ、何を Python 側で扱うか、各モジュールの責務。
- [チュートリアル](tutorial.html) — 単原子の完全ランダム系から `AmorphousBuilder` を使う基本手順。
- [API リファレンス](api.html) — Python ソースの docstring とシグネチャから自動生成される API 一覧。

## 全体の処理

```text
材料条件
  │
  ├─ symbols / ratios
  ├─ total_atom_count
  ├─ mass_density または number_density
  └─ minimum_separation
  │
  ▼
AmorphousBuilder
  │
  ├─ セル長の決定
  ├─ テンプレート登録
  ▼
PackmolInp ──→ *_packmol.inp
  │
  ▼
Packmol ─────→ *_packmol.xyz / *_packmol.log
  │
  ├─→ POSCAR
  ├─→ POSCAR.vasp
  └─→ 必要な場合 *.fnc
```

Packmol の入力文法を直接組み立てることよりも、材料側の条件を Python 上で明示し、それを Packmol の入力へ変換することを中心にしています。
