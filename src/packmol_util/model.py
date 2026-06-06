#!/usr/bin/env python3
"""
材料非依存の構造テンプレートと Packmol 用レシピを準備する共通モジュールである。

このファイルには、Li3PO4 や FeSiB のような物質固有の数値を置かない。
物質固有の原子数、密度、分子内距離、packing 半径は make_*.py 側で与える。

ここで行うことは、次の二つである。

1. Packmol に渡す単原子テンプレートまたは分子ユニットテンプレートの XYZ を作る。
2. make_*.py 側で決めたテンプレートと個数を、Packmol 入力用のレシピにまとめる。
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class StructureSpec:
    """
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
    """

    # Packmol に渡す 1 個のテンプレート XYZ ファイルである。
    # 単原子系なら Fe.xyz や Li.xyz、分子ユニット系なら PO4.xyz などを指す。
    xyz_file: str

    # 上のテンプレートをセル内に何個配置するかを表す。
    # PO4.xyz の number=64 は、PO4 ユニットを 64 個配置するという意味である。
    number: int

    # Packmol の atoms ... radius ... end atoms へ変換するための指定である。
    # make_*.py 側では元素記号で書き、packmol_inp.py 側で XYZ 内 atom index へ変換する。
    # これは分子内距離ではなく、配置時の packing 用排除半径である。
    packing_radii_by_atom_symbol: Optional[Dict[str, float]] = None


@dataclass(frozen=True)
class MaterialRecipe:
    """
    make_*.py 側で定義した構造作成条件を Packmol 入力生成へ渡すためのレシピである。

    total_atom_count は、セル内に最終的に入る総原子数である。
    Li3PO4 で Li 原子 192 個と PO4 ユニット 64 個を置く場合、総原子数は
    192 + 64 * 5 = 512 である。

    symbols と ratios は、最終的な POSCAR 変換や密度計算で使う元素順序と組成比である。
    structures は、Packmol に渡す structure ブロックの列である。
    """

    # 最終的に POSCAR に入る実原子数である。
    # structure 数ではなく、テンプレート内原子数も掛けた値である。
    total_atom_count: int

    # POSCAR に出力する元素順序である。
    symbols: List[str]

    # 元素順序に対応する組成比である。
    ratios: List[int]

    # Packmol に渡す structure ブロックの列である。
    structures: List[StructureSpec]


def write_xyz_template(
    filename: str,
    atoms: Sequence[Tuple[str, float, float, float]],
    comment: str = "template",
) -> None:
    """
    任意のテンプレート構造を XYZ として書き出す。

    atoms には、1 個の単原子テンプレートまたは 1 個の分子ユニットテンプレートの
    原子座標を渡す。ここで書かれた原子順が、Packmol の atom index の順番になる。
    """
    # XYZ 形式では 1 行目にテンプレート内原子数を書く。
    # Packmol はこの XYZ を 1 個の structure テンプレートとして読む。
    with open(filename, "w") as f:
        f.write(f"{len(atoms)}\n")

        # 2 行目はコメント行である。Packmol の配置には使わない。
        f.write(f"{comment}\n")

        # 3 行目以降が、テンプレート内部の原子順序と座標である。
        # この順序が Packmol の atoms 1, atoms 2, ... の番号に対応する。
        for symbol, x_value, y_value, z_value in atoms:
            f.write(f"{symbol}  {x_value:.10f}  {y_value:.10f}  {z_value:.10f}\n")


def write_single_atom_xyz(
    filename: str,
    element: str,
) -> None:
    """
    Packmol に単原子を配置させるための 1 原子 XYZ テンプレートを書き出す。

    これは FeSiB の Fe、Si、B のように、分子ユニットを作らず、元素ごとの単原子を
    ランダム配置したい場合に使う。
    """
    # 単原子テンプレートでは、テンプレート内に原子を 1 個だけ置く。
    # Packmol はこの 1 原子テンプレートを number 個だけ複製して配置する。
    write_xyz_template(
        filename=filename,
        atoms=[(element, 0.0, 0.0, 0.0)],
        comment=f"{element} atom template",
    )


def _validate_regular_tetrahedron_distances(
    center_vertex_distance: float,
    vertex_vertex_distance: float,
    distance_tolerance: float,
) -> None:
    """
    正四面体ユニットの中心-頂点距離と頂点-頂点距離の整合性を確認する。

    正四面体では、中心原子から各頂点原子までの距離を指定すると、頂点原子同士の
    距離は幾何学的に決まる。したがって、P-O と O-O を同時に入力として受ける場合、
    両者が正四面体として矛盾していないか確認する必要がある。
    """
    if center_vertex_distance <= 0.0:
        raise ValueError("center_vertex_distance は正の値で指定する。")

    if vertex_vertex_distance <= 0.0:
        raise ValueError("vertex_vertex_distance は正の値で指定する。")

    if distance_tolerance < 0.0:
        raise ValueError("distance_tolerance は 0 以上の値で指定する。")

    # 正四面体では、中心-頂点距離を決めると頂点-頂点距離は一意に決まる。
    # PO4 なら P-O 距離から O-O 距離が決まる。
    expected_vertex_vertex_distance: float = center_vertex_distance * math.sqrt(8.0 / 3.0)

    # make_*.py 側で明示された O-O 距離が、正四面体幾何から外れていないかを見る。
    distance_error: float = abs(expected_vertex_vertex_distance - vertex_vertex_distance)

    if distance_error > distance_tolerance:
        message = (
            "正四面体では center_vertex_distance と vertex_vertex_distance を "
            "独立には指定できない。"
            f" center_vertex_distance={center_vertex_distance:.10f},"
            f" vertex_vertex_distance={vertex_vertex_distance:.10f},"
            f" expected_vertex_vertex_distance={expected_vertex_vertex_distance:.10f},"
            f" distance_error={distance_error:.10f},"
            f" distance_tolerance={distance_tolerance:.10f}"
        )
        raise ValueError(message)


def write_tetrahedral_unit_xyz(
    filename: str,
    center_element: str,
    vertex_element: str,
    center_vertex_distance: float,
    vertex_vertex_distance: float,
    distance_tolerance: float = 0.05,
) -> None:
    """
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
    """
    _validate_regular_tetrahedron_distances(
        center_vertex_distance=center_vertex_distance,
        vertex_vertex_distance=vertex_vertex_distance,
        distance_tolerance=distance_tolerance,
    )

    # (±a, ±a, ±a) 型の 4 点を選ぶと、中心原子を原点に置いた正四面体になる。
    # 中心から各頂点までの距離は sqrt(3) * a なので、a を下のように決める。
    scale: float = center_vertex_distance / math.sqrt(3.0)

    # 1 番目の原子が中心原子、2-5 番目の原子が頂点原子である。
    # この順序は Packmol の atom index にも反映される。
    atoms: List[Tuple[str, float, float, float]] = [
        (center_element, 0.0, 0.0, 0.0),
        (vertex_element, scale, scale, scale),
        (vertex_element, scale, -scale, -scale),
        (vertex_element, -scale, scale, -scale),
        (vertex_element, -scale, -scale, scale),
    ]
    write_xyz_template(
        filename=filename,
        atoms=atoms,
        comment=f"{center_element}{vertex_element}4 tetrahedral unit template",
    )


def make_material_recipe(
    symbols: Sequence[str],
    ratios: Sequence[int],
    structures: Sequence[StructureSpec],
) -> MaterialRecipe:
    """
    make_*.py 側で作った structure 指定を Packmol 用レシピにまとめる。

    この関数は分子構造を作らない。Packmol 入力ファイルも書かない。
    すでに作られた XYZ テンプレートと、それぞれを何個配置するかという情報を、
    MaterialRecipe として一つにまとめる。

    Li3PO4 では、Li.xyz を何個置くか、PO4.xyz を何個置くかを structures に渡す。
    FeSiB では、Fe.xyz、Si.xyz、B.xyz をそれぞれ何個置くかを structures に渡す。
    """
    if len(symbols) != len(ratios):
        raise ValueError("symbols と ratios の長さが一致していません。")

    # Sequence のまま保持せず、後段で扱いやすい list に固定する。
    symbol_list: List[str] = list(symbols)
    ratio_list: List[int] = list(ratios)
    structure_list: List[StructureSpec] = list(structures)

    # total_atom_count は、Packmol の structure 個数の合計ではない。
    # PO4 のように 1 テンプレートが 5 原子を含む場合があるため、XYZ 先頭行から
    # テンプレート内原子数を読み、number と掛け合わせて総原子数を作る。
    total_atom_count: int = 0
    for structure in structure_list:
        atom_count_in_template: int = _count_atoms_in_xyz_file(
            xyz_file=structure.xyz_file,
        )
        total_atom_count = total_atom_count + structure.number * atom_count_in_template

    return MaterialRecipe(
        total_atom_count=total_atom_count,
        symbols=symbol_list,
        ratios=ratio_list,
        structures=structure_list,
    )


def _count_atoms_in_xyz_file(
    xyz_file: str,
) -> int:
    """
    XYZ ファイル先頭行から、1 テンプレート中の原子数を読む。

    単原子テンプレートなら 1、PO4 テンプレートなら 5 を返す。
    MaterialRecipe.total_atom_count を、structure の個数ではなく実際の総原子数にするために使う。
    """
    with open(xyz_file, "r") as f:
        first_line: str = f.readline().strip()

    # XYZ の 1 行目はテンプレート内の原子数である。
    atom_count: int = int(first_line)
    if atom_count <= 0:
        raise ValueError(f"XYZ ファイルの原子数が正ではない: {xyz_file}")

    return atom_count


def make_atomic_mixture_recipe(
    symbols: Sequence[str],
    ratios: Sequence[int],
    total_atom_count: int,
    xyz_files: Optional[Sequence[str]] = None,
) -> MaterialRecipe:
    """
    複数元素の単原子テンプレートを作り、Packmol 用レシピを返す。

    FeSiB のように、分子ユニットを使わず、Fe、Si、B の単原子をそれぞれ指定数だけ
    ランダム配置する場合に使う。

    total_atom_count は、最終セルに入れる総原子数である。
    ratios の比に従い、各元素の原子数を決める。
    例えば total_atom_count=100、ratios=[80, 9, 11] なら、Fe 80 個、Si 9 個、
    B 11 個の単原子テンプレートを Packmol に配置させる recipe を作る。
    """
    if len(symbols) != len(ratios):
        raise ValueError("symbols と ratios の長さが一致していません。")

    if total_atom_count <= 0:
        raise ValueError("total_atom_count は正の整数である必要があります。")

    ratio_sum: int = sum(ratios)
    if ratio_sum <= 0:
        raise ValueError("ratios の合計は正の整数である必要があります。")

    if total_atom_count % ratio_sum != 0:
        raise ValueError("total_atom_count は ratios の合計の整数倍である必要があります。")

    # xyz_files を明示しない場合は、元素記号から Fe.xyz, Si.xyz のように自動命名する。
    # FeSiB のような単原子混合系のサンプルでは、この規約で十分である。
    if xyz_files is None:
        actual_xyz_files: List[str] = []
        for symbol in symbols:
            actual_xyz_files.append(f"{symbol}.xyz")
    else:
        if len(symbols) != len(xyz_files):
            raise ValueError("symbols と xyz_files の長さが一致していません。")
        actual_xyz_files = list(xyz_files)

    # total_atom_count が組成比の整数倍であるため、各元素の配置数は倍率で決まる。
    multiplier: int = total_atom_count // ratio_sum
    structures: List[StructureSpec] = []

    for symbol, ratio, xyz_file in zip(symbols, ratios, actual_xyz_files):
        # Fe80Si9B11 で total_atom_count=100 の場合、ratio がそのまま各元素数になる。
        atom_count: int = ratio * multiplier

        # 各元素の 1 原子テンプレートを作る。
        write_single_atom_xyz(filename=xyz_file, element=symbol)

        # その単原子テンプレートを atom_count 個配置する structure として recipe に登録する。
        structures.append(StructureSpec(xyz_file=xyz_file, number=atom_count))

    return MaterialRecipe(
        total_atom_count=total_atom_count,
        symbols=list(symbols),
        ratios=list(ratios),
        structures=structures,
    )
