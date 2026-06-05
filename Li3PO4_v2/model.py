#!/usr/bin/env python3
"""
材料依存のテンプレート構造を準備する補助関数。
Packmol クラス本体へ材料専用処理を入れないために分離する。
"""

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class StructureSpec:
    """
    Packmol に渡す 1 つの structure 情報。
    """

    xyz_file: str
    number: int


@dataclass(frozen=True)
class MaterialRecipe:
    """
    1 つの材料系に対する Packmol 入力準備情報。
    """

    N_tot: int
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


def write_po4_xyz(
    filename: str,
    p_o_distance: float = 1.54,
) -> None:
    """
    正四面体 PO4 ユニットの XYZ テンプレートを書き出す。
    """
    scale: float = p_o_distance / math.sqrt(3.0)
    atoms: List[Tuple[str, float, float, float]] = [
        ("P", 0.0, 0.0, 0.0),
        ("O", scale, scale, scale),
        ("O", scale, -scale, -scale),
        ("O", -scale, scale, -scale),
        ("O", -scale, -scale, scale),
    ]
    write_xyz_template(
        filename=filename,
        atoms=atoms,
        comment="PO4 tetrahedral unit template",
    )


def prepare_fesib_recipe(
    N_tot: int,
    fe_xyz: str = "Fe.xyz",
    si_xyz: str = "Si.xyz",
    b_xyz: str = "B.xyz",
) -> MaterialRecipe:
    """
    FeSiB 用のテンプレートと個数を準備する。
    """
    if N_tot <= 0:
        raise ValueError("N_tot は正の整数である必要があります。")

    symbols: List[str] = ["Fe", "Si", "B"]
    ratios: List[int] = [80, 9, 11]

    ratio_sum: int = sum(ratios)
    if N_tot % ratio_sum != 0:
        raise ValueError(
            "N_tot は Fe80Si9B11 の比率合計 100 の整数倍である必要があります。"
        )

    multiplier: int = N_tot // ratio_sum

    fe_count: int = ratios[0] * multiplier
    si_count: int = ratios[1] * multiplier
    b_count: int = ratios[2] * multiplier

    write_single_atom_xyz(filename=fe_xyz, element="Fe")
    write_single_atom_xyz(filename=si_xyz, element="Si")
    write_single_atom_xyz(filename=b_xyz, element="B")

    structures: List[StructureSpec] = [
        StructureSpec(xyz_file=fe_xyz, number=fe_count),
        StructureSpec(xyz_file=si_xyz, number=si_count),
        StructureSpec(xyz_file=b_xyz, number=b_count),
    ]

    return MaterialRecipe(
        N_tot=N_tot,
        symbols=symbols,
        ratios=ratios,
        structures=structures,
    )


def prepare_li3po4_recipe(
    formula_unit_count: int,
    li_xyz: str = "Li.xyz",
    po4_xyz: str = "PO4.xyz",
    p_o_distance: float = 1.54,
) -> MaterialRecipe:
    """
    Li3PO4 用のテンプレートと個数を準備する。
    """
    if formula_unit_count <= 0:
        raise ValueError("formula_unit_count は正の整数である必要があります。")

    li_count: int = formula_unit_count * 3
    po4_count: int = formula_unit_count
    N_tot: int = formula_unit_count * 8
    symbols: List[str] = ["Li", "P", "O"]
    ratios: List[int] = [3, 1, 4]

    write_single_atom_xyz(filename=li_xyz, element="Li")
    write_po4_xyz(filename=po4_xyz, p_o_distance=p_o_distance)

    structures: List[StructureSpec] = [
        StructureSpec(xyz_file=li_xyz, number=li_count),
        StructureSpec(xyz_file=po4_xyz, number=po4_count),
    ]

    return MaterialRecipe(
        N_tot=N_tot,
        symbols=symbols,
        ratios=ratios,
        structures=structures,
    )
