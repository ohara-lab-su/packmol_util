#!/usr/bin/env python3
"""
材料非依存のテンプレート構造を準備する補助関数である。
Packmol クラス本体へ材料専用処理を入れないために分離する。
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class StructureSpec:
    """
    Packmol に渡す 1 つの structure 情報である。
    """

    xyz_file: str
    number: int
    packing_radii_by_atom_symbol: Optional[Dict[str, float]] = None


@dataclass(frozen=True)
class MaterialRecipe:
    """
    Packmol 入力準備情報である。
    """

    total_atom_count: int
    symbols: List[str]
    ratios: List[int]
    structures: List[StructureSpec]


def write_xyz_template(
    filename: str,
    atoms: Sequence[Tuple[str, float, float, float]],
    comment: str = "template",
) -> None:
    """
    任意のテンプレート構造を XYZ として書き出す。
    """
    with open(filename, "w") as f:
        f.write(f"{len(atoms)}\n")
        f.write(f"{comment}\n")
        for symbol, x_value, y_value, z_value in atoms:
            f.write(f"{symbol}  {x_value:.10f}  {y_value:.10f}  {z_value:.10f}\n")


def write_single_atom_xyz(
    filename: str,
    element: str,
) -> None:
    """
    単一原子テンプレートを書き出す。
    """
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
    """
    if center_vertex_distance <= 0.0:
        raise ValueError("center_vertex_distance は正の値で指定する。")

    if vertex_vertex_distance <= 0.0:
        raise ValueError("vertex_vertex_distance は正の値で指定する。")

    if distance_tolerance < 0.0:
        raise ValueError("distance_tolerance は 0 以上の値で指定する。")

    expected_vertex_vertex_distance: float = center_vertex_distance * math.sqrt(8.0 / 3.0)
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

    center_vertex_distance は中心原子と頂点原子の距離である。
    vertex_vertex_distance は頂点原子同士の距離である。
    正四面体では両者は独立ではないため、指定値の整合性を確認する。
    """
    _validate_regular_tetrahedron_distances(
        center_vertex_distance=center_vertex_distance,
        vertex_vertex_distance=vertex_vertex_distance,
        distance_tolerance=distance_tolerance,
    )

    scale: float = center_vertex_distance / math.sqrt(3.0)
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
    元素、組成比、Packmol structure 情報からレシピを作る。
    """
    if len(symbols) != len(ratios):
        raise ValueError("symbols と ratios の長さが一致していません。")

    symbol_list: List[str] = list(symbols)
    ratio_list: List[int] = list(ratios)
    structure_list: List[StructureSpec] = list(structures)

    total_atom_count: int = 0
    for structure in structure_list:
        total_atom_count = total_atom_count + structure.number

    return MaterialRecipe(
        total_atom_count=total_atom_count,
        symbols=symbol_list,
        ratios=ratio_list,
        structures=structure_list,
    )


def make_atomic_mixture_recipe(
    symbols: Sequence[str],
    ratios: Sequence[int],
    total_atom_count: int,
    xyz_files: Optional[Sequence[str]] = None,
) -> MaterialRecipe:
    """
    複数元素の単原子テンプレートを作り、Packmol 用レシピを返す。
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

    if xyz_files is None:
        actual_xyz_files: List[str] = []
        for symbol in symbols:
            actual_xyz_files.append(f"{symbol}.xyz")
    else:
        if len(symbols) != len(xyz_files):
            raise ValueError("symbols と xyz_files の長さが一致していません。")
        actual_xyz_files = list(xyz_files)

    multiplier: int = total_atom_count // ratio_sum
    structures: List[StructureSpec] = []

    for symbol, ratio, xyz_file in zip(symbols, ratios, actual_xyz_files):
        atom_count: int = ratio * multiplier
        write_single_atom_xyz(filename=xyz_file, element=symbol)
        structures.append(StructureSpec(xyz_file=xyz_file, number=atom_count))

    return MaterialRecipe(
        total_atom_count=total_atom_count,
        symbols=list(symbols),
        ratios=list(ratios),
        structures=structures,
    )
