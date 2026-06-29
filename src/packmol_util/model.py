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
class TetrahedralUnitFncSpec:
    """
    正四面体ユニットの FNC 指定と Packmol 用代表距離をまとめた仕様である。

    FNC の rmin/rmax を一次情報とし、その中央値から Packmol に渡す
    テンプレート構造用の代表距離を派生させる。
    """

    center_vertex_distance: float
    vertex_vertex_distance: float
    fnc_pairs_in_template: List[Tuple[int, int, int]]
    fnc_distance_ranges: Dict[int, Tuple[float, float]]


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
    # 以後の処理では何度も走査するため、Sequence を list に固定する。
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

def _normalize_atom_pair(
    atom_symbol_a: str,
    atom_symbol_b: str,
) -> Tuple[str, str]:
    """
    元素ペアを順序非依存のキーに正規化する。

    Li-P と P-Li は同じ pair distance を表すため、辞書キーを常に同じ順序へそろえる。
    ここでは文字列順を使うだけであり、元素の物理的な大小関係を意味しない。
    """
    # pair distance は元素ペアの順序に意味を持たない。
    # そのため、入力が ("Li", "O") でも ("O", "Li") でも同じキーへ落とす。
    if atom_symbol_a <= atom_symbol_b:
        return atom_symbol_a, atom_symbol_b
    return atom_symbol_b, atom_symbol_a


def solve_packing_radii_from_pair_distances(
    symbols: Sequence[str],
    minimum_distances_by_pair: Dict[Tuple[str, str], float],
    pair_distance_tolerance: float = 0.0,
) -> Dict[str, float]:
    """
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
    """
    symbol_list: List[str] = list(symbols)
    if len(symbol_list) == 0:
        raise ValueError("symbols は 1 つ以上必要である。")

    if pair_distance_tolerance < 0.0:
        raise ValueError("pair_distance_tolerance は 0 以上である必要がある。")

    # 入力された pair distance 辞書を、順序非依存の正規化キーで作り直す。
    # これにより ("Li", "O") と ("O", "Li") を同じ指定として扱う。
    normalized_minimum_distances_by_pair: Dict[Tuple[str, str], float] = {}
    for raw_pair_key, distance in minimum_distances_by_pair.items():
        if len(raw_pair_key) != 2:
            raise ValueError(f"pair key は 2 要素タプルで指定する: {raw_pair_key}")

        atom_symbol_a, atom_symbol_b = raw_pair_key
        normalized_pair_key = _normalize_atom_pair(atom_symbol_a, atom_symbol_b)

        if distance <= 0.0:
            raise ValueError(
                f"元素ペア距離 {normalized_pair_key} は正の値である必要がある。"
            )

        normalized_minimum_distances_by_pair[normalized_pair_key] = distance

    # 半径和モデルで確認すべき全ペアを作る。
    # symbols=[Li, P, O] なら Li-Li, Li-P, Li-O, P-P, P-O, O-O を確認する。
    pair_keys: List[Tuple[str, str]] = []
    for i, atom_symbol_a in enumerate(symbol_list):
        for atom_symbol_b in symbol_list[i:]:
            pair_key = _normalize_atom_pair(atom_symbol_a, atom_symbol_b)
            if pair_key not in normalized_minimum_distances_by_pair:
                raise ValueError(f"元素ペア距離 {pair_key} が指定されていない。")
            pair_keys.append(pair_key)

    # best_radii は、半径和で全ペア条件を満たす候補のうち、
    # 元の pair distance からの総短縮量が最も小さいものを保持する。
    best_radii: Optional[Dict[str, float]] = None
    best_score: Optional[float] = None

    # 自己ペア距離 Li-Li, P-P, O-O を少しずつ短くしながら候補を探索する。
    # 自己ペア距離を決めると r_Li, r_P, r_O が決まり、そこから Li-P などの異種ペア距離も決まる。
    # 完全な連続最適化ではなく、サンプル用の離散探索である。
    step_count: int = 40

    # 各元素について、自己ペア距離をどこまで緩めるかの候補リストを作る。
    # 自己ペア距離 d_ii が決まれば、その元素の packing radius は d_ii / 2 になる。
    diagonal_ranges: List[List[float]] = []
    for symbol in symbol_list:
        diagonal_key = _normalize_atom_pair(symbol, symbol)
        requested_distance = normalized_minimum_distances_by_pair[diagonal_key]

        values: List[float] = []
        for step_index in range(step_count + 1):
            reduction = pair_distance_tolerance * float(step_index) / float(step_count)
            diagonal_distance = requested_distance - reduction
            if diagonal_distance > 0.0:
                values.append(diagonal_distance)

        if len(values) == 0:
            raise ValueError(
                f"pair_distance_tolerance が大きすぎて自己ペア距離が非正になる: {diagonal_key}"
            )

        diagonal_ranges.append(values)

    def _search(
        depth: int,
        current_diagonal_distances: Dict[str, float],
    ) -> None:
        nonlocal best_radii
        nonlocal best_score

        if depth == len(symbol_list):
            # すべての自己ペア距離候補が決まったので、元素ごとの半径へ変換する。
            radii: Dict[str, float] = {}
            for symbol in symbol_list:
                radii[symbol] = current_diagonal_distances[symbol] / 2.0

            total_reduction: float = 0.0
            for pair_key in pair_keys:
                atom_symbol_a, atom_symbol_b = pair_key
                requested_distance = normalized_minimum_distances_by_pair[pair_key]
                effective_distance = radii[atom_symbol_a] + radii[atom_symbol_b]

                # 半径和が要求距離より大きい場合は、Packmol の排除距離が強すぎる。
                # ここでは「指定値以下に緩める」方針なので、この候補は棄却する。
                if effective_distance > requested_distance:
                    return

                # 半径和が要求距離より短い場合、その短縮量を評価する。
                # 短縮量が pair_distance_tolerance を超える候補は棄却する。
                reduction = requested_distance - effective_distance
                if reduction > pair_distance_tolerance:
                    return

                total_reduction += reduction

            if best_score is None or total_reduction < best_score:
                best_score = total_reduction
                best_radii = dict(radii)
            return

        # 次の元素について、許された自己ペア距離候補を順に試す。
        symbol = symbol_list[depth]
        for diagonal_distance in diagonal_ranges[depth]:
            current_diagonal_distances[symbol] = diagonal_distance
            _search(depth + 1, current_diagonal_distances)

    _search(depth=0, current_diagonal_distances={})

    if best_radii is None:
        raise ValueError(
            "指定された pair distance は、許容した緩和幅の中では両立しない。"
            f" pair_distance_tolerance={pair_distance_tolerance:.6f}"
        )

    return best_radii

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


def make_tetrahedral_unit_fnc_pairs(
    center_index: int = 1,
    vertex_indices: Optional[Sequence[int]] = None,
    center_vertex_constraint_type: int = 1,
    vertex_vertex_constraint_type: int = 2,
) -> List[Tuple[int, int, int]]:
    """
    正四面体ユニット用の FNC 局所ペアを作る。

    返り値は、テンプレート内の 1 始まり局所原子番号で表した
    (local_i, local_j, constraint_type) のリストである。
    PO4.xyz が P, O, O, O, O の順なら、P-O 4 本と O-O 6 本を返す。
    実際の Packmol XYZ 番号や POSCAR/cfg 番号への変換は builder 側で行う。
    """
    if vertex_indices is None:
        vertex_indices = [2, 3, 4, 5]

    vertex_index_list: List[int] = list(vertex_indices)
    if len(vertex_index_list) != 4:
        raise ValueError("正四面体ユニットの頂点原子は 4 個で指定する。")

    fnc_pairs: List[Tuple[int, int, int]] = []

    for vertex_index in vertex_index_list:
        fnc_pairs.append((center_index, vertex_index, center_vertex_constraint_type))

    for i, vertex_i in enumerate(vertex_index_list):
        for vertex_j in vertex_index_list[i + 1:]:
            fnc_pairs.append((vertex_i, vertex_j, vertex_vertex_constraint_type))

    return fnc_pairs

def _midpoint_distance(distance_range: Tuple[float, float], name: str) -> float:
    """
    FNC の rmin/rmax から Packmol テンプレート用の代表距離を返す。
    """
    rmin, rmax = distance_range
    if rmin <= 0.0:
        raise ValueError(f"{name} の rmin は正の値で指定する。")
    if rmax <= 0.0:
        raise ValueError(f"{name} の rmax は正の値で指定する。")
    if rmin >= rmax:
        raise ValueError(f"{name} は rmin < rmax で指定する。")
    return 0.5 * (rmin + rmax)


def make_tetrahedral_unit_fnc_spec_from_ranges(
    center_vertex_range: Tuple[float, float],
    vertex_vertex_range: Tuple[float, float],
    center_index: int = 1,
    vertex_indices: Optional[Sequence[int]] = None,
    center_vertex_constraint_type: int = 1,
    vertex_vertex_constraint_type: int = 2,
    geometry_distance_tolerance: float = 0.05,
) -> TetrahedralUnitFncSpec:
    """
    FNC の rmin/rmax を一次情報として、正四面体ユニットの仕様を作る。

    center_vertex_range は中心原子-頂点原子の FNC 距離範囲である。
    vertex_vertex_range は頂点原子-頂点原子の FNC 距離範囲である。

    Packmol に渡す PO4 などのテンプレート XYZ 用距離は、これらの範囲の
    中央値から派生させる。したがって、Packmol 用距離と FNC 用距離範囲を
    利用側で二重管理しない。

    geometry_distance_tolerance は FNC の許容幅ではない。
    FNC range の中央値から作った中心-頂点距離と頂点-頂点距離が、
    正四面体として幾何学的に整合しているかを検査するためだけに使う。
    """
    center_vertex_distance = _midpoint_distance(
        center_vertex_range,
        "center_vertex_range",
    )
    vertex_vertex_distance = _midpoint_distance(
        vertex_vertex_range,
        "vertex_vertex_range",
    )

    _validate_regular_tetrahedron_distances(
        center_vertex_distance=center_vertex_distance,
        vertex_vertex_distance=vertex_vertex_distance,
        distance_tolerance=geometry_distance_tolerance,
    )

    fnc_pairs_in_template = make_tetrahedral_unit_fnc_pairs(
        center_index=center_index,
        vertex_indices=vertex_indices,
        center_vertex_constraint_type=center_vertex_constraint_type,
        vertex_vertex_constraint_type=vertex_vertex_constraint_type,
    )

    return TetrahedralUnitFncSpec(
        center_vertex_distance=center_vertex_distance,
        vertex_vertex_distance=vertex_vertex_distance,
        fnc_pairs_in_template=fnc_pairs_in_template,
        fnc_distance_ranges={
            center_vertex_constraint_type: center_vertex_range,
            vertex_vertex_constraint_type: vertex_vertex_range,
        },
    )

