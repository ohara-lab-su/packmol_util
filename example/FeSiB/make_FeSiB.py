#!/usr/bin/env python3
"""FeSiB アモルファス初期構造の作成スクリプト"""

import shutil

from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz


def main() -> None:
    symbols = ["Fe", "Si", "B"]
    ratios = [80, 9, 11]
    total_atom_count = 100

    # テンプレート生成
    for sym in symbols:
        write_single_atom_xyz(f"{sym}.xyz", sym)

    # ビルダーの実行
    builder = AmorphousBuilder(
        symbols=symbols,
        ratios=ratios,
        mass_density=7.0,  # 質量密度での指定
        total_atom_count=total_atom_count,
        minimum_separation=2.3,
    )

    # 単原子系はループで簡単に登録可能
    for sym, ratio in zip(symbols, ratios):
        builder.add_template(f"{sym}.xyz", number=ratio)

    builder.build(output_prefix="FeSiB")
    shutil.copyfile("POSCAR", "POSCAR.vasp")


if __name__ == "__main__":
    main()
