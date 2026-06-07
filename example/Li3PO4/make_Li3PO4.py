#!/usr/bin/env python3
"""Li3PO4 アモルファス初期構造の作成スクリプ"""

import shutil
from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_tetrahedral_unit_xyz, write_single_atom_xyz


def main() -> None:
    # 1. 物質固有の構成・条件を定義
    formula_unit_count = 64
    symbols = ["Li", "P", "O"]
    ratios = [3, 1, 4]

    # 2. テンプレートXYZの自動生成 (内部幾何)
    write_single_atom_xyz("Li.xyz", "Li")
    write_tetrahedral_unit_xyz(
        filename="PO4.xyz",
        center_element="P",
        vertex_element="O",
        center_vertex_distance=1.30,
        vertex_vertex_distance=2.10,
    )

    # 3. 汎用ビルダーを使って一撃で構築・実行・変換まで行う
    # （ボイラープレートコードをすべて高レベルAPIに隠蔽）
    builder = AmorphousBuilder(
        symbols=symbols,
        ratios=ratios,
        number_density=0.0772877,  # 数密度指定 (mass_density=7.0 のように質量密度も選べるようにする)
        total_atom_count=formula_unit_count * sum(ratios),  # 64 * 8 = 512
        minimum_separation=1.8,
    )

    # 各テンプレートファイルと、1セルあたりの配置個数を登録
    builder.add_template("Li.xyz", number=formula_unit_count * 3)
    builder.add_template(
        "PO4.xyz", number=formula_unit_count, packing_radii={"P": 0.25, "O": 1.05}
    )

    # 実行 (packmol.inpの書き出し、Packmol実行、POSCAR出力を一括で行う)
    builder.build(output_prefix="Li3PO4")
    shutil.copyfile("POSCAR", "POSCAR.vasp")


if __name__ == "__main__":
    main()
