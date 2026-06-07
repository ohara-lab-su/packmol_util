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
        # Packmol 入力ファイルでは tolerance として出力する。
        # Python 側では物理的な意味に近い名前として minimum_separation_distance を使う。
        self.minimum_separation_distance: float = minimum_separation_distance

        # Packmol が生成する XYZ ファイル名である。
        self.output_xyz: str = output_xyz

        # 立方体セルの一辺長 [Å] である。inside box と pbc の両方で使う。
        self.box_length: float = box_length

        # Packmol の pbc 行を出すかどうかを表す。
        self.use_pbc: bool = use_pbc

        # add_structure() で登録された structure ブロックを一時的に保持する。
        # ここには物質固有の意味ではなく、Packmol 入力へ出すための情報だけを置く。
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
        ここで与える半径は、Packmol が複数の structure を箱の中へ置くときの重なり回避に使う。
        """
        # ここではまだ Packmol 入力ファイルには書かない。
        # write() が呼ばれた時点で、登録済み block を順に structure ... end structure へ変換する。
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

        Packmol の radius 指定は atoms 1 2 3 のような 1 始まり index で書く。
        しかし make_*.py 側で 1, 2, 3 を直接書くと、XYZ の原子順に強く依存して読みにくくなる。
        そのため、make_*.py 側では {"P": 0.25, "O": 1.05} のように元素記号で書き、
        この関数で XYZ 内の実際の原子順を読む。

        返り値は ["P", "O", "O", "O", "O"] のようなリストである。
        このリストの 0 番目が Packmol の atoms 1 に対応する。
        """
        # XYZ 内の atom index 順に元素記号だけを保存する。
        # 座標値は、radius 指定を atom index に変換する処理では使わない。
        atom_symbols: List[str] = []

        with open(xyz_file, "r") as f:
            raw_lines: List[str] = f.readlines()

        if len(raw_lines) < 2:
            raise ValueError(f"XYZ ファイルの行数が不足している: {xyz_file}")

        # XYZ の 1 行目はテンプレート内原子数、2 行目はコメント行である。
        atom_count_text: str = raw_lines[0].strip()
        atom_count: int = int(atom_count_text)
        atom_lines: List[str] = raw_lines[2:]

        if len(atom_lines) < atom_count:
            raise ValueError(f"XYZ ファイルの原子行数が不足している: {xyz_file}")

        line_index: int = 0
        while line_index < atom_count:
            # 各原子行の 1 列目だけを元素記号として使う。
            # 座標値は Packmol の atom index 変換には不要である。
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

        この対応は Packmol 入力へ radius を書くためだけに使う。
        PO4 の P-O 距離や O-O 距離は、この関数では決めない。
        分子ユニット内部の距離は model.py の write_tetrahedral_unit_xyz() で決まる。
        """
        # XYZ の原子順を読み、同じ元素記号を持つ atom index をまとめる。
        atom_symbols: List[str] = self._read_xyz_atom_symbols(xyz_file=xyz_file)
        atom_indices_by_symbol: Dict[str, List[int]] = {}

        atom_position: int = 0
        for atom_symbol in atom_symbols:
            # Packmol の atoms 指定は 1 始まりなので、Python の位置に 1 を足す。
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

        Packmol の radius 指定は元素記号ではなく atom index に対して行う。
        そのため、このメソッドでは次の変換を行う。

        1. xyz_file を読み、元素記号ごとの atom index を調べる。
        2. make_*.py 側の {"P": r_P, "O": r_O} を、Packmol の atoms 1 / atoms 2 3 4 5 へ変換する。
        3. radius 行を書き出す。

        ここで扱う radius は配置用の排除半径であり、分子ユニット内部の結合距離ではない。
        """
        atom_indices_by_symbol: Dict[str, List[int]] = self._make_atom_indices_by_symbol(
            xyz_file=xyz_file,
        )

        # 元素記号ごとに、対応する atom index 群へ同じ radius を割り当てる。
        for atom_symbol in packing_radii_by_atom_symbol.keys():
            if atom_symbol not in atom_indices_by_symbol:
                raise ValueError(
                    f"{xyz_file} に元素記号 {atom_symbol} が存在しない。"
                )

            # 例えば PO4.xyz が P, O, O, O, O の順なら、O は atoms 2 3 4 5 になる。
            atom_indices: List[int] = atom_indices_by_symbol[atom_symbol]
            atom_indices_text: str = " ".join(str(atom_index) for atom_index in atom_indices)
            radius: float = packing_radii_by_atom_symbol[atom_symbol]
            if radius <= 0.0:
                raise ValueError(
                    f"packing radius は正の値で指定する: {atom_symbol}, {radius}"
                )

            # Packmol の atoms ブロックとして、同一元素記号に対応する atom index をまとめて出す。
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
            # 全 structure に共通する最小分離距離を Packmol の tolerance として書く。
            f.write(f"tolerance {self.minimum_separation_distance}\n")

            if self.use_pbc:
                # 直交立方セルの周期境界条件を Packmol に渡す。
                f.write(
                    f"pbc {box_length:.6f} {box_length:.6f} {box_length:.6f}\n"
                )

            # 入出力座標形式を XYZ に固定する。
            f.write("filetype xyz\n")
            f.write(f"output {self.output_xyz}\n\n")

            for structure_block in self.structure_blocks:
                # ここから 1 個の Packmol structure ブロックを書き始める。
                # 単原子テンプレートでも PO4 のような分子ユニットでも、Packmol では同じ structure として扱う。
                xyz_file = str(structure_block["xyz"])
                number = int(structure_block["number"])
                packing_radii_by_atom_symbol = structure_block.get(
                    "packing_radii_by_atom_symbol"
                )

                # structure は、1 種類のテンプレート座標を Packmol に登録する行である。
                f.write(f"structure {xyz_file}\n")

                # number は、そのテンプレートを何個複製して配置するかを指定する。
                f.write(f"  number {number}\n")
                # inside box は、テンプレートの重心・配置位置が入る直方体領域を指定する。
                # ここでは立方体セル全体を配置領域にしている。
                f.write(
                    "  inside box "
                    "0.0 0.0 0.0  "
                    f"{box_length:.6f} {box_length:.6f} {box_length:.6f}\n"
                )

                if packing_radii_by_atom_symbol is not None:
                    # 元素記号で指定された packing 半径を、Packmol が要求する atom index 指定へ変換する。
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
