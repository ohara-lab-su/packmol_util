#!/usr/bin/env python
import math
from typing import Dict, List, Optional, Sequence, Tuple


def write_xyz_template(
    filename: str,
    atoms: Sequence[Tuple[str, float, float, float]],
    comment: str = "template",
) -> None:
    """
    任意のテンプレート構造を XYZ として書き出す。
    材料固有の分子・多原子ユニット生成はクラス外で扱う。
    """
    with open(filename, "w") as f:
        f.write(f"{len(atoms)}\n")
        f.write(f"{comment}\n")
        for symbol, x_value, y_value, z_value in atoms:
            f.write(f"{symbol}  {x_value:.10f}  {y_value:.10f}  {z_value:.10f}\n")


def write_po4_xyz(
    filename: str,
    p_o_distance: float = 1.54,
) -> None:
    """
    正四面体 PO4 ユニットの XYZ テンプレートを書き出す。
    Li3PO4 専用処理だが、Packmol クラスには入れない。
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
