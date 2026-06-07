#!/usr/bin/env python3
"""
Li3PO4 の Packmol 初期構造を作るサンプルである。

このスクリプトは、物質固有の処方箋を書く場所である。
共通モジュール側には Li3PO4 専用の値を置かない。
"""

import shutil

from packmol_util.builder import AmorphousBuilder
from packmol_util.model import write_single_atom_xyz, write_tetrahedral_unit_xyz


def main() -> None:
    """
    Li3PO4 の単原子 Li と PO4 分子ユニットを Packmol で混合配置する。
    """
    # ------------------------------------------------------------
    # Li3PO4 の物質固有条件を指定する。
    # セル内に入れる総原子数として total_atom_count = 512 を直接指定する。
    # 1 式単位 (Li3PO4) あたり合計 8 原子であるため、
    # 512 原数は 64 式単位分に相当する。
    # ratios=[3, 1, 4] により、Li、P、O の組成比を維持する。
    # ------------------------------------------------------------
    total_atom_count: int = 512
    number_density_A3: float = 0.0772877

    # ------------------------------------------------------------
    # PO4 ユニット内部の幾何を指定する。
    # p_o_distance は PO4 ユニット内の P-O 距離である。
    # o_o_distance は PO4 ユニット内の O-O 距離である。
    # 正四面体条件を満たすようにパラメータを選ぶ。
    # ------------------------------------------------------------
    p_o_distance: float = 1.30
    o_o_distance: float = 2.10

    # ------------------------------------------------------------
    # Packmol がテンプレート同士を配置するときの全体的な近接回避距離である。
    # ------------------------------------------------------------
    minimum_separation_distance: float = 1.8

    symbols = ["Li", "P", "O"]
    ratios = [3, 1, 4]

    # 2. テンプレートXYZの自動生成 (内部幾何)
    write_single_atom_xyz("Li.xyz", "Li")
    write_tetrahedral_unit_xyz(
        filename="PO4.xyz",
        center_element="P",
        vertex_element="O",
        # 中心原子—頂点原子の距離
        center_vertex_distance=p_o_distance,
        # 頂点原子—頂点原子の距離 (理想的な四面体では 2.123 くらい)
        vertex_vertex_distance=o_o_distance,
    )

    # 3. 汎用ビルダーを使って一撃で構築・実行・変換まで行う
    # （ボイラープレートコードをすべて高レベルAPIに隠蔽）
    # ユーザーが指定した総原子数 (512) をそのまま流し込む。
    builder = AmorphousBuilder(
        symbols=symbols,
        ratios=ratios,
        number_density=number_density_A3,  # 数密度指定
        total_atom_count=total_atom_count,  # 直接 512 を指定
        minimum_separation=minimum_separation_distance,
    )

    # 各テンプレートファイルと、1セルあたりに配置する個数を指定する。
    # 512 原子のとき、組成比 (3:1:4, 合計8) から自動計算される各元素の総数は
    # Li: 192個, P: 64個, O: 256個 となる。
    # PO4.xyz は「1個あたり1個のPと4個のO」を含むユニットなので、
    # 配置するユニット数（複製数）は P の数と同じ（512 * 1/8 = 64個）になる。
    # 同様に、Li.xyz は単原子なので Li の総数と同じ（512 * 3/8 = 192個）になる。
    #
    # 【重要】高レベルAPI (AmorphousBuilder) 側が内部で比率 (ratio_part) を用いて
    # 適切な個数を自動計算して追加するため、ここでは組成比のパーツ (3 や 1) をそのまま渡す。
    builder.add_template(
        "Li.xyz",
        ratio_part=3,
    )
    builder.add_template(
        "PO4.xyz",
        ratio_part=1,
        packing_radii={"P": 0.25, "O": 1.05},
    )

    builder.build(output_prefix="li3po4")
    shutil.copyfile("POSCAR", "POSCAR.vasp")


if __name__ == "__main__":
    main()
