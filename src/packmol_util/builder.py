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

        ratio_sum: int = sum(ratios)
        if ratio_sum <= 0:
            raise ValueError("ratios の合計は正の整数である必要があります。")

        self.symbols = symbols
        self.ratios = ratios
        self.minimum_separation = minimum_separation
        self.packmol_bin = packmol_bin

        # -------------------------------------------------------------------------
        # 原子数フィッティングロジック
        # 指定した total_atom_count が組成比の合計で割り切れない場合、指定可能な最も近い数に自動調整する。
        # -------------------------------------------------------------------------
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
            self.multiplier = multiplier
        else:
            self.total_atom_count = total_atom_count
            self.multiplier = total_atom_count // ratio_sum

        # -------------------------------------------------------------------------
        # 密度からセル一辺長 L を逆算する (Packmol クラスの機能を活用)
        # -------------------------------------------------------------------------
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

        # 登録するテンプレート情報を保持するリスト
        self.templates: List[dict] = []

    def add_template(
        self,
        xyz_file: str,
        number: int,
        packing_radii: Optional[Dict[str, float]] = None,
    ):
        """配置するXYZテンプレートファイルと個数、個別の exclusion radius を手動で登録する"""
        self.templates.append(
            {"xyz": xyz_file, "number": number, "radii": packing_radii}
        )

    def add_template_by_ratio(
        self,
        xyz_file: str,
        ratio_part: int,
        packing_radii: Optional[Dict[str, float]] = None,
    ):
        """組成比の一部（1式単位あたりの数）から、自動フィッティングされた個数を算出して登録する"""
        calculated_number = ratio_part * self.multiplier
        self.templates.append(
            {"xyz": xyz_file, "number": calculated_number, "radii": packing_radii}
        )

    def build(self, output_prefix: str):
        """
        Packmol 入力ファイルの構築、実行、および生成された XYZ から POSCAR / vasp.xyz への変換を一括で行う。
        """
        input_file = f"{output_prefix}_packmol.inp"
        output_xyz = f"{output_prefix}_packmol.xyz"
        output_log = f"{output_prefix}_packmol.log"
        poscar_file = "POSCAR"
        vasp_file = "vasp.xyz"

        # ------------------------------------------------------------
        # Packmol 入力ファイルを構築する。
        # builder.add_structure() により、登録された各テンプレート情報を
        # Packmol の structure ブロックとして登録する。
        # ------------------------------------------------------------
        inp_builder = PackmolInp(
            minimum_separation_distance=self.minimum_separation,
            output_xyz=output_xyz,
            box_length=self.box_length,
            use_pbc=True,
        )
        for t in self.templates:
            inp_builder.add_structure(
                xyz_file=t["xyz"],
                number=t["number"],
                packing_radii_by_atom_symbol=t["radii"],
            )
        inp_builder.write(input_file)

        # ------------------------------------------------------------
        # Packmol を実行し、生成された XYZ を POSCAR に変換する。
        # ------------------------------------------------------------
        self.packmol_runner.run_packmol(
            input_file=input_file,
            output_log=output_log,
            packmol_bin=self.packmol_bin,
        )

        # Packmol 出力は Cartesian 座標なので、VASP POSCAR 用に Direct 座標へ変換する。
        # 元素順序は指定された symbols に従う。
        self.packmol_runner.xyz_to_poscar(
            xyz_file=output_xyz,
            poscar_file=poscar_file,
            packmol_inp=input_file,
            comment=f"{output_prefix} amorphous initial model generated by Packmol (Total Atoms: {self.total_atom_count})",
            elements=self.symbols,
        )

        # 外部ツール連携用に vasp.xyz も同様に出力する。
        self.packmol_runner.xyz_to_poscar(
            xyz_file=output_xyz,
            poscar_file=vasp_file,
            packmol_inp=input_file,
            comment=f"{output_prefix} amorphous initial model vasp format",
            elements=self.symbols,
        )

        print(
            f"[Success] 構造作成が完了しました: {poscar_file} (最終総原子数: {self.total_atom_count}, セル長: {self.box_length:.5f} Å)"
        )
