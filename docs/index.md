# packmol_util

`packmol_util` は、Packmol を利用したアモルファス初期構造作成を Python から扱うためのライブラリです。

組成、総原子数、密度、最小分離距離などの条件から、Packmol 入力の生成、Packmol の実行、生成構造の POSCAR 変換までを扱います。

```{toctree}
:maxdepth: 2
:caption: Contents:

philosophy
tutorial
reference
api/modules
```

## ドキュメント

- {doc}`philosophy` — ライブラリの基本思想と責務分離
- {doc}`tutorial` — 基本的な使用方法
- {doc}`reference` — 人間向けに整理した主要コンポーネントの説明
- {doc}`api/modules` — Python ソースと docstring から自動生成される API Reference

## API Reference

API Reference は手書きではありません。

ビルド時に `sphinx-apidoc` が `src/packmol_util` を走査して `docs/api/` を生成し、その内容を Sphinx が HTML 化します。

したがって `src/packmol_util` の API を変更して `main` に push すると、GitHub Actions の Pages ビルド時に API Reference も再生成されます。
