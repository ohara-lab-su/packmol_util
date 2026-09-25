# チュートリアル

## 単原子 template から構造を作る

Fe–Si–B のように、各元素を独立した単原子 template として配置する例です。

### template を作る

```python
from packmol_util.model import write_single_atom_xyz

write_single_atom_xyz("Fe.xyz", "Fe")
write_single_atom_xyz("Si.xyz", "Si")
write_single_atom_xyz("B.xyz", "B")
```

それぞれ 1 原子だけを含む XYZ template が生成されます。

### Builder を作る

```python
from packmol_util.builder import AmorphousBuilder

builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    mass_density=7.0,
)
```

組成比の和は 100 なので、この場合の組成単位の倍率は、

```python
builder.multiplier
```

から取得できます。

### template を登録する

```python
builder.add_template(
    "Fe.xyz",
    80 * builder.multiplier,
)

builder.add_template(
    "Si.xyz",
    9 * builder.multiplier,
)

builder.add_template(
    "B.xyz",
    11 * builder.multiplier,
)
```

### 構造を生成する

```python
builder.build("FeSiB")
```

`build()` により Packmol 入力生成、Packmol 実行、出力構造の変換が行われます。

## 数密度を指定する

質量密度の代わりに数密度を指定できます。

```python
builder = AmorphousBuilder(
    symbols=["Fe", "Si", "B"],
    ratios=[80, 9, 11],
    total_atom_count=1000,
    minimum_separation=2.0,
    number_density=0.08,
)
```

計算されたセル一辺長は、

```python
print(builder.box_length)
```

で確認できます。

## 分子ユニットを配置する

Li3PO4 のように PO4 を 1 個の構造ユニットとして配置する場合は、PO4 の XYZ template を作ります。

### Li template

```python
from packmol_util.model import write_single_atom_xyz

write_single_atom_xyz("Li.xyz", "Li")
```

### PO4 template

```python
from packmol_util.model import write_tetrahedral_unit_xyz

write_tetrahedral_unit_xyz(
    filename="PO4.xyz",
    center_element="P",
    vertex_element="O",
    center_vertex_distance=1.54,
    vertex_vertex_distance=2.51,
)
```

ここで指定している距離は PO4 内部の幾何です。

### Builder

```python
from packmol_util.builder import AmorphousBuilder

builder = AmorphousBuilder(
    symbols=["Li", "P", "O"],
    ratios=[3, 1, 4],
    total_atom_count=512,
    minimum_separation=1.5,
    number_density=0.09119,
)
```

Li3PO4 は 1 組成単位あたり 8 原子なので、512 原子では 64 組成単位です。

### template を登録する

```python
builder.add_template(
    xyz_file="Li.xyz",
    number=3 * builder.multiplier,
)

builder.add_template(
    xyz_file="PO4.xyz",
    number=builder.multiplier,
    packing_radii={
        "P": 0.25,
        "O": 1.05,
    },
)
```

`packing_radii` は PO4 内部の結合距離ではなく、Packmol が template を配置するときの排除距離に使われます。

### 構造を生成する

```python
builder.build("Li3PO4")
```

## 低レベル API

高レベルの `AmorphousBuilder` を使わず、下位 API を個別に利用することもできます。

たとえば Packmol 入力だけを組み立てたい場合は `PackmolInp`、密度やセルサイズの計算、Packmol 実行、XYZ → POSCAR 変換などを個別に扱いたい場合は `Packmol` を利用します。

各クラスとメソッドの最新のシグネチャは {doc}`api/modules` を参照してください。
