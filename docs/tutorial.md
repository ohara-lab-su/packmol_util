---
layout: page
title: チュートリアル
permalink: /tutorial.html
---

# チュートリアル

* TOC
{:toc}

## 1. 最小構成: 多元素を完全ランダムに配置する

ここでは Li–S–P–C 系を例に、各元素を独立した単原子テンプレートとして配置します。分子ユニットや FNC は使用しません。

```python
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz

symbols = ["Li", "S", "P", "C"]
ratios = [43, 39, 5, 13]
total_atom_count = 100
number_density_A3 = 0.0453277972
minimum_separation_distance = 1.8
```

`ratios` の合計は 100 なので、この例では `total_atom_count=100` に対して倍率 `multiplier` は 1 です。

## 2. 単原子 XYZ テンプレートを作る

Packmol は配置対象となる座標テンプレートを必要とします。完全ランダム系では、元素ごとに原点上の 1 原子だけを持つ XYZ を作ります。

```python
for symbol in symbols:
    write_single_atom_xyz(
        filename=f"{symbol}.xyz",
        element=symbol,
    )
```

生成される `Li.xyz` などは、「Li 原子を一個配置するためのテンプレート」です。実際のセル内原子数は Packmol の `number` によって決まります。

## 3. `AmorphousBuilder` を作る

```python
builder = AmorphousBuilder(
    symbols=symbols,
    ratios=ratios,
    total_atom_count=total_atom_count,
    number_density=number_density_A3,
    minimum_separation=minimum_separation_distance,
)
```

数密度を指定した場合、セル一辺 `L` は総原子数 `N` と数密度 `ρ_N` から

```text
L = (N / ρ_N)^(1/3)
```

として決まります。

質量密度を使う場合は `number_density` の代わりに `mass_density` を指定します。原子量と組成比から内部で数密度へ換算されます。

## 4. テンプレートを登録する

```python
for symbol, ratio in zip(symbols, ratios):
    builder.add_template(
        xyz_file=f"{symbol}.xyz",
        number=ratio * builder.multiplier,
        packing_radii=None,
        fnc_pairs_in_template=None,
        fnc_distance_ranges=None,
        fnc_output_constraint_types=None,
    )
```

`builder.multiplier` は、化学量論比全体を何倍すれば実際のセル原子数になるかを表します。したがって各元素の実原子数は `ratio * builder.multiplier` です。

## 5. Packmol を実行して出力を作る

```python
builder.build(output_prefix="LiSPC_random")
```

`build()` は、内部で `PackmolInp` を使って入力を生成し、Packmol を実行し、その XYZ を POSCAR へ変換します。

代表的な生成物は次の通りです。

```text
LiSPC_random_packmol.inp
LiSPC_random_packmol.xyz
LiSPC_random_packmol.log
POSCAR
POSCAR.vasp
```

FNC の定義をテンプレートへ与えた場合は、対応する `.fnc` も生成されます。

## 6. 総原子数の自動補正

例えば `ratios=[3, 1, 4]` の Li3PO4 は、一組あたり 8 原子です。希望する `total_atom_count` が 8 の整数倍でなければ、組成比を厳密に維持できません。

`AmorphousBuilder` はこの場合、希望値に近い整数倍率を選び、実際の `total_atom_count` を補正します。

```python
builder.multiplier
builder.total_atom_count
```

を参照すれば、補正後の倍率と原子数を取得できます。

## 7. 分子ユニットを配置する

PO4 のような局所構造を最初から保持したい場合、P と O を別々の単原子として置くのではなく、一個の PO4 XYZ をテンプレートとして登録します。

```python
from packmol_util.model import write_tetrahedral_unit_xyz

write_tetrahedral_unit_xyz(
    filename="PO4.xyz",
    center_element="P",
    vertex_element="O",
    center_vertex_distance=1.52,
    vertex_vertex_distance=2.48,
)
```

Packmol はこの XYZ 全体を一つの structure として複製するため、テンプレート内部の PO4 形状を保持した状態でランダム配置できます。

packing radius を使う場合は `add_template()` の `packing_radii` に元素記号をキーとする辞書を渡します。

```python
builder.add_template(
    xyz_file="PO4.xyz",
    number=builder.multiplier,
    packing_radii={"P": 1.2, "O": 1.0},
)
```

この半径は P–O 結合長を決めるものではありません。テンプレート間の配置時に使う排除半径です。

## 8. 密度だけを相互変換する

`Packmol` クラスは質量密度と数密度の換算にも使えます。

```python
from packmol_util.packmol import Packmol

packmol = Packmol()

number_density = packmol.number_density_from_mass_density(
    symbols=["Si", "O"],
    ratios=[1, 2],
    mass_density_g_cm3=2.214,
)
```

逆変換には `mass_density_from_number_density()` を使用します。

## 9. どの層を使うか

通常の構造生成では `AmorphousBuilder` を使います。Packmol の `.inp` 自体を細かく制御したい場合は `PackmolInp`、密度計算・Packmol 実行・XYZ/POSCAR 変換を個別に使いたい場合は `Packmol` を直接利用します。
