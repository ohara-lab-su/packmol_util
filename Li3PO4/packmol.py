#!/usr/bin/env python3
"""
Li3PO4 の Packmol 初期構造作成に使う補助クラスである。
"""

from __future__ import annotations

import math
import subprocess
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from packmol_inp import PackmolInp

NA: float = 6.02214076e23
A3_TO_CM3: float = 1.0e-24

ATOMIC_WEIGHTS: Dict[str, float] = {
    "Li": 6.941,
    "B": 10.811,
    "O": 15.9994,
    "Si": 28.0855,
    "P": 30.973762,
    "Fe": 55.845,
}


class Packmol:
    """
    Packmol による非晶質初期構造作成を補助するクラスである。
    """

    def __init__(
        self,
        input_file: Optional[str] = None,
        output_xyz: Optional[str] = None,
        output_log: Optional[str] = None,
        packmol_bin: Optional[str] = None,
    ) -> None:
        """
        Args:
            input_file: Packmol 入力ファイル名である。
            output_xyz: Packmol 出力 XYZ ファイル名である。
            output_log: Packmol ログファイル名である。
            packmol_bin: Packmol 実行ファイルである。
        """
        if input_file is None:
            self.input_file = "packmol.inp"
        else:
            self.input_file = input_file

        if output_xyz is None:
            self.output_xyz = "amorphous.xyz"
        else:
            self.output_xyz = output_xyz

        if output_log is None:
            self.output_log = "packmol.log"
        else:
            self.output_log = output_log

        if packmol_bin is None:
            self.packmol_bin = "packmol"
        else:
            self.packmol_bin = packmol_bin

    def get_unit_atom_count(
        self,
        ratios: Sequence[int],
    ) -> int:
        """
        化学量論比 1 単位あたりの原子数を返す。

        Args:
            ratios: 化学量論比である。

        Returns:
            化学量論比 1 単位あたりの原子数である。
        """
        total: int = 0
        for value in ratios:
            total = total + value
        return total

    def get_atomic_weight(
        self,
        element: str,
    ) -> float:
        """
        元素記号から原子量を返す。

        Args:
            element: 元素記号である。

        Returns:
            原子量である。
        """
        return ATOMIC_WEIGHTS[element]

    def average_atomic_weight(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
    ) -> float:
        """
        化学量論比から平均原子量を計算する。

        Args:
            symbols: 元素記号の列である。
            ratios: 元素記号に対応する化学量論比である。

        Returns:
            平均原子量である。
        """
        if len(symbols) != len(ratios):
            raise ValueError("symbols と ratios の長さが一致していない。")

        total_atoms: int = 0
        for ratio in ratios:
            total_atoms = total_atoms + ratio

        if total_atoms <= 0:
            raise ValueError("ratios の合計は正である必要がある。")

        total_mass: float = 0.0
        index: int = 0
        for symbol in symbols:
            ratio_value: int = ratios[index]
            atomic_weight: float = self.get_atomic_weight(symbol)
            total_mass = total_mass + atomic_weight * float(ratio_value)
            index = index + 1

        return total_mass / float(total_atoms)

    def number_density_from_mass_density(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
        mass_density_g_cm3: float,
    ) -> float:
        """
        質量密度から原子数密度を計算する。

        Args:
            symbols: 元素記号の列である。
            ratios: 元素記号に対応する化学量論比である。
            mass_density_g_cm3: 質量密度である。

        Returns:
            原子数密度である。
        """
        average_weight: float = self.average_atomic_weight(symbols, ratios)
        number_density: float = mass_density_g_cm3 * NA * A3_TO_CM3 / average_weight
        return number_density

    def cell_length_from_number_density(
        self,
        atom_count: int,
        number_density_a3: float,
    ) -> float:
        """
        原子数と原子数密度から立方体セル長を計算する。

        Args:
            atom_count: セル内の総原子数である。
            number_density_a3: 原子数密度である。

        Returns:
            立方体セルの一辺長である。
        """
        if atom_count <= 0:
            raise ValueError("atom_count は正の整数である必要がある。")

        if number_density_a3 <= 0.0:
            raise ValueError("number_density_a3 は正である必要がある。")

        volume_a3: float = float(atom_count) / number_density_a3
        cell_length: float = volume_a3 ** (1.0 / 3.0)
        return cell_length

    def compute_element_counts(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
        atom_count: int,
    ) -> Dict[str, int]:
        """
        総原子数と化学量論比から元素別原子数を計算する。

        Args:
            symbols: 元素記号の列である。
            ratios: 元素記号に対応する化学量論比である。
            atom_count: 総原子数である。

        Returns:
            元素記号をキー、原子数を値とする辞書である。
        """
        if len(symbols) != len(ratios):
            raise ValueError("symbols と ratios の長さが一致していない。")

        if atom_count <= 0:
            raise ValueError("atom_count は正の整数である必要がある。")

        ratio_sum: int = 0
        for ratio in ratios:
            ratio_sum = ratio_sum + ratio

        if ratio_sum <= 0:
            raise ValueError("ratios の合計は正である必要がある。")

        ideal_counts: List[float] = []
        int_counts: List[int] = []

        for ratio in ratios:
            ideal_count: float = float(atom_count) * float(ratio) / float(ratio_sum)
            ideal_counts.append(ideal_count)
            int_counts.append(int(ideal_count))

        used_count: int = 0
        for int_count in int_counts:
            used_count = used_count + int_count

        remainder: int = atom_count - used_count
        fractional_values: List[Tuple[int, float]] = []
        index: int = 0
        for ideal_count in ideal_counts:
            fractional_value: float = ideal_count - float(int_counts[index])
            fractional_values.append((index, fractional_value))
            index = index + 1

        fractional_values.sort(key=lambda item: item[1], reverse=True)

        remainder_index: int = 0
        while remainder_index < remainder:
            target_index: int = fractional_values[remainder_index][0]
            int_counts[target_index] = int_counts[target_index] + 1
            remainder_index = remainder_index + 1

        result: Dict[str, int] = {}
        index = 0
        for symbol in symbols:
            result[symbol] = int_counts[index]
            index = index + 1

        return result

    def write_single_atom_xyz(
        self,
        filename: str,
        element: str,
    ) -> None:
        """
        単原子 XYZ テンプレートを書き出す。

        Args:
            filename: 書き出す XYZ ファイル名である。
            element: 元素記号である。
        """
        with open(filename, "w", encoding="utf-8") as output_file:
            output_file.write("1\n")
            output_file.write(f"{element} atom template\n")
            output_file.write(f"{element} 0.000000 0.000000 0.000000\n")

    def write_po4_xyz(
        self,
        filename: str,
        p_o_distance: float = 1.54,
    ) -> None:
        """
        正四面体 PO4 ユニットの XYZ テンプレートを書き出す。

        Args:
            filename: 書き出す XYZ ファイル名である。
            p_o_distance: P-O 距離である。
        """
        scale: float = p_o_distance / math.sqrt(3.0)
        positions: List[Tuple[str, float, float, float]] = []
        positions.append(("P", 0.0, 0.0, 0.0))
        positions.append(("O", scale, scale, scale))
        positions.append(("O", scale, -scale, -scale))
        positions.append(("O", -scale, scale, -scale))
        positions.append(("O", -scale, -scale, scale))

        with open(filename, "w", encoding="utf-8") as output_file:
            output_file.write("5\n")
            output_file.write("PO4 tetrahedral unit template\n")
            for symbol, x_value, y_value, z_value in positions:
                output_file.write(
                    f"{symbol} {x_value:.10f} {y_value:.10f} {z_value:.10f}\n"
                )

    def write_li3po4_packmol_input(
        self,
        formula_unit_count: int,
        mass_density_g_cm3: float,
        inp_file: str = "packmol.inp",
        output_xyz: str = "li3po4_packmol.xyz",
        li_xyz: str = "Li.xyz",
        po4_xyz: str = "PO4.xyz",
        tolerance: float = 1.8,
        seed: Optional[int] = 191917,
        p_o_distance: float = 1.54,
        use_pbc: bool = True,
        precision: Optional[float] = 0.01,
        nloop: Optional[int] = None,
        maxit: Optional[int] = None,
    ) -> float:
        """
        Li3PO4 用の Packmol 入力と構造テンプレートを書き出す。

        Args:
            formula_unit_count: Li3PO4 の式単位数である。
            mass_density_g_cm3: 質量密度である。
            inp_file: Packmol 入力ファイル名である。
            output_xyz: Packmol 出力 XYZ ファイル名である。
            li_xyz: Li 単原子テンプレートのファイル名である。
            po4_xyz: PO4 ユニットテンプレートのファイル名である。
            tolerance: Packmol tolerance である。
            seed: Packmol seed である。
            p_o_distance: PO4 テンプレートの P-O 距離である。
            use_pbc: Packmol pbc 行を書くかどうかである。
            precision: Packmol precision である。
            nloop: Packmol nloop である。
            maxit: Packmol maxit である。

        Returns:
            計算された立方体セル長である。
        """
        if formula_unit_count <= 0:
            raise ValueError("formula_unit_count は正の整数である必要がある。")

        li_count: int = formula_unit_count * 3
        po4_count: int = formula_unit_count
        atom_count: int = formula_unit_count * 8
        symbols: List[str] = ["Li", "P", "O"]
        ratios: List[int] = [3, 1, 4]
        number_density: float = self.number_density_from_mass_density(
            symbols=symbols,
            ratios=ratios,
            mass_density_g_cm3=mass_density_g_cm3,
        )
        cell_length: float = self.cell_length_from_number_density(
            atom_count=atom_count,
            number_density_a3=number_density,
        )

        self.write_single_atom_xyz(filename=li_xyz, element="Li")
        self.write_po4_xyz(filename=po4_xyz, p_o_distance=p_o_distance)

        builder = PackmolInp(
            tolerance=tolerance,
            output_xyz=output_xyz,
            box_length=cell_length,
            filetype="xyz",
            seed=seed,
            use_pbc=use_pbc,
            precision=precision,
            nloop=nloop,
            maxit=maxit,
        )
        builder.add_structure(xyz_file=li_xyz, number=li_count)
        builder.add_structure(xyz_file=po4_xyz, number=po4_count)
        builder.write(inp_file=inp_file)

        return cell_length

    def run_packmol(
        self,
        input_file: Optional[str] = None,
        output_log: Optional[str] = None,
        packmol_bin: Optional[str] = None,
    ) -> None:
        """
        Packmol を実行する。

        Args:
            input_file: Packmol 入力ファイル名である。
            output_log: Packmol ログファイル名である。
            packmol_bin: Packmol 実行ファイルである。
        """
        if input_file is None:
            actual_input_file: str = self.input_file
        else:
            actual_input_file = input_file

        if output_log is None:
            actual_output_log: str = self.output_log
        else:
            actual_output_log = output_log

        if packmol_bin is None:
            actual_packmol_bin: str = self.packmol_bin
        else:
            actual_packmol_bin = packmol_bin

        with open(actual_input_file, "r", encoding="utf-8") as input_handle:
            with open(actual_output_log, "w", encoding="utf-8") as log_handle:
                result = subprocess.run(
                    [actual_packmol_bin],
                    stdin=input_handle,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False,
                )

        if result.returncode != 0:
            with open(actual_output_log, "r", encoding="utf-8") as log_handle:
                log_lines: List[str] = log_handle.readlines()

            log_tail: str = "".join(log_lines[-120:])

            raise RuntimeError(
                "Packmol の終了ステータスが 0 ではない。\n"
                f"log = {actual_output_log}\n"
                "Packmol log tail:\n"
                f"{log_tail}"
            )

    def _read_xyz_atoms(
        self,
        xyz_file: str,
    ) -> List[Tuple[str, float, float, float]]:
        """
        XYZ ファイルから原子座標を読む。

        Args:
            xyz_file: XYZ ファイル名である。

        Returns:
            元素記号と Cartesian 座標のリストである。
        """
        with open(xyz_file, "r", encoding="utf-8") as input_file:
            lines: List[str] = input_file.readlines()

        atoms: List[Tuple[str, float, float, float]] = []
        for line in lines[2:]:
            parts: List[str] = line.split()
            if len(parts) < 4:
                continue

            symbol: str = parts[0]
            x_value: float = float(parts[1])
            y_value: float = float(parts[2])
            z_value: float = float(parts[3])
            atoms.append((symbol, x_value, y_value, z_value))

        return atoms

    def xyz_to_poscar(
        self,
        xyz_file: str,
        poscar_file: str,
        cell_length: float,
        elements: Sequence[str],
        comment: str = "packmol Li3PO4",
    ) -> None:
        """
        Packmol 出力 XYZ を VASP POSCAR へ変換する。

        Args:
            xyz_file: Packmol 出力 XYZ ファイル名である。
            poscar_file: 書き出す POSCAR ファイル名である。
            cell_length: 立方体セルの一辺長である。
            elements: POSCAR に書く元素順である。
            comment: POSCAR コメント行である。
        """
        atoms: List[Tuple[str, float, float, float]] = self._read_xyz_atoms(xyz_file)
        species_positions: Dict[str, List[Tuple[float, float, float]]] = {}
        species_counts: Dict[str, int] = {}

        for element in elements:
            species_positions[element] = []
            species_counts[element] = 0

        for symbol, x_value, y_value, z_value in atoms:
            if symbol not in species_positions:
                raise RuntimeError(f"未知の元素シンボルである: {symbol}")

            x_fractional: float = x_value / cell_length
            y_fractional: float = y_value / cell_length
            z_fractional: float = z_value / cell_length
            species_positions[symbol].append((x_fractional, y_fractional, z_fractional))
            species_counts[symbol] = species_counts[symbol] + 1

        with open(poscar_file, "w", encoding="utf-8") as output_file:
            output_file.write(f"{comment}\n")
            output_file.write("1.0\n")
            output_file.write(f"{cell_length:.10f} 0.0000000000 0.0000000000\n")
            output_file.write(f"0.0000000000 {cell_length:.10f} 0.0000000000\n")
            output_file.write(f"0.0000000000 0.0000000000 {cell_length:.10f}\n")
            output_file.write(" ".join(elements) + "\n")
            output_file.write(
                " ".join(str(species_counts[element]) for element in elements) + "\n"
            )
            output_file.write("Direct\n")

            for element in elements:
                for x_fractional, y_fractional, z_fractional in species_positions[
                    element
                ]:
                    output_file.write(
                        f"{x_fractional:.10f} {y_fractional:.10f} {z_fractional:.10f}\n"
                    )


def main0() -> None:
    """
    Li3PO4 の Packmol 入力を作成する実行例である。
    """
    packmol = Packmol(
        input_file="packmol.inp",
        output_xyz="li3po4_packmol.xyz",
        output_log="packmol.log",
        packmol_bin="packmol",
    )
    cell_length: float = packmol.write_li3po4_packmol_input(
        formula_unit_count=64,
        mass_density_g_cm3=2.46,
        inp_file="packmol.inp",
        output_xyz="li3po4_packmol.xyz",
        li_xyz="Li.xyz",
        po4_xyz="PO4.xyz",
        tolerance=1.8,
        seed=191917,
        p_o_distance=1.54,
        use_pbc=True,
        precision=0.01,
    )
    print(f"cell_length = {cell_length:.10f} Angstrom")
    print("packmol < packmol.inp")
    print("Packmol 実行後に以下を呼ぶ。")
    print(
        "packmol.xyz_to_poscar('li3po4_packmol.xyz', 'POSCAR', cell_length, ['Li', 'P', 'O'])"
    )


def main() -> None:
    """
    Li3PO4 の Packmol 入力作成、Packmol 実行、POSCAR 作成を行う。
    """
    packmol = Packmol(
        input_file="packmol.inp",
        output_xyz="li3po4_packmol.xyz",
        output_log="packmol.log",
        packmol_bin="packmol",
    )

    cell_length: float = packmol.write_li3po4_packmol_input(
        formula_unit_count=64,
        mass_density_g_cm3=2.46,
        inp_file="packmol.inp",
        output_xyz="li3po4_packmol.xyz",
        li_xyz="Li.xyz",
        po4_xyz="PO4.xyz",
        tolerance=1.8,
        seed=191917,
        p_o_distance=1.54,
        use_pbc=True,
        precision=0.01,
    )

    packmol.run_packmol(
        input_file="packmol.inp",
        output_log="packmol.log",
        packmol_bin="packmol",
    )

    packmol.xyz_to_poscar(
        xyz_file="li3po4_packmol.xyz",
        poscar_file="POSCAR",
        cell_length=cell_length,
        elements=["Li", "P", "O"],
        comment="Li3PO4 amorphous initial model generated by Packmol",
    )

    print(f"cell_length = {cell_length:.10f} Angstrom")
    print("created: Li.xyz")
    print("created: PO4.xyz")
    print("created: packmol.inp")
    print("created: li3po4_packmol.xyz")
    print("created: packmol.log")
    print("created: POSCAR")


if __name__ == "__main__":
    main()
