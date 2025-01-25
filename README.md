# ATM分析ダッシュボード

ATMの現金フローを分析し、可視化するためのStreamlitダッシュボードです。

## 機能

- 時系列での現金フロー分析
- 支店別の取引傾向分析
- 紙幣・硬貨の種別分析
- 予測モデルの可視化

## セットアップ手順

1. リポジトリのクローン
```bash
git clone [リポジトリURL]
cd ATM_master
```

2. Python仮想環境の作成と有効化
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

3. 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

4. ダッシュボードの起動
```bash
# Windows
.\start_dashboard.bat
# Mac/Linux
streamlit run dashboard.py
```

## 使用方法

1. ダッシュボードが起動すると、既定のWebブラウザで自動的に開きます
2. 左サイドバーから分析したい項目を選択
3. 各種フィルターを使用してデータを絞り込み

## 注意事項

- サンプルデータを使用する場合は、`data/sample_data`ディレクトリにデータを配置してください
- 実データを使用する場合は、`.env`ファイルで適切なパスを設定してください

## 必要システム要件

- Python 3.8以上
- Windows 10/11 または macOS/Linux
- 4GB以上のRAM

## ライセンス

このプロジェクトは非公開です。権限のあるユーザーのみが使用できます。 