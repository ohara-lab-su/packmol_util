#!/usr/bin/env python3
"""
K.NAKADA, kengo.nakada@gmail.com
make_amorphous.py

アモルファス初期構造を Packmol により生成するための
入力ファイル (packmol.inp) を作成するスクリプト。

本スクリプトは、以下の 3 点を外部入力とする：

    1. 化学量論比（整数比）
    2. 密度 [g/cm^3] または 数密度 [1/Å^3] のいずれか一方
    3. セル内の総原子数 total_atom_count

Packmol は密度・化学量論比の概念を持たないため、本スクリプト側で
原子数とセル一辺長 L を計算し、Packmol 形式の inside box 指定に変換する。
"""

from typing import Dict, List, Optional, Sequence, Tuple
import subprocess

from param import ATOMIC_WEIGHTS, NA, A3_TO_CM3
from x_logger import XLogger


class Packmol:
    """
    amorphous構造を作成するのに助けになるメソッドなど
    """

    def __init__(
        self,
        input_file: Optional[str] = None,
        output_xyz: Optional[str] = None,
        output_log: Optional[str] = None,
        packmol_bin: Optional[str] = None,
        logger: Optional[XLogger] = None,
    ) -> None:
        # Packmol 実行や変換処理で使うファイル名を保持する。
        # make_*.py 側から明示されない場合は、標準的なファイル名を使う。
        self._logger: XLogger = logger or XLogger()
        self.input_file: str = input_file or "packmol.inp"
        self.output_xyz: str = output_xyz or "amorphous.xyz"
        self.output_log: str = output_log or "packmol.log"
        self.packmol_bin: str = packmol_bin or "packmol"

        self._logger.info(f"input_file: {self.input_file}")
        self._logger.info(f"output_xyz: {self.output_xyz}")
        self._logger.info(f"output_log: {self.output_log}")
        self._logger.info(f"packmol_bin: {self.packmol_bin}")

    def get_unit_atom_count(
        self,
        ratios: Sequence[int],
    ) -> int:
        """
        化学量論比1ユニットあたりの原子数を返す。
        例: [80, 9, 11] -> 100
        """
        self._logger.info("== get_unit_atom_count()")
        # ratios の和は、化学式 1 単位あたりの原子数に対応する。
        # Fe80Si9B11 なら 100、Li3PO4 なら 8 である。
        total = 0
        for value in ratios:
            total = total + value
        return total

    @staticmethod
    def get_atomic_weight(
        element: str,
    ) -> float:
        """汎用

        元素記号から原子量を取得する。
        """
        return ATOMIC_WEIGHTS[element]

    def average_atomic_weight(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
    ) -> float:
        """汎用

        化学量論比から平均原子量を計算する。
        """
        self._logger.info("== average_atomic_weight()")
        if len(symbols) != len(ratios):
            raise ValueError("symbols と ratios の長さが一致していません。")

        # 平均原子量は、密度と数密度の換算に使う。
        total_atoms: int = sum(ratios)
        if total_atoms <= 0:
            raise ValueError("ratios の合計が 0 以下です。")

        # 組成比で重み付けした原子量合計を作る。
        total_mass: float = 0.0
        for symbol, ratio in zip(symbols, ratios):
            atomic_weight: float = self.get_atomic_weight(symbol)
            total_mass += atomic_weight * float(ratio)

        return total_mass / float(total_atoms)

    def number_density_from_mass_density(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
        mass_density_g_cm3: float,
    ) -> float:
        """汎用

        質量密度から数密度 n [1/Å^3] を計算する。
        """
        self._logger.info("== number_density_from_mass_density()")
        # rho [g/cm3] * NA [1/mol] / M_avg [g/mol] で cm3 あたりの原子数になる。
        # A3_TO_CM3 を掛けて A3 あたりの数密度に変換する。
        M_avg: float = self.average_atomic_weight(symbols, ratios)
        return mass_density_g_cm3 * NA * A3_TO_CM3 / M_avg

    def mass_density_from_number_density(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
        number_density_A3: float,
    ) -> float:
        """汎用

        数密度 n [1/Å^3] から質量密度 ρ [g/cm^3] を計算する。
        """
        self._logger.info("== mass_density_from_number_density()")
        # number_density_A3 [1/A3] を質量密度 [g/cm3] へ戻す逆変換である。
        M_avg: float = self.average_atomic_weight(symbols, ratios)
        return number_density_A3 * M_avg / (NA * A3_TO_CM3)

    def cell_length_from_number_density(
        self,
        total_atom_count: int,
        number_density_A3: float,
    ) -> float:
        """汎用

        総原子数と数密度から立方体セル長 L [Å] を計算する。
        """
        self._logger.info("== cell_length_from_number_density()")
        if total_atom_count <= 0:
            raise ValueError("total_atom_count は正の整数である必要があります。")
        if number_density_A3 <= 0.0:
            raise ValueError("数密度 number_density_A3 は正の値である必要があります。")

        # 数密度 n = N / V なので、V = N / n でセル体積を決める。
        volume_A3: float = float(total_atom_count) / number_density_A3

        # 現状は立方体セルを前提としているため、L は体積の 3 乗根である。
        L: float = volume_A3 ** (1.0 / 3.0)
        return L

    def compute_element_counts(
        self,
        symbols: Sequence[str],
        ratios: Sequence[int],
        total_atom_count: int,
    ) -> Dict[str, int]:
        """汎用

        化学量論比と total_atom_count から各元素の原子数を決める。
        """
        self._logger.info("== compute_element_counts()")
        if len(symbols) != len(ratios):
            raise ValueError(
                "元素記号の種類数と、それに対応する化学量論比の個数が一致していません。"
            )

        if total_atom_count <= 0:
            raise ValueError("total_atom_count は正の整数で指定してください。")

        ratio_sum: int = sum(ratios)
        if ratio_sum <= 0:
            raise ValueError("化学量論比の総和が 0 以下です。")

        # total_atom_count を組成比で割り付けた理想原子数をまず実数で作る。
        ideal_counts: List[float] = []
        for ratio in ratios:
            ideal = total_atom_count * float(ratio) / float(ratio_sum)
            ideal_counts.append(ideal)

        # 整数化で失われた端数は、後で端数の大きい元素へ順に配る。
        int_counts: List[int] = [int(x) for x in ideal_counts]
        used: int = sum(int_counts)
        remainder: int = total_atom_count - used

        if remainder > 0:
            frac_list: List[Tuple[int, float]] = []
            for i, ideal in enumerate(ideal_counts):
                fractional = ideal - float(int_counts[i])
                frac_list.append((i, fractional))

            # 端数の大きい元素から 1 個ずつ足し、総原子数を合わせる。
            frac_list.sort(key=lambda x: x[1], reverse=True)

            for k in range(remainder):
                idx: int = frac_list[k][0]
                int_counts[idx] += 1

        # 元素記号をキーとする原子数辞書に戻す。
        result: Dict[str, int] = {}
        for sym, cnt in zip(symbols, int_counts):
            result[sym] = cnt

        return result

    def compute_cell_sizes(
        self,
        ratios: Sequence[int],
        max_atom_count: int,
    ) -> List[int]:
        """汎用

        化学量論比を厳密に保つセル原子数を列挙する。
        """
        self._logger.info("== generate_cell_sizes()")
        unit_atom_count = self.get_unit_atom_count(ratios)
        cell_sizes: List[int] = []

        multiplier = 1
        current_size = unit_atom_count * multiplier

        # 組成比を崩さない総原子数だけを列挙する。
        while current_size <= max_atom_count:
            cell_sizes.append(current_size)
            multiplier = multiplier + 1
            current_size = unit_atom_count * multiplier

        return cell_sizes

    def write_single_atom_xyz(
        self,
        filename: str,
        element: str,
    ) -> None:
        """単一原子のみを含む XYZ ファイルを生成する。"""
        self._logger.info("== write_single_atom_xyz()")
        # Packmol に単原子を配置させるため、1 原子だけを含む XYZ を作る。
        with open(filename, "w") as f:
            f.write("1\n")
            f.write(f"{element} atom template\n")
            f.write(f"{element}  0.0  0.0  0.0\n")

    def run_packmol(
        self,
        input_file: Optional[str] = None,
        output_log: Optional[str] = None,
        packmol_bin: Optional[str] = None,
    ) -> None:
        """Packmol を実行する。"""
        self._logger.info("== run_packmol()")
        if input_file is None:
            input_file = self.input_file

        if output_log is None:
            output_log = self.output_log

        if packmol_bin is None:
            packmol_bin = self.packmol_bin

        # Packmol は標準入力から .inp を読むため、input_file を stdin に渡す。
        # 標準出力と標準エラーはログファイルへまとめる。
        with open(input_file, "r") as fin, open(output_log, "w") as flog:
            result = subprocess.run(
                [packmol_bin],
                stdin=fin,
                stdout=flog,
                stderr=subprocess.STDOUT,
                text=True,
            )

        if result.returncode != 0:
            print(
                f"Packmol の終了ステータスが 0 ではありません (code={result.returncode})"
            )
            print(f"詳細はログ {output_log} を確認してください。")

    def xyz_to_poscar(
        self,
        xyz_file: str,
        poscar_file: str = "POSCAR",
        packmol_inp: str = "packmol.inp",
        comment: str = "packmol",
        elements: Optional[List[str]] = None,
    ) -> None:
        """Packmol が出力した XYZ を VASP POSCAR へ変換する。"""
        self._logger.info("== xyz_to_poscar()")
        if elements is None:
            raise ValueError("elements は指定してください。")

        # Packmol 出力 XYZ を読む。1 行目と 2 行目は XYZ のヘッダなので飛ばす。
        with open(xyz_file, "r") as f:
            lines = f.readlines()

        xyz_atoms = []
        for line in lines[2:]:
            parts = line.split()
            if len(parts) < 4:
                continue
            sym = parts[0]
            x, y, z = map(float, parts[1:4])
            xyz_atoms.append((sym, x, y, z))

        # POSCAR の格子長には、Packmol 入力の inside box で指定したセル長を使う。
        L = None
        with open(packmol_inp, "r") as f:
            for line in f:
                if "inside box" in line:
                    parts = line.split()
                    L = float(parts[-1])
                    break

        if L is None:
            raise RuntimeError(f"{packmol_inp} から L を取得できませんでした。")

        # Packmol 出力は Cartesian 座標なので、VASP POSCAR 用に Direct 座標へ変換する。
        frac_atoms = [(sym, x / L, y / L, z / L) for sym, x, y, z in xyz_atoms]

        # POSCAR では元素ごとに座標をまとめて出力するため、元素別に数と座標を集める。
        species_counts = {s: 0 for s in elements}
        species_positions = {s: [] for s in elements}

        for sym, fx, fy, fz in frac_atoms:
            if sym in elements:
                species_counts[sym] += 1
                species_positions[sym].append((fx, fy, fz))
            else:
                raise RuntimeError(f"未知の元素シンボル: {sym}")

        # VASP5 形式の POSCAR を書く。元素順序は make_*.py 側の symbols に従う。
        with open(poscar_file, "w") as f:
            f.write(f"{comment}\n")
            f.write("1.0\n")
            f.write(f"{L:.10f} 0.0 0.0\n")
            f.write(f"0.0 {L:.10f} 0.0\n")
            f.write(f"0.0 0.0 {L:.10f}\n")
            f.write(" ".join(elements) + "\n")
            f.write(" ".join(str(species_counts[s]) for s in elements) + "\n")
            f.write("Direct\n")

            for s in elements:
                for fx, fy, fz in species_positions[s]:
                    f.write(f"{fx:.10f}  {fy:.10f}  {fz:.10f}\n")
