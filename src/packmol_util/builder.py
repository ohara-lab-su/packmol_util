# packmol_util/builder.py (新規追加する汎用統合モジュール)

from typing import Dict, Optional, List
from packmol_util.packmol import Packmol
from packmol_util.packmol_inp import PackmolInp


class AmorphousBuilder:
    def __init__(
        self,
        symbols: List[str],
        ratios: List[int],
        total_atom_count: int,
        minimum_separation: float,
        mass_density: Optional[float] = None,
        number_density: Optional[float] = None,
    ):
        self.symbols = symbols
        self.ratios = ratios
        self.total_atom_count = total_atom_count
        self.minimum_separation = minimum_separation

        # 密度の計算とセル一辺の長さ決定
        self.packmol_runner = Packmol()
        if number_density is not None:
            self.box_length = self.packmol_runner.cell_length_from_number_density(
                total_atom_count, number_density
            )
        elif mass_density is not None:
            n_density = self.packmol_runner.number_density_from_mass_density(
                symbols, ratios, mass_density
            )
            self.box_length = self.packmol_runner.cell_length_from_number_density(
                total_atom_count, n_density
            )
        else:
            raise ValueError(
                "mass_density または number_density のどちらかを指定してください。"
            )

        self.templates: List[dict] = []

    def add_template(
        self,
        xyz_file: str,
        number: int,
        packing_radii: Optional[Dict[str, float]] = None,
    ):
        self.templates.append(
            {"xyz": xyz_file, "number": number, "radii": packing_radii}
        )

    def build(self, output_prefix: str):
        inp_file = f"{output_prefix}_packmol.inp"
        xyz_file = f"{output_prefix}_packmol.xyz"
        log_file = f"{output_prefix}_packmol.log"
        poscar_file = "POSCAR"

        # 1. PackmolInpの構築と書き出し
        inp_builder = PackmolInp(
            minimum_separation_distance=self.minimum_separation,
            output_xyz=xyz_file,
            box_length=self.box_length,
            use_pbc=True,
        )
        for t in self.templates:
            inp_builder.add_structure(t["xyz"], t["number"], t["radii"])
        inp_builder.write(inp_file)

        # 2. Packmolの実行
        runner = Packmol(input_file=inp_file, output_xyz=xyz_file, output_log=log_file)
        runner.run_packmol(input_file=inp_file, output_log=log_file)

        # 3. POSCARへの変換
        runner.xyz_to_poscar(
            xyz_file=xyz_file,
            poscar_file=poscar_file,
            packmol_inp=inp_file,
            comment=f"{output_prefix} amorphous initial model",
            elements=self.symbols,
        )
        print(
            f"構造作成が完了しました: {poscar_file} (Cell Length: {self.box_length:.4f} A)"
        )
