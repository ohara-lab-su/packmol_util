#!/usr/bin/env python3
"""
Packmol の入力ファイルを構築するための補助クラスである。
"""

from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence


class PackmolInp:
    """
    Packmol の .inp ファイルを構築するクラスである。

    Global option と structure block を分けて保持する。
    単原子だけでなく、PO4 のような複数原子ユニットも同じ structure として扱う。
    """

    def __init__(
        self,
        tolerance: float,
        output_xyz: str,
        box_length: float,
        filetype: str = "xyz",
        seed: Optional[int] = None,
        use_pbc: bool = True,
        precision: Optional[float] = None,
        nloop: Optional[int] = None,
        maxit: Optional[int] = None,
        random_initial_point: bool = False,
        move_bad_random: bool = False,
    ) -> None:
        """
        Args:
            tolerance: Packmol の距離 tolerance である。
            output_xyz: Packmol の出力 XYZ ファイル名である。
            box_length: 立方体セルの一辺長である。
            filetype: Packmol 入出力のファイル形式である。
            seed: 乱数シードである。None の場合は seed 行を書かない。
            use_pbc: pbc 行を書くかどうかを指定する。
            precision: Packmol の収束判定精度である。
            nloop: Packmol の最適化ループ数である。
            maxit: GENCAN の反復回数である。
            random_initial_point: randominitialpoint を使うかどうかである。
            move_bad_random: movebadrandom を使うかどうかである。
        """
        self.tolerance: float = tolerance
        self.output_xyz: str = output_xyz
        self.box_length: float = box_length
        self.filetype: str = filetype
        self.seed: Optional[int] = seed
        self.use_pbc: bool = use_pbc
        self.precision: Optional[float] = precision
        self.nloop: Optional[int] = nloop
        self.maxit: Optional[int] = maxit
        self.random_initial_point: bool = random_initial_point
        self.move_bad_random: bool = move_bad_random
        self.structure_blocks: List[Dict[str, object]] = []

    def add_structure(
        self,
        xyz_file: str,
        number: int,
        inside_box: Optional[Sequence[float]] = None,
        radius: Optional[float] = None,
        constraints: Optional[Sequence[str]] = None,
    ) -> None:
        """
        structure ブロックを追加する。

        Args:
            xyz_file: 1個の構造テンプレートを含む XYZ ファイルである。
            number: 複製数である。
            inside_box: inside box の 6 成分である。None の場合はセル全体を使う。
            radius: structure 全体に与える Packmol radius である。
            constraints: structure ブロックへそのまま追加する制約行である。
        """
        if number <= 0:
            raise ValueError("number は正の整数である必要がある。")

        block: Dict[str, object] = {}
        block["xyz_file"] = xyz_file
        block["number"] = number
        block["inside_box"] = inside_box
        block["radius"] = radius

        if constraints is None:
            block["constraints"] = []
        else:
            block["constraints"] = list(constraints)

        self.structure_blocks.append(block)

    def write(
        self,
        inp_file: str,
    ) -> None:
        """
        Packmol 入力ファイルを書き出す。

        Args:
            inp_file: 書き出す Packmol 入力ファイル名である。
        """
        cell_max: float = self.box_length

        with open(inp_file, "w", encoding="utf-8") as output_file:
            output_file.write(f"tolerance {self.tolerance:.6f}\n")

            if self.use_pbc:
                output_file.write(f"pbc {cell_max:.6f} {cell_max:.6f} {cell_max:.6f}\n")

            output_file.write(f"filetype {self.filetype}\n")
            output_file.write(f"output {self.output_xyz}\n")

            if self.seed is not None:
                output_file.write(f"seed {self.seed}\n")

            if self.precision is not None:
                output_file.write(f"precision {self.precision:.6f}\n")

            if self.nloop is not None:
                output_file.write(f"nloop {self.nloop}\n")

            if self.maxit is not None:
                output_file.write(f"maxit {self.maxit}\n")

            if self.random_initial_point:
                output_file.write("randominitialpoint\n")

            if self.move_bad_random:
                output_file.write("movebadrandom\n")

            output_file.write("\n")

            for structure_block in self.structure_blocks:
                xyz_file: str = str(structure_block["xyz_file"])
                number: int = int(structure_block["number"])
                inside_box_object = structure_block["inside_box"]
                radius_object = structure_block["radius"]
                constraints_object = structure_block["constraints"]

                output_file.write(f"structure {xyz_file}\n")
                output_file.write(f"  number {number}\n")

                if inside_box_object is None:
                    output_file.write(
                        "  inside box "
                        f"0.000000 0.000000 0.000000 "
                        f"{cell_max:.6f} {cell_max:.6f} {cell_max:.6f}\n"
                    )
                else:
                    inside_box_values: List[float] = [
                        float(value) for value in inside_box_object
                    ]

                    if len(inside_box_values) != 6:
                        raise ValueError("inside_box は 6 成分である必要がある。")

                    output_file.write(
                        "  inside box "
                        f"{inside_box_values[0]:.6f} "
                        f"{inside_box_values[1]:.6f} "
                        f"{inside_box_values[2]:.6f} "
                        f"{inside_box_values[3]:.6f} "
                        f"{inside_box_values[4]:.6f} "
                        f"{inside_box_values[5]:.6f}\n"
                    )

                if radius_object is not None:
                    radius_value: float = float(radius_object)
                    output_file.write(f"  radius {radius_value:.6f}\n")

                constraints: List[str] = [str(value) for value in constraints_object]

                for constraint in constraints:
                    output_file.write(f"  {constraint}\n")

                output_file.write("end structure\n\n")
