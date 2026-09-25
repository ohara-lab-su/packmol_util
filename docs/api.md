---
layout: page
title: API リファレンス
permalink: /api.html
---

# API リファレンス

このページは `doc/generate_api.py` により Python ソースのシグネチャと docstring から自動生成されます。

* TOC
{:toc}

## `packmol_util.builder`

packmol_util/builder.py

詳細なファイルのバケツリレーを隠蔽し、
数行でアモルファス構造を作成するための高レベル統合モジュール。

以下の 3 点を外部入力の基準とする：
    1. 化学量論比（整数比）
    2. 密度 [g/cm^3] または 数密度 [1/Å^3] のいずれか一方
    3. セル内の総原子数 total_atom_count

【重要】指定した total_atom_count が ratios の合計で割り切れない（組成比を維持できない）場合、
プログラムが破綻するのを防ぐため、指定された原子数に最も近い「割り切れる総原子数」へ自動補正を行う。
内部で計算された全体のスケール倍率（multiplier）を外部に公開（プロパティ化）することで、
利用側のスクリプトがユニット構成単位でのパッキング個数を一元管理できるように設計されている。

### `class AmorphousBuilder`

#### `AmorphousBuilder.__init__`

```python
def __init__(self, symbols: List[str], ratios: List[int], total_atom_count: int, minimum_separation: float, mass_density: Optional[float]=None, number_density: Optional[float]=None, packmol_bin: str='packmol')
```

#### `AmorphousBuilder.multiplier`

```python
def multiplier(self) -> int
```

全体の化学量論比に対するセルのスケール倍率を返す。
利用側のスクリプトは、この倍率をユニットの1式あたり構成比に乗算することで、
Packmol に引き渡すべき実際の複製個数（number）を算出する。

#### `AmorphousBuilder.add_template`

```python
def add_template(self, xyz_file: str, number: int, packing_radii: Optional[Dict[str, float]]=None, fnc_pairs_in_template: Optional[List[Tuple[int, int, int]]]=None, fnc_distance_ranges: Optional[Dict[int, Tuple[float, float]]]=None, fnc_output_constraint_types: Optional[List[int]]=None)
```

Packmol の 1 つの structure ブロックに対応するテンプレート情報を登録する。

引数の説明：
    xyz_file: Packmol に渡す単原子または分子ユニットテンプレートの座標ファイル名 (.xyz)
    number: そのテンプレートを何個複製して配置するかを指定する [int]
    packing_radii: Packmol 配置時に使う元素記号別の排除半径の辞書（任意）。
                   分子ユニット内部の結合距離や形状を作る値ではない。
    fnc_pairs_in_template: テンプレート内の局所原子番号で指定した FNC ペア。
                           (local_i, local_j, constraint_type) のリストで指定する。
    fnc_distance_ranges: FNC constraint type ごとの距離範囲。
                         {type: (rmin, rmax)} で指定する。
    fnc_output_constraint_types: .fnc に実際に出力する constraint type のリスト。
                                 None の場合は全 type を出力する。
                                 例: [1] を指定すると type 1 のペアだけを出力する。
                                 Packmol 用 XYZ テンプレートの形状や配置には影響しない。

#### `AmorphousBuilder.build`

```python
def build(self, output_prefix: str, fnc_file: Optional[str]=None)
```

---

## `packmol_util.model`

材料非依存の構造テンプレートと Packmol 用レシピを準備する共通モジュールである。

このファイルには、Li3PO4 や FeSiB のような物質固有の数値を置かない。
物質固有の原子数、密度、分子内距離、packing 半径は make_*.py 側で与える。

ここで行うことは、次の二つである。

1. Packmol に渡す単原子テンプレートまたは分子ユニットテンプレートの XYZ を作る。
2. make_*.py 側で決めたテンプレートと個数を、Packmol 入力用のレシピにまとめる。

### `class StructureSpec`

Packmol の 1 つの structure ブロックに対応する情報である。

xyz_file は、Packmol に渡す 1 個の単原子テンプレートまたは 1 個の分子ユニット
テンプレートの座標ファイル名である。

number は、そのテンプレートを Packmol がセル内に何個配置するかを表す。
例えば Li.xyz の number が 192 なら、Li 単原子テンプレートを 192 個配置する。
PO4.xyz の number が 64 なら、PO4 ユニットを 64 個配置する。

packing_radii_by_atom_symbol は、Packmol の atoms ... radius ... end atoms 指定へ
変換するための情報である。キーは元素記号であり、Packmol の atom index ではない。
Packmol 入力ファイルに書くときに、packmol_inp.py が XYZ 内の原子順を読んで、
元素記号から atom index へ変換する。

この packing 半径は分子ユニット内部の結合距離ではない。
分子ユニット内部の距離は、write_tetrahedral_unit_xyz() などのテンプレート生成関数で
決める。

### `class TetrahedralUnitFncSpec`

正四面体ユニットの FNC 指定と Packmol 用代表距離をまとめた仕様である。

FNC の rmin/rmax を一次情報とし、その中央値から Packmol に渡す
テンプレート構造用の代表距離を派生させる。

### `class MaterialRecipe`

make_*.py 側で定義した構造作成条件を Packmol 入力生成へ渡すためのレシピである。

total_atom_count は、セル内に最終的に入る総原子数である。
Li3PO4 で Li 原子 192 個と PO4 ユニット 64 個を置く場合、総原子数は
192 + 64 * 5 = 512 である。

symbols と ratios は、最終的な POSCAR 変換や密度計算で使う元素順序と組成比である。
structures は、Packmol に渡す structure ブロックの列である。

### `write_xyz_template`

```python
def write_xyz_template(filename: str, atoms: Sequence[Tuple[str, float, float, float]], comment: str='template') -> None
```

任意のテンプレート構造を XYZ として書き出す。

atoms には、1 個の単原子テンプレートまたは 1 個の分子ユニットテンプレートの
原子座標を渡す。ここで書かれた原子順が、Packmol の atom index の順番になる。

### `write_single_atom_xyz`

```python
def write_single_atom_xyz(filename: str, element: str) -> None
```

Packmol に単原子を配置させるための 1 原子 XYZ テンプレートを書き出す。

これは FeSiB の Fe、Si、B のように、分子ユニットを作らず、元素ごとの単原子を
ランダム配置したい場合に使う。

### `write_tetrahedral_unit_xyz`

```python
def write_tetrahedral_unit_xyz(filename: str, center_element: str, vertex_element: str, center_vertex_distance: float, vertex_vertex_distance: float, distance_tolerance: float=0.05) -> None
```

中心原子 1 個と頂点原子 4 個からなる正四面体ユニットを書き出す。

PO4 の場合、center_element は P、vertex_element は O である。
center_vertex_distance は P-O 距離である。
vertex_vertex_distance は O-O 距離である。

この関数で作る XYZ が、Packmol に渡す「1 個の PO4 ユニット」の形になる。
Packmol はこの XYZ を読み、PO4 ユニットの内部形状を保ったまま、指定個数を
セル内に配置する。

packing 半径や最小分離距離はここでは扱わない。それらは、すでに作った
ユニット同士、またはユニットと単原子が配置時に近づきすぎないようにするための
Packmol 入力側の条件である。

### `make_material_recipe`

```python
def make_material_recipe(symbols: Sequence[str], ratios: Sequence[int], structures: Sequence[StructureSpec]) -> MaterialRecipe
```

make_*.py 側で作った structure 指定を Packmol 用レシピにまとめる。

この関数は分子構造を作らない。Packmol 入力ファイルも書かない。
すでに作られた XYZ テンプレートと、それぞれを何個配置するかという情報を、
MaterialRecipe として一つにまとめる。

Li3PO4 では、Li.xyz を何個置くか、PO4.xyz を何個置くかを structures に渡す。
FeSiB では、Fe.xyz、Si.xyz、B.xyz をそれぞれ何個置くかを structures に渡す。

### `solve_packing_radii_from_pair_distances`

```python
def solve_packing_radii_from_pair_distances(symbols: Sequence[str], minimum_distances_by_pair: Dict[Tuple[str, str], float], pair_distance_tolerance: float=0.0) -> Dict[str, float]
```

希望する元素ペア距離を Packmol の原子半径モデルへ近似変換する。

Packmol は Li-O=1.55, P-O=1.30 のような元素ペア距離表を直接受け取らない。
Packmol が受け取れるのは atom index ごとの radius であり、実効距離は
radius_i + radius_j として扱われる。

この関数は、make_*.py 側で書いた元素ペア距離表を、Packmol に渡せる
元素ごとの packing radius に変換するための補助関数である。

ただし、任意の元素ペア距離表が半径和で完全に表せるわけではない。
例えば Li-Li, Li-P, Li-O, P-P, P-O, O-O をすべて独立に与えると、
半径和モデルでは矛盾する場合がある。

pair_distance_tolerance は、その矛盾をどの程度まで短い距離側へ緩めて許すかを表す。
この値は Packmol の tolerance ではない。元素ペア距離表を packing radius に
近似変換するための内部的な許容幅である。

戻り値は {"Li": r_Li, "P": r_P, "O": r_O} のような辞書である。
この辞書は StructureSpec.packing_radii_by_atom_symbol に渡し、
packmol_inp.py 側で atom index 指定へ変換される。

注意：この変換で得られる半径は、分子ユニット内部の距離を決めるものではない。
例えば PO4 の P-O / O-O 距離は write_tetrahedral_unit_xyz() が作る XYZ 座標で決まる。
この関数が扱うのは、Packmol が複数ユニットを配置するときに使う半径和モデルである。

### `make_atomic_mixture_recipe`

```python
def make_atomic_mixture_recipe(symbols: Sequence[str], ratios: Sequence[int], total_atom_count: int, xyz_files: Optional[Sequence[str]]=None) -> MaterialRecipe
```

複数元素の単原子テンプレートを作り、Packmol 用レシピを返す。

FeSiB のように、分子ユニットを使わず、Fe、Si、B の単原子をそれぞれ指定数だけ
ランダム配置する場合に使う。

total_atom_count は、最終セルに入れる総原子数である。
ratios の比に従い、各元素の原子数を決める。
例えば total_atom_count=100、ratios=[80, 9, 11] なら、Fe 80 個、Si 9 個、
B 11 個の単原子テンプレートを Packmol に配置させる recipe を作る。

### `make_tetrahedral_unit_fnc_pairs`

```python
def make_tetrahedral_unit_fnc_pairs(center_index: int=1, vertex_indices: Optional[Sequence[int]]=None, center_vertex_constraint_type: int=1, vertex_vertex_constraint_type: int=2) -> List[Tuple[int, int, int]]
```

正四面体ユニット用の FNC 局所ペアを作る。

返り値は、テンプレート内の 1 始まり局所原子番号で表した
(local_i, local_j, constraint_type) のリストである。
PO4.xyz が P, O, O, O, O の順なら、P-O 4 本と O-O 6 本を返す。
実際の Packmol XYZ 番号や POSCAR/cfg 番号への変換は builder 側で行う。

### `make_tetrahedral_unit_fnc_spec_from_ranges`

```python
def make_tetrahedral_unit_fnc_spec_from_ranges(center_vertex_range: Tuple[float, float], vertex_vertex_range: Tuple[float, float], center_index: int=1, vertex_indices: Optional[Sequence[int]]=None, center_vertex_constraint_type: int=1, vertex_vertex_constraint_type: int=2, geometry_distance_tolerance: float=0.05) -> TetrahedralUnitFncSpec
```

FNC の rmin/rmax を一次情報として、正四面体ユニットの仕様を作る。

center_vertex_range は中心原子-頂点原子の FNC 距離範囲である。
vertex_vertex_range は頂点原子-頂点原子の FNC 距離範囲である。

Packmol に渡す PO4 などのテンプレート XYZ 用距離は、これらの範囲の
中央値から派生させる。したがって、Packmol 用距離と FNC 用距離範囲を
利用側で二重管理しない。

geometry_distance_tolerance は FNC の許容幅ではない。
FNC range の中央値から作った中心-頂点距離と頂点-頂点距離が、
正四面体として幾何学的に整合しているかを検査するためだけに使う。

---

## `packmol_util.packmol`

K.NAKADA, kengo.nakada@gmail.com
make_amorphous.py

アモルファス初期構造を Packmol により生成するための
入力ファイル (packmol.inp) を作成するスクリプト。

本スクリプトは、以下の 3 点を外部入力とする：

    1. 化学量論比（整数比）
    2. 密度 [g/cm^3] または 数密度 [1/Å^3] のいずれか一方
    3. セル内の総原子数 total_atom_count

Packmol は密度・化学量論比の概念を持たないため、本スクリプト側で
原子数とセル一辺長 L を計算し、Packmol 形式の inside box 指定に変換する。

### `class Packmol`

Packmol 実行と、密度・セル長・POSCAR 変換をまとめる補助クラスである。

このクラスは分子ユニットの形を作らない。
PO4 のようなテンプレート形状は model.py が作る。

このクラスが担当するのは、密度からセル長を決めること、Packmol を実行すること、
Packmol が出力した XYZ を POSCAR へ変換することである。

#### `Packmol.__init__`

```python
def __init__(self, input_file: Optional[str]=None, output_xyz: Optional[str]=None, output_log: Optional[str]=None, packmol_bin: Optional[str]=None, logger: Optional[XLogger]=None) -> None
```

#### `Packmol.get_unit_atom_count`

```python
def get_unit_atom_count(self, ratios: Sequence[int]) -> int
```

化学量論比 1 単位あたりの原子数を返す。

Fe80Si9B11 なら 80 + 9 + 11 = 100 である。
Li3PO4 なら 3 + 1 + 4 = 8 である。
この値は、組成比を保ったまま総原子数候補を列挙するときに使う。

#### `Packmol.count_atoms_in_xyz`

```python
def count_atoms_in_xyz(self, xyz_file: str) -> int
```

XYZ ファイル先頭行から原子数を読む。

#### `Packmol.get_atomic_weight`

```python
def get_atomic_weight(element: str) -> float
```

元素記号から原子量を取得する。

#### `Packmol.average_atomic_weight`

```python
def average_atomic_weight(self, symbols: Sequence[str], ratios: Sequence[int]) -> float
```

汎用

化学量論比から平均原子量を計算する。

#### `Packmol.number_density_from_mass_density`

```python
def number_density_from_mass_density(self, symbols: Sequence[str], ratios: Sequence[int], mass_density_g_cm3: float) -> float
```

汎用

質量密度から数密度 n [1/Å^3] を計算する。

#### `Packmol.mass_density_from_number_density`

```python
def mass_density_from_number_density(self, symbols: Sequence[str], ratios: Sequence[int], number_density_A3: float) -> float
```

汎用

数密度 n [1/Å^3] から質量密度 ρ [g/cm^3] を計算する。

#### `Packmol.cell_length_from_number_density`

```python
def cell_length_from_number_density(self, total_atom_count: int, number_density_A3: float) -> float
```

汎用

総原子数と数密度から立方体セル長 L [Å] を計算する。

#### `Packmol.compute_element_counts`

```python
def compute_element_counts(self, symbols: Sequence[str], ratios: Sequence[int], total_atom_count: int) -> Dict[str, int]
```

化学量論比と total_atom_count から各元素の原子数を決める。

total_atom_count が ratios の整数倍でない場合でも、端数の大きい元素へ
残りの原子を割り当て、総原子数が total_atom_count になるようにする。
厳密な組成比だけを許す用途では、make_atomic_mixture_recipe() のように
整数倍を要求する関数を使う。

#### `Packmol.compute_cell_sizes`

```python
def compute_cell_sizes(self, ratios: Sequence[int], max_atom_count: int) -> List[int]
```

汎用

化学量論比を厳密に保つセル原子数を列挙する。

#### `Packmol.write_single_atom_xyz`

```python
def write_single_atom_xyz(self, filename: str, element: str) -> None
```

単一原子のみを含む XYZ ファイルを生成する。

#### `Packmol.run_packmol`

```python
def run_packmol(self, input_file: Optional[str]=None, output_log: Optional[str]=None, packmol_bin: Optional[str]=None) -> None
```

Packmol を実行する。

Packmol はコマンドライン引数で入力ファイル名を受け取るのではなく、
標準入力から .inp を読む使い方を前提にしている。
そのため、このメソッドでは input_file を stdin に接続する。

#### `Packmol.xyz_to_poscar`

```python
def xyz_to_poscar(self, xyz_file: str, poscar_file: str='POSCAR', packmol_inp: str='packmol.inp', comment: str='packmol', elements: Optional[List[str]]=None) -> Dict[int, int]
```

Packmol が出力した XYZ を VASP POSCAR へ変換する。

Packmol 出力は元素が混在した Cartesian XYZ である。
VASP POSCAR では元素ごとに座標をまとめ、Direct 座標で書くため、
ここで元素順に並べ替えてセル長で割る。

セル長は packmol.inp の inside box 行から読む。

Returns:
    Dict[int, int]: Packmol XYZ の 1 始まり原子番号から、POSCAR の
        1 始まり原子番号への対応表。FNC を最終 POSCAR/cfg 番号で
        書くために使う。

#### `Packmol.write_fnc_file`

```python
def write_fnc_file(self, fnc_file: str, total_atom_count: int, fnc_pairs: Sequence[Tuple[int, int, int]], distance_ranges_by_type: Dict[int, Tuple[float, float]], title: str='Fixed neighbours constraints generated from Packmol mapping') -> None
```

RMC_POT の通常 FNC 用 *.fnc ファイルを書き出す。

fnc_pairs は、すでに最終 POSCAR/cfg の 1 始まり原子番号へ変換済みの
(atom_i, atom_j, constraint_type) で指定する。
RMC_POT の通常 FNC は、各原子について FNC neighbour の index と
constraint type を列挙する形式なので、ここで対称な neighbour list へ展開する。

---

## `packmol_util.packmol_inp`

Packmol の入力ファイルを構築するための共通クラスである。

このファイルは、物質固有の構造を知らない。
make_*.py 側から渡された structure 情報を、Packmol の .inp 形式へ変換する。

### `class PackmolInp`

Packmol の .inp ファイルを構築するためのクラスである。

minimum_separation_distance は、Packmol 入力ファイル先頭の tolerance に対応する。
これは、配置時に原子や分子ユニットが近づきすぎないようにする全体条件である。

add_structure() で登録する 1 件が、Packmol 入力の structure ... end structure
ブロック 1 個に対応する。

#### `PackmolInp.__init__`

```python
def __init__(self, minimum_separation_distance: float, output_xyz: str, box_length: float, use_pbc: bool=False) -> None
```

#### `PackmolInp.add_structure`

```python
def add_structure(self, xyz_file: str, number: int, packing_radii_by_atom_symbol: Optional[Dict[str, float]]=None) -> None
```

1 つの単原子テンプレートまたは分子ユニットテンプレートを登録する。

xyz_file は、Li.xyz、Fe.xyz、PO4.xyz などのテンプレート座標である。
number は、そのテンプレートを Packmol が何個配置するかである。

packing_radii_by_atom_symbol は、必要な場合だけ指定する配置用の排除半径である。
これは分子内距離ではない。例えば PO4 の P-O 距離や O-O 距離は、PO4.xyz を
作る段階で決まる。
ここで与える半径は、Packmol が複数の structure を箱の中へ置くときの重なり回避に使う。

#### `PackmolInp.write`

```python
def write(self, inp_file: str) -> None
```

Packmol の .inp ファイルを書き出す。

ここで、make_*.py 側で作った recipe が、Packmol の具体的な入力形式になる。
structure ブロックは、1 種類の単原子テンプレートまたは 1 種類の分子ユニットを
Packmol に何個配置させるかを表す。

---

## `packmol_util.config`

packmol_util の設定保持クラス。

### `class Config`

packmol_util 用の設定値を保持する。

#### `Config.__init__`

```python
def __init__(self, yaml_path: Optional[str]=None, logger: Optional[XLogger]=None) -> None
```

#### `Config.load_yaml`

```python
def load_yaml(cls, yaml_path: Optional[str]=None) -> None
```

YAML の内容でクラス変数を上書きする。

---

## `packmol_util.param`

定数定義。

---
