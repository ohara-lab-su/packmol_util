#!/usr/bin/env python3
"""
FeSiB の Packmol 初期構造を作るサンプルである。

このスクリプトは、分子ユニットを使わない単原子混合系の例である。
Fe.xyz、Si.xyz、B.xyz という 1 原子テンプレートを作り、それぞれを指定個数だけ
Packmol に配置させる。
"""

import shutil

from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz


def main() -> None:
    """
    Fe80Si9B11 の単原子混合初期構造を Packmol で作る。
    """
    # ------------------------------------------------------------
    # FeSiB の物質固有条件を指定する。
    # total_atom_count はセル内に入れる総原子数である。
    # ratios=[80, 9, 11] により、Fe 80 個、Si 9 個、B 11 個を配置する。
    # ------------------------------------------------------------
    total_atom_count: int = 100
    mass_density_g_cm3: float = 7.0

    symbols = ["Fe", "Si", "B"]
    ratios = [80, 9, 11]
    xyz_files = ["Fe.xyz", "Si.xyz", "B.xyz"]

    # ------------------------------------------------------------
    # Packmol が単原子テンプレート同士を配置するときの全体的な近接回避距離である。
    # FeSiB では分子ユニットを作らないため、PO4 のような分子内距離指定は存在しない。
    # ------------------------------------------------------------
    minimum_separation_distance: float = 2.3

    # テンプレート生成
    for sym in symbols:
        write_single_atom_xyz(f"{sym}.xyz", sym)

    # ビルダーの実行
    builder = AmorphousBuilder(
        symbols=symbols,
        ratios=ratios,
        mass_density=mass_density_g_cm3,  # 質量密度での指定
        total_atom_count=total_atom_count,
        minimum_separation=minimum_separation_distance,
    )

    # 単原子系はループで簡単に登録可能
    for sym, ratio in zip(symbols, ratios):
        builder.add_template(f"{sym}.xyz", number=ratio)

    builder.build(output_prefix="FeSiB")
    shutil.copyfile("POSCAR", "POSCAR.vasp")


if __name__ == "__main__":
    main()
