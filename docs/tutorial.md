---
layout: default
title: チュートリアル
---

# チュートリアル

* TOC
{:toc}

## 1. 基本形

高レベル API では `AmorphousBuilder` を使います。

```python
from packmol_util.builder import AmorphousBuilder

builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[82, 4, 14],
    total_atom_count=2000,
    mass_density_g_cm3=7.3336,
)
```

`symbols` と `ratios` が組成を、`total_atom_count` が希望総原子数を表します。密度は質量密度または数密度を与えます。

## 2. 実際に採用された倍率を確認する

```python
print(builder.multiplier)
```

希望総原子数が組成比と整合しない場合でも、組成比を維持するよう内部で原子数が調整されます。

## 3. テンプレートを登録する

単原子だけでなく、あらかじめ作った分子・構造ユニットの XYZ を Packmol の structure として登録できます。

```python
builder.add_template(
    xyz_file="PO4.xyz",
    number=builder.multiplier,
)
```


実際に指定可能な引数はバージョンにより変化し得るため、最新の定義は [API Reference](api/) を参照してください。

## 4. 構造を生成する

```python
builder.build(output_prefix="amorphous")
```

`build()` が Packmol 入力生成から後続処理までを統合します。FNC を出力する場合は `fnc_file` を指定できます。

## 5. 低レベル API

計算やファイル生成を個別に制御する場合は次の層を直接使用します。

- `packmol_util.packmol.Packmol`: 密度変換、セルサイズ、Packmol 実行、XYZ→POSCAR など
- `packmol_util.packmol_inp.PackmolInp`: Packmol `.inp` の構築
- `packmol_util.model`: XYZ テンプレート、structure レシピ、packing 半径等

詳細なシグネチャと docstring は [自動生成 API Reference](api/) に集約しています。
