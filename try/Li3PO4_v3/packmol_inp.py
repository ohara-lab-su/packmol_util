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
        packing_radii_by_atom_symbol: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        1つの分子または単原子テンプレートに対する structure ブロックを登録する。
        """
        block: Dict[str, object] = {
            "xyz": xyz_file,
            "number": number,
            "packing_radii_by_atom_symbol": packing_radii_by_atom_symbol,
        }
        self.structure_blocks.append(block)

    def _read_xyz_atom_symbols(
        self,
        xyz_file: str,
    ) -> List[str]:
        """
        XYZ ファイルから Packmol の atom index に対応する元素記号列を読む。
        """
        atom_symbols: List[str] = []

        with open(xyz_file, "r") as f:
            raw_lines: List[str] = f.readlines()

        if len(raw_lines) < 2:
            raise ValueError(f"XYZ ファイルの行数が不足している: {xyz_file}")

        atom_count_text: str = raw_lines[0].strip()
        atom_count: int = int(atom_count_text)
        atom_lines: List[str] = raw_lines[2:]

        if len(atom_lines) < atom_count:
            raise ValueError(f"XYZ ファイルの原子行数が不足している: {xyz_file}")

        line_index: int = 0
        while line_index < atom_count:
            atom_line: str = atom_lines[line_index].strip()
            fields: List[str] = atom_line.split()
            if len(fields) < 1:
                raise ValueError(f"XYZ ファイルに空の原子行がある: {xyz_file}")
            atom_symbols.append(fields[0])
            line_index = line_index + 1

        return atom_symbols

    def _make_atom_indices_by_symbol(
        self,
        xyz_file: str,
    ) -> Dict[str, List[int]]:
        """
        元素記号から Packmol の 1 始まり atom index への対応を作る。
        """
        atom_symbols: List[str] = self._read_xyz_atom_symbols(xyz_file=xyz_file)
        atom_indices_by_symbol: Dict[str, List[int]] = {}

        atom_position: int = 0
        for atom_symbol in atom_symbols:
            atom_index: int = atom_position + 1
            if atom_symbol not in atom_indices_by_symbol:
                atom_indices_by_symbol[atom_symbol] = []
            atom_indices_by_symbol[atom_symbol].append(atom_index)
            atom_position = atom_position + 1

        return atom_indices_by_symbol

    def _write_packing_radii_by_atom_symbol(
        self,
        file_object,
        xyz_file: str,
        packing_radii_by_atom_symbol: Dict[str, float],
    ) -> None:
        """
        元素記号で指定された packing 半径を Packmol の atom index 指定へ変換して書く。
        """
        atom_indices_by_symbol: Dict[str, List[int]] = self._make_atom_indices_by_symbol(
            xyz_file=xyz_file,
        )

        for atom_symbol in packing_radii_by_atom_symbol.keys():
            if atom_symbol not in atom_indices_by_symbol:
                raise ValueError(
                    f"{xyz_file} に元素記号 {atom_symbol} が存在しない。"
                )

            atom_indices: List[int] = atom_indices_by_symbol[atom_symbol]
            atom_indices_text: str = " ".join(str(atom_index) for atom_index in atom_indices)
            radius: float = packing_radii_by_atom_symbol[atom_symbol]

            file_object.write(f"  atoms {atom_indices_text} ")
            file_object.write(f"    radius {radius:.6f} ")
            file_object.write("  end atoms ")

    def write(
        self,
        inp_file: str,
    ) -> None:
        """
        .inp ファイルを書き出す。
        """
        box_length: float = self.box_length

        with open(inp_file, "w") as f:
            f.write(f"tolerance {self.minimum_separation_distance} ")

            if self.use_pbc:
                f.write(
                    f"pbc {box_length:.6f} {box_length:.6f} {box_length:.6f} "
                )

            f.write("filetype xyz ")
            f.write(f"output {self.output_xyz} ")

            for structure_block in self.structure_blocks:
                xyz_file = str(structure_block["xyz"])
                number = int(structure_block["number"])
                packing_radii_by_atom_symbol = structure_block.get(
                    "packing_radii_by_atom_symbol"
                )

                f.write(f"structure {xyz_file} ")
                f.write(f"  number {number} ")
                f.write(
                    "  inside box "
                    "0.0 0.0 0.0  "
                    f"{box_length:.6f} {box_length:.6f} {box_length:.6f} " )

                if packing_radii_by_atom_symbol is not None:
                    if not isinstance(packing_radii_by_atom_symbol, dict):
                        raise TypeError(
                            "packing_radii_by_atom_symbol は dict で指定する。"
                        )
                    self._write_packing_radii_by_atom_symbol(
                        file_object=f,
                        xyz_file=xyz_file,
                        packing_radii_by_atom_symbol=packing_radii_by_atom_symbol,
                    )

                f.write("end structure")
