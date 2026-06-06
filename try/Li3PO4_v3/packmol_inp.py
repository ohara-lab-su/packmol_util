#!/usr/bin/env python3
"""
Packmol の入力ファイルを構築するための共通クラスである。
"""

from typing import Dict, List, Optional


class PackmolInp:
    """
    Packmol の .inp ファイルを構築するための単純なクラスである。
    """

    def __init__(
        self,
        minimum_separation_distance: float,
        output_xyz: str,
        box_length: float,
        use_pbc: bool = False,
    ) -> None:
        self.minimum_separation_distance: float = minimum_separation_distance
        self.output_xyz: str = output_xyz
        self.box_length: float = box_length
        self.use_pbc: bool = use_pbc
        self.structure_blocks: List[Dict[str, object]] = []

    def add_structure(
        self,
        xyz_file: str,
        number: int,
        packing_radii_by_atom_index: Optional[Dict[int, float]] = None,
    ) -> None:
        """
        1つの分子または単原子テンプレートに対する structure ブロックを登録する。
        """
        block: Dict[str, object] = {
            "xyz": xyz_file,
            "number": number,
            "packing_radii_by_atom_index": packing_radii_by_atom_index,
        }
        self.structure_blocks.append(block)

    def write(
        self,
        inp_file: str,
    ) -> None:
        """
        .inp ファイルを書き出す。
        """
        box_length: float = self.box_length

        with open(inp_file, "w") as f:
            f.write(f"tolerance {self.minimum_separation_distance}\n")

            if self.use_pbc:
                f.write(
                    f"pbc {box_length:.6f} {box_length:.6f} {box_length:.6f}\n"
                )

            f.write("filetype xyz\n")
            f.write(f"output {self.output_xyz}\n\n")

            for structure_block in self.structure_blocks:
                xyz_file = str(structure_block["xyz"])
                number = int(structure_block["number"])
                packing_radii_by_atom_index = structure_block.get(
                    "packing_radii_by_atom_index"
                )

                f.write(f"structure {xyz_file}\n")
                f.write(f"  number {number}\n")
                f.write(
                    "  inside box "
                    "0.0 0.0 0.0  "
                    f"{box_length:.6f} {box_length:.6f} {box_length:.6f}\n"
                )

                if packing_radii_by_atom_index is not None:
                    if not isinstance(packing_radii_by_atom_index, dict):
                        raise TypeError(
                            "packing_radii_by_atom_index は dict で指定する。"
                        )

                    for atom_index in sorted(packing_radii_by_atom_index.keys()):
                        radius = packing_radii_by_atom_index[atom_index]
                        f.write(f"  atoms {atom_index}\n")
                        f.write(f"    radius {radius:.6f}\n")
                        f.write("  end atoms\n")

                f.write("end structure\n\n")
