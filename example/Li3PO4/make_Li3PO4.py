#!/usr/bin/env python3
"""
Li3PO4 の Packmol 初期構造を作るサンプルである。

このスクリプトは、物質固有の処方箋を書く場所である。
共通モジュール側には Li3PO4 専用の値を置かない。
"""

from packmol_util.model import StructureSpec
from packmol_util.model import make_material_recipe
from packmol_util.model import solve_packing_radii_from_pair_distances
from packmol_util.model import write_single_atom_xyz
from packmol_util.model import write_tetrahedral_unit_xyz

from packmol_util.packmol import Packmol
from packmol_util.packmol_inp import PackmolInp


def main() -> None:
    """
    Li3PO4 の単原子 Li と PO4 分子ユニットを Packmol で混合配置する。
    """
    # ------------------------------------------------------------
    # Li3PO4 の物質固有条件を指定する。
    # formula_unit_count は Li3PO4 の式単位数である。
    # 1 式単位あたり Li が 3 個、PO4 ユニットが 1 個である。
    # ------------------------------------------------------------
    formula_unit_count: int = 64
    number_density_A3: float = 0.0772877

    # ------------------------------------------------------------
    # PO4 ユニット内部の幾何を指定する。
    # p_o_distance は PO4 ユニット内の P-O 距離である。
    # o_o_distance は PO4 ユニット内の O-O 距離である。
    # 正四面体では P-O と O-O は独立ではないため、model.py 側で整合性を確認する。
    # ------------------------------------------------------------
    p_o_distance: float = 1.30
    o_o_distance: float = 2.10
    po4_distance_tolerance: float = 0.05

    # ------------------------------------------------------------
    # Packmol が Li 原子と PO4 ユニットを配置するときの全体的な近接回避距離である。
    # これは PO4 ユニット内部の P-O 距離や O-O 距離ではない。
    # ------------------------------------------------------------
    minimum_separation_distance: float = 1.8

    # ------------------------------------------------------------
    # PO4 ユニットを他の原子・他のユニットと配置するときに使う packing 半径である。
    # キーは元素記号であり、PO4.xyz 内の atom index ではない。
    # packmol_inp.py が PO4.xyz を読み、P -> atoms 1、O -> atoms 2 3 4 5 へ変換する。
    # これは分子内の P-O 距離や O-O 距離を作る指定ではない。
    # ------------------------------------------------------------
    # po4_packing_radii_by_atom_symbol = {
    #     "P": 0.25,
    #     "O": 1.05,
    # }

    # radii + tolerance から擬似的に atom <--> atom 距離を作る
    minimum_distances_by_pair = {
        ("Li", "Li"): 1.7,
        ("Li", "P"): 2.0,
        ("Li", "O"): 1.55,
        ("P", "P"): 2.6,
        ("P", "O"): 1.3,
        ("O", "O"): 2.1,
    }

    # ------------------------------------------------------------
    # 入出力ファイル名と Packmol 実行コマンドを指定する。
    # Li.xyz と PO4.xyz は、このスクリプトが作る Packmol 用テンプレートである。
    # ------------------------------------------------------------
    li_xyz: str = "Li.xyz"
    po4_xyz: str = "PO4.xyz"
    output_xyz: str = "li3po4_packmol.xyz"
    input_file: str = "packmol.inp"
    output_log: str = "packmol.log"
    poscar_file: str = "POSCAR"
    vasp_file: str = "POSCAR.vasp"
    packmol_bin: str = "packmol"

    # ------------------------------------------------------------
    # 最終構造の元素順と組成比である。
    # POSCAR 変換時の元素順にも使う。
    # ------------------------------------------------------------
    symbols = ["Li", "P", "O"]
    ratios = [3, 1, 4]

    # ------------------------------------------------------------
    # Packmol に配置させるテンプレート数を決める。
    # Li は単原子テンプレートとして 3 * formula_unit_count 個配置する。
    # PO4 は分子ユニットテンプレートとして formula_unit_count 個配置する。
    # ------------------------------------------------------------
    li_count: int = formula_unit_count * 3
    po4_count: int = formula_unit_count

    packmol = Packmol(
        input_file=input_file,
        output_xyz=output_xyz,
        output_log=output_log,
        packmol_bin=packmol_bin,
    )

    # ------------------------------------------------------------
    # Packmol に渡すテンプレート座標を作る。
    # Li.xyz は Li 原子 1 個だけを含む単原子テンプレートである。
    # PO4.xyz は P 1 個と O 4 個からなる 1 個の PO4 ユニットである。
    # ------------------------------------------------------------
    write_single_atom_xyz(filename=li_xyz, element="Li")
    write_tetrahedral_unit_xyz(
        filename=po4_xyz,
        center_element="P",
        vertex_element="O",
        center_vertex_distance=p_o_distance,
        vertex_vertex_distance=o_o_distance,
        distance_tolerance=po4_distance_tolerance,
    )

    # ------------------------------------------------------------
    # Packmol に渡す structure の処方箋を作る。
    # StructureSpec 1 個が、Packmol 入力の structure ... end structure 1 ブロックになる。
    # Li.xyz の StructureSpec は Li 原子を li_count 個配置する指定である。
    # PO4.xyz の StructureSpec は PO4 ユニットを po4_count 個配置する指定である。
    # ------------------------------------------------------------
    # recipe = make_material_recipe(
    #     symbols=symbols,
    #     ratios=ratios,
    #     structures=[
    #         StructureSpec(xyz_file=li_xyz, number=li_count),
    #         StructureSpec(
    #             xyz_file=po4_xyz,
    #             number=po4_count,
    #             packing_radii_by_atom_symbol=po4_packing_radii_by_atom_symbol,
    #         ),
    #     ],
    # )
    packing_radii_by_atom_symbol = solve_packing_radii_from_pair_distances(
        symbols=["Li", "P", "O"],
        minimum_distances_by_pair=minimum_distances_by_pair,
        distance_tolerance=0.05,
    )

    recipe = make_material_recipe(
        symbols=symbols,
        ratios=ratios,
        structures=[
            StructureSpec(
                xyz_file=li_xyz,
                number=li_count,
                packing_radii_by_atom_symbol={"Li": packing_radii_by_atom_symbol["Li"]},
            ),
            StructureSpec(
                xyz_file=po4_xyz,
                number=po4_count,
                packing_radii_by_atom_symbol={
                    "P": packing_radii_by_atom_symbol["P"],
                    "O": packing_radii_by_atom_symbol["O"],
                },
            ),
        ],
    )

    # ------------------------------------------------------------
    # 数密度と総原子数から立方体セルの一辺長を決める。
    # PO4 は 1 structure で 5 原子を含むため、recipe.total_atom_count は
    # Li 個数 + PO4 個数 * 5 で計算される。
    # ------------------------------------------------------------
    box_length: float = packmol.cell_length_from_number_density(
        total_atom_count=recipe.total_atom_count,
        number_density_A3=number_density_A3,
    )

    # ------------------------------------------------------------
    # Packmol 入力ファイルを構築する。
    # builder.add_structure() により、recipe 内の各 StructureSpec を Packmol の
    # structure ブロックとして登録する。
    # ------------------------------------------------------------
    builder = PackmolInp(
        minimum_separation_distance=minimum_separation_distance,
        output_xyz=output_xyz,
        box_length=box_length,
        use_pbc=True,
    )
    for structure in recipe.structures:
        builder.add_structure(
            xyz_file=structure.xyz_file,
            number=structure.number,
            packing_radii_by_atom_symbol=structure.packing_radii_by_atom_symbol,
        )
    builder.write(input_file)

    # ------------------------------------------------------------
    # Packmol を実行し、生成された XYZ を POSCAR に変換する。
    # ------------------------------------------------------------
    packmol.run_packmol(
        input_file=input_file,
        output_log=output_log,
        packmol_bin=packmol_bin,
    )

    packmol.xyz_to_poscar(
        xyz_file=output_xyz,
        poscar_file=poscar_file,
        packmol_inp=input_file,
        comment="Li3PO4 amorphous initial model generated by Packmol",
        elements=recipe.symbols,
    )
    packmol.xyz_to_poscar(
        xyz_file=output_xyz,
        poscar_file=vasp_file,
        packmol_inp=input_file,
        comment="Li3PO4 amorphous initial model generated by Packmol",
        elements=recipe.symbols,
    )


if __name__ == "__main__":
    main()
