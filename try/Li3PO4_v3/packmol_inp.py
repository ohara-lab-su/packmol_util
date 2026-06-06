#!/usr/bin/env python3
"""
K.NAKADA, kengo.nakada@gmail.com
"""

from typing import Dict, List, Optional


class PackmolInp:
    """
    Packmol の .inp ファイルを構築するための単純なクラス。

    builder = PackmolInp(
        tolerance=2.3,
        output_xyz="result.xyz",
        box_length=L)

    builder.add_structure("Fe.xyz", N_Fe)
    builder.add_structure("Si.xyz", N_Si)
    builder.add_structure("B.xyz", N_B)

    builder.write("packmol.inp")
    """

    def __init__(
        self,
        tolerance: float,
        output_xyz: str,
        box_length: float,
        use_pbc: bool = False,
    ) -> None:
        self.tolerance: float = tolerance
        self.output_xyz: str = output_xyz
        self.box_length: float = box_length
        self.use_pbc: bool = use_pbc
        self.structure_blocks: List[Dict[str, object]] = []

    def add_structure(
        self,
        xyz_file: str,
        number: int,
        atom_radii: Optional[Dict[int, float]] = None,
    ) -> None:
        """
        1つの分子（元素）に対する structure ブロックを登録する。
        """
        block: Dict[str, object] = {
            "xyz": xyz_file,
            "number": number,
            "atom_radii": atom_radii,
        }
        self.structure_blocks.append(block)

    def write(
        self,
        inp_file: str,
    ) -> None:
        """
        .inp ファイルを書き出す。
        """
        L: float = self.box_length

        with open(inp_file, "w") as f:
            f.write(f"tolerance {self.tolerance}\n")

            if self.use_pbc:
                f.write(f"pbc {L:.6f} {L:.6f} {L:.6f}\n")

            f.write("filetype xyz\n")
            f.write(f"output {self.output_xyz}\n\n")

            for blk in self.structure_blocks:
                xyz = str(blk["xyz"])
                num = int(blk["number"])
                atom_radii = blk.get("atom_radii")

                f.write(f"structure {xyz}\n")
                f.write(f"  number {num}\n")
                f.write(f"  inside box 0.0 0.0 0.0  {L:.6f} {L:.6f} {L:.6f}\n")

                if atom_radii is not None:
                    actual_atom_radii = atom_radii
                    if not isinstance(actual_atom_radii, dict):
                        raise TypeError("atom_radii は dict で指定してください。")

                    for atom_index in sorted(actual_atom_radii.keys()):
                        radius = actual_atom_radii[atom_index]
                        f.write(f"  atoms {atom_index}\n")
                        f.write(f"    radius {radius:.6f}\n")
                        f.write("  end atoms\n")

                f.write("end structure\n\n")
