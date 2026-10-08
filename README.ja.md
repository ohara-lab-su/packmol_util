# packmol_util
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/packmol_util/blob/main/README.ja.md)


Packmol を用いて、第一原理計算（VASP）や分子動力学（MD）シミュレーションのための**アモルファス初期構造（POSCAR）を自動生成する Python ユーティリティキット**。

化学量論比、密度（質量密度または数密度）、総原子数を指定するだけで、Packmol の入力ファイル作成、実行、および VASP 形式（Direct 座標）の POSCAR 出力までを一撃で自動完結させます。

---

## 💡 特徴

1. **直感的な密度指定**
   - Packmol 自体は「密度」や「原子量」を解釈できませんが、本ツールが内部で自動計算し、指定した密度を満たす立方体セル長 $L$ を算出します。
2. **元素記号による Exclusion Radius (排他半径) の指定**
   - Packmol 特有の不便な「XYZ内の原子インデックス指定」を隠蔽。`{"P": 0.25, "O": 1.05}` のように、直感的な元素名ベースの辞書で原子間の近接回避距離を制御できます。
3. **分子ユニット（幾何構造）の維持**
   - $\text{Li}_3\text{PO}_4$ のような系において、$\text{PO}_4$ 正四面体などの分子内結合距離を崩さずにアモルファス化（混合・パッキング）させることが可能です。
4. **極めてシンプルな高レベル API**
   - `AmorphousBuilder` を用いることで、煩雑なファイルのバケツリレー（.inp構築 $\rightarrow$ 外部実行 $\rightarrow$ 座標変換）をわずか数行のスクリプトに集約できます。

---

## 📁 ディレクトリ構成

```text
src/
├── packmol_util/
│
│   ├── __init__.py          # パッケージ初期化ファイル
│   ├── builder.py           # 高レベル統合ビルダー (AmorphousBuilder) ★NEW
│   ├── model.py             # テンプレートXYZ生成・構造定義モジュール
│   ├── packmol.py           # 密度計算・Packmol実行・POSCAR変換コア
│   ├── packmol_inp.py       # packmol.inp 構築用パースエンジン
│   ├── param.py             # 周期表の原子量・物理定数定義

└── example/                 # 物質固有の作成スクリプト配置場所
    ├── Li3PO4/
    │   └── make_Li3PO4.py
    └── FeSiB/
        └── make_FeSiB.py