#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""packmol_util の設定保持クラス。"""

from typing import Optional, Sequence, Union
import os

import yaml
from x_logger import XLogger


class Config:
    """packmol_util 用の設定値を保持する。"""

    N_tot: int = 2000
    mass_density_g_cm3: float = 7.3336
    number_density_A3: float = 0.09119
    element_info: Union[str, Sequence[str]] = ["Fe", "Si", "B"]
    ratios: Sequence[int] = [82, 4, 14]

    packmol_bin: str = "packmol"
    minimum_separation: float = 2.0
    output_prefix: str = "amorphous"

    def __init__(
        self,
        yaml_path: Optional[str] = None,
        logger: Optional[XLogger] = None,
    ) -> None:
        if logger is None:
            logger = XLogger(logger_name=__name__)
        self._logger = logger

        if yaml_path:
            self._load_yaml(yaml_path)

    @classmethod
    def load_yaml(cls, yaml_path: Optional[str] = None) -> None:
        """YAML の内容でクラス変数を上書きする。"""
        if yaml_path is None:
            yaml_path = os.environ.get("PACKMOL_UTIL_CONFIG_YAML")
            if yaml_path is None:
                return

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        if data is None:
            return

        for key, value in data.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
            else:
                print("NO SUCH VAR:", key)

    def _load_yaml(self, yaml_path: Optional[str] = None) -> None:
        """YAML の内容でインスタンス属性を上書きする。"""
        self._logger.info(f"load_yaml: {yaml_path}")

        if yaml_path is None:
            yaml_path = os.environ.get("PACKMOL_UTIL_CONFIG_YAML")
            if yaml_path is None:
                return

        yaml_path = os.path.abspath(yaml_path)
        self._logger.info(f"abspath: {yaml_path}")

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        if data is None:
            return

        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print("NO SUCH VAR:", key)
