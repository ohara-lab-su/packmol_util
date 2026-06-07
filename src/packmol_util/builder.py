#!/usr/bin/env python3
"""
packmol_util/builder.py

詳細なファイルのバケツリレーを隠蔽し、
数行でアモルファス構造を作成するための高レベル統合モジュール。

以下の 3 点を外部入力の基準とする：
    1. 化学量論比（整数比）
    2. 密度 [g/cm^3] または 数密度 [1/Å^3] のいずれか一方
    3. セル内の総原子数 total_atom_count

【重要】指定した total_atom_count が ratios の合計で割り切れない（組成比を維持できない）場合、
プログラムが破綻するのを防ぐため、指定された原子数に最も近い「割り切れる総原子数」へ自動補正を行う。
内部で計算された全体のスケール倍率（multiplier）を外部に公開（プロパティ化）することで、
利用側のスクリプトがユニット構成単位でのパッキング個数を一元管理できるように設計されている。
"""

from typing import Dict, List, Optional
from packmol_util.packmol import Packmol
from packmol_util.packmol_inp import PackmolInp


class AmorphousBuilder:

    def __init__(
        self,
        symbols: List[str],
        ratios: List[int],
        total_atom_count: int,  # 希望するベースの総原子数
        minimum_separation: float,
        mass_density: Optional[float] = None,
        number_density: Optional[float] = None,
        packmol_bin: str = "packmol",
    ):
        if len(symbols) != len(ratios):
            raise ValueError("symbols と ratios の長さが一致していません。")

        if total_atom_count <= 0:
            raise ValueError("total_atom_count は正の整数である必要があります。")

        self.symbols = symbols
        self.ratios = ratios
        self.minimum_separation = minimum_separation
        self.packmol_bin = packmol_bin

        # --- 【自動補正ロジック】指定できない比率（割り切れない数）のときの自動補正 ---
        ratio_sum = sum(ratios)
        if total_atom_count % ratio_sum != 0:
            # 最も近い整数倍（倍率）を計算
            multiplier = round(total_atom_count / ratio_sum)
            if multiplier < 1:
                multiplier = 1
            adjusted_atom_count = ratio_sum * multiplier
            print(
                f"[Warning] 指定された総原子数 {total_atom_count} は組成比の合計 {ratio_sum} で割り切れません。"
            )
            print(
                f"          組成比を維持するため、総原子数を {adjusted_atom_count} (倍率: {multiplier}) に自動調整しました。"
            )
            self.total_atom_count = adjusted_atom_count
            self._multiplier = multiplier
        else:
            self.total_atom_count = total_atom_count
            self._multiplier = total_atom_count // ratio_sum

        # 密度の計算とセル一辺の長さ決定
        self.packmol_runner = Packmol()
        if number_density is not None:
            self.box_length = self.packmol_runner.cell_length_from_number_density(
                self.total_atom_count, number_density
            )
        elif mass_density is not None:
            n_density = self.packmol_runner.number_density_from_mass_density(
                symbols, ratios, mass_density
            )
            self.box_length = self.packmol_runner.cell_length_from_number_density(
                self.total_atom_count, n_density
            )
        else:
            raise ValueError(
                "mass_density または number_density のどちらかを指定してください。"
            )

        self.templates: List[dict] = []

    @property
    def multiplier(self) -> int:
        """
        全体の化学量論比に対するセルのスケール倍率を返す。
        利用側のスクリプトは、この倍率をユニットの1式あたり構成比に乗算することで、
        Packmol に引き渡すべき実際の複製個数（number）を算出する。
        """
        return self._multiplier

    def add_template(
        self,
        xyz_file: str,
        number: int,  # そのテンプレートを Packmol がセル内に何個配置するかを表す実際の複製個数
        packing_radii: Optional[Dict[str, float]] = None,
    ):
        """
        Packmol の 1 つの structure ブロックに対応するテンプレート情報を登録する。

        引数の説明：
            xyz_file: Packmol に渡す単原子または分子ユニットテンプレートの座標ファイル名 (.xyz)
            number: そのテンプレートを何個複製して配置するかを指定する [int]
            packing_radii: Packmol 配置時に使う元素記号別の排除半径の辞書（任意）。
                           分子ユニット内部の結合距離や形状を作る値ではない。
        """
        # builder では、テンプレートをまだ Packmol 入力へ変換しない。
        # ここでは「どの XYZ テンプレートを何個置くか」と、必要なら配置用 packing 半径だけを保存する。
        # 具体的な structure ... end structure への変換は build() 内の PackmolInp が担当する。
        self.templates.append(
            {
                "xyz": xyz_file,
                "number": number,
                "radii": packing_radii,
            }
        )

    def build(self, output_prefix: str):
        # output_prefix は、一連の生成ファイル名の接頭辞として使う。
        # 例: output_prefix="Li3PO4" の場合、Li3PO4_packmol.inp / Li3PO4_packmol.xyz / Li3PO4_packmol.log を作る。
        input_file = f"{output_prefix}_packmol.inp"
        output_xyz = f"{output_prefix}_packmol.xyz"
        output_log = f"{output_prefix}_packmol.log"
        poscar_file = "POSCAR"
        vasp_file = "POSCAR.vasp"

        # 1. PackmolInp を構築する。
        # AmorphousBuilder が持つ情報は Python 側の抽象表現である。
        # PackmolInp は、それを Packmol の .inp 文法へ落とす役割を持つ。
        inp_builder = PackmolInp(
            minimum_separation_distance=self.minimum_separation,
            output_xyz=output_xyz,
            box_length=self.box_length,
            use_pbc=True,
        )
        for t in self.templates:
            # 1 件の template は Packmol 入力の 1 つの structure ブロックに対応する。
            # 単原子テンプレートでも PO4 のような分子ユニットでも、ここでは同じ登録処理を通す。
            inp_builder.add_structure(
                xyz_file=t["xyz"],
                number=t["number"],
                packing_radii_by_atom_symbol=t["radii"],
            )
        # 登録した template 群を Packmol 入力ファイルとして書き出す。
        inp_builder.write(input_file)

        # 2. Packmol を実行し、生成された XYZ を POSCAR に変換する。
        self.packmol_runner.run_packmol(
            input_file=input_file,
            output_log=output_log,
            packmol_bin=self.packmol_bin,
        )

        # Packmol 出力は Cartesian 座標なので、VASP POSCAR 用に Direct 座標へ変換する。
        self.packmol_runner.xyz_to_poscar(
            xyz_file=output_xyz,
            poscar_file=poscar_file,
            packmol_inp=input_file,
            comment=f"{output_prefix} amorphous initial model generated by Packmol (Total Atoms: {self.total_atom_count})",
            elements=self.symbols,
        )

        # 外部ツール連携用に vasp.xyz（あるいは POSCAR.vasp）も同様に出力する。
        self.packmol_runner.xyz_to_poscar(
            xyz_file=output_xyz,
            poscar_file=vasp_file,
            packmol_inp=input_file,
            comment=f"{output_prefix} amorphous initial model vasp format",
            elements=self.symbols,
        )


#
