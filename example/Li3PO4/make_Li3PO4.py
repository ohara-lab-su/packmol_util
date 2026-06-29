#!/usr/bin/env python3
"""
Li3PO4 の Packmol 初期構造を作るサンプルである。

このスクリプトは、単原子 Li と PO4 分子ユニットを混合配置する【分子ユニット混在系】の例である。
物質固有の処方箋として、登録すべき「ユニット（塊）」の構造と比率をトップレベルで明確に区別して整理する。

共通モジュール（builder.py など）側には Li3PO4 専用の値を置かず、
このスクリプト側で、物質固有の原子数、密度、分子内距離、packing 半径を与える。

【ユニット構造の明示による整理】
Li3PO4 では、構成要素が「Li単原子ユニット」と「PO4分子ユニット」という、トポロジーの異なる2大ユニットに分かれる。
PO4分子の内部にはあらかじめ P:1, O:4 が共有結合を保護された塊として内包されているため、
1式単位（Formula Unit）あたり、Liユニットを「3個」、PO4ユニットを「1個」配置すれば、
全体の化学量論比 (3:1:4, 合計8) と完全に一致する。この関係性をデータ構造として明確に峻別する。
"""

import shutil

from packmol_util.builder import AmorphousBuilder
from packmol_util.model import (
    make_tetrahedral_unit_fnc_spec_from_ranges,
    write_single_atom_xyz,
    write_tetrahedral_unit_xyz,
)


def main() -> None:
    """
    Li3PO4 の単原子 Li と PO4 分子ユニットを Packmol で混合配置する。
    """
    # ------------------------------------------------------------
    # Li3PO4 の物質固有条件を指定する。
    # セル内に入れる総原子数として total_atom_count = 512 を直接指定する。
    # 1 式単位 (Li3PO4) あたり合計 8 原子であるため、
    # 512 原子は 64 式単位分に相当する（multiplier = 64）。
    # ratios=[3, 1, 4] により、Li、P、O の組成比を維持する。
    # ------------------------------------------------------------
    total_atom_count: int = 512
    number_density_A3: float = 0.0772877

    symbols = ["Li", "P", "O"]
    ratios = [3, 1, 4]

    # ------------------------------------------------------------
    # 【ユニットベースのデータ定義】
    # この系を構成する「Li」と「PO4」の2大ユニットを定義する。
    #
    # xyz は、Packmol に渡す 1 個のユニットテンプレートである。
    # Li.xyz は 1 原子だけを含む単原子ユニットであり、PO4.xyz は P 原子 1 個と O 原子 4 個を含む
    # 分子ユニットである。PO4.xyz の内部幾何は、後段の write_tetrahedral_unit_xyz() で作る。
    #
    # unit_ratio は、1 式単位 Li3PO4 あたりに配置するユニット数である。
    # Li は 3 個、PO4 は 1 個であり、PO4 ユニット 1 個の内部に P:1, O:4 が含まれる。
    #
    # radii は Packmol の配置時に使う元素記号別の packing 半径である。
    # これは PO4 内部の P-O 距離や O-O 距離を作る値ではない。
    # PO4 内部距離は FNC の rmin/rmax から代表距離を派生させ、XYZ 座標として固定する。
    # radii は、作成済みの PO4 ユニットや Li 原子をセル内に配置するとき、他ユニット・他原子との
    # 重なりを避けるための排除半径である。
    # ------------------------------------------------------------
    li3po4_units = {
        "Li": {"xyz": "Li.xyz", "unit_ratio": 3, "radii": None},
        "PO4": {
            "xyz": "PO4.xyz",
            "unit_ratio": 1,
            "radii": {"P": 0.25, "O": 1.05},
        },
    }

    # ------------------------------------------------------------
    # PO4 ユニット内部の距離条件を FNC 側の rmin/rmax として指定する。
    # Packmol 用の PO4.xyz 代表距離は、この FNC 範囲の中央値からモジュール側で派生させる。
    # したがって、Packmol 用距離と FNC 用距離範囲を二重管理しない。
    # ------------------------------------------------------------
    po4_fnc_spec = make_tetrahedral_unit_fnc_spec_from_ranges(
        center_vertex_range=(1.25, 1.35),  # P-O rmin/rmax [Å]
        vertex_vertex_range=(2.05, 2.20),  # O-O rmin/rmax [Å]
    )

    # Packmol 配置時の全体的な近接回避距離である。
    # この値は PO4 内部の P-O 距離や O-O 距離ではない。
    # PO4 内部の幾何は、上で指定した FNC rmin/rmax から派生した代表距離で決める。
    # minimum_separation_distance は、Li ユニットや PO4 ユニット同士を箱の中に置くときの全体条件である。
    minimum_separation_distance: float = 1.8

    # ============================================================
    # 2. ユニットテンプレート（XYZ）の自動生成 (内部幾何)
    # ============================================================
    # 単原子の最小ユニットと、5原子からなる正四面体分子ユニットをそれぞれ個別に作成
    write_single_atom_xyz("Li.xyz", "Li")
    write_tetrahedral_unit_xyz(
        filename="PO4.xyz",
        center_element="P",
        vertex_element="O",
        # 中心原子—頂点原子の距離 [Å]
        center_vertex_distance=po4_fnc_spec.center_vertex_distance,
        # 頂点原子—頂点原子の距離 [Å] (理想的な四面体では 2.123 くらい)
        vertex_vertex_distance=po4_fnc_spec.vertex_vertex_distance,
    )

    # ============================================================
    # 3. 汎用ビルダーの実行 (既存 of AmorphousBuilder をそのまま使用)
    # ============================================================
    # 指定された総原子数 (512) と、数密度 [1/Å^3] からセル長を決定。
    # 各元素の自動計算される総数は Li: 192個, P: 64個, O: 256個 となる。
    builder = AmorphousBuilder(
        symbols=symbols,
        ratios=ratios,
        number_density=number_density_A3,  # 数密度 [1/Å^3] 指定
        total_atom_count=total_atom_count,  # 総原子数 512 を直接指定
        minimum_separation=minimum_separation_distance,  # ユニット間の近接回避距離
    )

    # ============================================================
    # 4. 整理されたユニットをビルダーに引き渡す（共通ループ処理）
    # ============================================================
    # add_template メソッドの引数の仕様（xyz_file, number, packing_radii）に従い、
    # 1式単位あたりのユニット数 (unit_ratio) に、ビルダーが内部で保持する
    # 全体のスケール倍率 (builder.multiplier = 64) を乗算して、正確な配置個数 (number) を算出する。
    #
    # メソッド引数の説明：
    #   xyz_file: Packmol に渡す単原子または分子ユニットテンプレートの座標ファイル名 (.xyz)
    #   number: そのテンプレートを Packmol がセル内に何個配置するかを表す実際の複製個数
    #           (Li は 3 * 64 = 192 個、PO4 は 1 * 64 = 64 個となる)
    #   packing_radii: Packmol 配置時に使う元素記号別の排除半径である。
    #                  PO4 の内部構造を作る値ではない。
    #                  P-O / O-O の分子内距離は write_tetrahedral_unit_xyz() で生成済みの PO4.xyz に含まれる。
    # ============================================================
    for unit_name, cfg in li3po4_units.items():
        calculated_number = cfg["unit_ratio"] * builder.multiplier
        builder.add_template(
            xyz_file=cfg["xyz"],
            number=calculated_number,  # 同期された引数名 'number' で配置個数を引き渡す
            packing_radii=cfg["radii"],
            fnc_pairs_in_template=(
                po4_fnc_spec.fnc_pairs_in_template if unit_name == "PO4" else None
            ),
            fnc_distance_ranges=(
                po4_fnc_spec.fnc_distance_ranges if unit_name == "PO4" else None
            ),
            # --------------------------------------------------------
            # Packmol 用 PO4.xyz の形状は変更しない。
            #
            # ここでは「Packmol 後に生成する .fnc」に
            # 出力する constraint type を選択するだけである。
            #
            # None
            #     FNC に全 constraint type を出力する（デフォルト）。
            #
            # [1]
            #     constraint type 1 のみ出力する。
            #     Li3PO4 のサンプルでは
            #         type 1 : P-O
            #         type 2 : O-O
            #     として作成しているため、
            #     O-O は FNC に出力されず、
            #     初期 PO4 形状だけ保持したまま
            #     RMC 中は O-O を拘束しない。
            #
            # [2]
            #     O-O のみ拘束する例。
            #
            # [1, 2]
            #     P-O, O-O の両方を拘束する。
            #     （None と同じ結果）
            # --------------------------------------------------------
            fnc_output_constraint_types=([1] if unit_name == "PO4" else None),
        )

    # 5. 構造構築と出力
    builder.build(output_prefix="Li3PO4", fnc_file="Li3PO4.fnc")
    shutil.copyfile("POSCAR", "POSCAR.vasp")


if __name__ == "__main__":
    main()
