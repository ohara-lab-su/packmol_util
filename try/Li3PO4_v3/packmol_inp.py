#!/usr/bin/env python3
"""
Packmol の入力ファイルを構築するための共通クラスである。

このファイルは、物質固有の構造を知らない。
make_*.py 側から渡された structure 情報を、Packmol の .inp 形式へ変換する。
"""

from typing import Dict, List, Optional, TextIO


class PackmolInp:
    """
    Packmol の .inp ファイルを構築するためのクラスである。

    minimum_separation_distance は、Packmol 入力ファイル先頭の tolerance に対応する。
    これは、配置時に原子や分子ユニットが近づきすぎないようにする全体条件である。

    add_structure() で登録する 1 件が、Packmol 入力の structure ... end structure
    ブロック 1 個に対応する。
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
        1 つの単原子テンプレートまたは分子ユニットテンプレートを登録する。

        xyz_file は、Li.xyz、Fe.xyz、PO4.xyz などのテンプレート座標である。
        number は、そのテンプレートを Packmol が何個配置するかである。

        packing_radii_by_atom_symbol は、必要な場合だけ指定する配置用の排除半径である。
        これは分子内距離ではない。例えば PO4 の P-O 距離や O-O 距離は、PO4.xyz を
        作る段階で決まる。
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
        XYZ ファイルから、Packmol の atom index に対応する元素記号列を読む。

        Packmol の atoms 指定は 1 始まりの atom index を使う。
        make_*.py 側では元素記号で指定し、この関数で XYZ 内の並び順を読み取る。
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

        例えば PO4.xyz が P, O, O, O, O の順なら、P -> [1]、O -> [2, 3, 4, 5]
        という対応を作る。
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
        file_object: TextIO,
        xyz_file: str,
        packing_radii_by_atom_symbol: Dict[str, float],
    ) -> None:
        """
        元素記号で指定された packing 半径を Packmol の atom index 指定へ変換して書く。

        Packmol の radius 指定は atom index に対して行うため、ここで XYZ ファイルを読んで
        元素記号から atom index へ変換する。
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

            file_object.write(f"  atoms {atom_indices_text}\n")
            file_object.write(f"    radius {radius:.6f}\n")
            file_object.write("  end atoms\n")

    def write(
        self,
        inp_file: str,
    ) -> None:
        """
        Packmol の .inp ファイルを書き出す。

        ここで、make_*.py 側で作った recipe が、Packmol の具体的な入力形式になる。
        structure ブロックは、1 種類の単原子テンプレートまたは 1 種類の分子ユニットを
        Packmol に何個配置させるかを表す。
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
                packing_radii_by_atom_symbol = structure_block.get(
                    "packing_radii_by_atom_symbol"
                )

                f.write(f"structure {xyz_file}\n")
                f.write(f"  number {number}\n")
                f.write(
                    "  inside box "
                    "0.0 0.0 0.0  "
                    f"{box_length:.6f} {box_length:.6f} {box_length:.6f}\n"
                )

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

                f.write("end structure\n\n")
