import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta

# 基本的なフォント設定
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']

# 日本語の曜日マッピング
WEEKDAY_MAP = {
    'Monday': '月',
    'Tuesday': '火',
    'Wednesday': '水',
    'Thursday': '木',
    'Friday': '金',
    'Saturday': '土',
    'Sunday': '日'
}

class ATMDashboard:
    def __init__(self):
        try:
            self.base_dir = os.getcwd()
            print(f"作業ディレクトリ: {self.base_dir}")
            
            # 金種の定義
            self.bills = {
                '10000': '10000円札',
                '5000': '5000円札',
                '2000': '2000円札',
                '1000': '1000円札'
            }
            
            self.coins = {
                '500': '500円',
                '100': '100円',
                '50': '50円',
                '10': '10円',
                '5': '5円',
                '1': '1円'
            }
            
            self.branch_data = {}
            
            # データの読み込みを試行
            try:
                self.load_data()
                print("データ読み込み完了")
            except Exception as e:
                print(f"データ読み込みエラー: {str(e)}")
                print("デモデータを使用します")
                self.create_demo_data()
            
            # ページ設定
            self.setup_page()
            
        except Exception as e:
            print(f"初期化エラー: {str(e)}")
            # 最低限の初期化を確保
            self.branch_data = {}
            self.create_demo_data()
            self.setup_page()

    def load_data(self):
        """データの読み込み"""
        branch_codes = ['00512', '00524', '00525', '00609', '00616', 
                       '00643', '00669', '00748', '00796']
        
        data_loaded = False
        for code in branch_codes:
            try:
                # ATM精算データ
                atm_files = [f for f in os.listdir(self.base_dir) if f.startswith(f"{code}_ATM精算")]
                if atm_files:
                    atm_path = os.path.join(self.base_dir, atm_files[0])
                    print(f"読み込むファイル: {atm_path}")
                    atm_df = pd.read_csv(atm_path, encoding='cp932')
                    
                    # 日付と時刻の変換
                    atm_df['日付'] = pd.to_datetime(atm_df['日付'].astype(str), format='%Y%m%d')
                    atm_df['曜日'] = atm_df['日付'].dt.day_name().map(WEEKDAY_MAP)
                    
                    # 時刻の処理
                    atm_df['時刻'] = atm_df['時刻'].astype(str).str.zfill(6)
                    atm_df['時刻'] = pd.to_datetime(atm_df['時刻'], format='%H%M%S').dt.time
                    
                    # 金種データの列を特定
                    bill_cols = []
                    coin_cols = []
                    
                    # 紙幣の列を検索
                    for bill_value in self.bills.keys():
                        col_pattern = f'ATM現金（手入力以外）入金（{bill_value}円）枚数'
                        matching_cols = [col for col in atm_df.columns if col.replace(' ', '') == col_pattern.replace(' ', '')]
                        if matching_cols:
                            bill_cols.extend(matching_cols)
                    
                    # 硬貨の列を検索
                    for coin_value in self.coins.keys():
                        col_pattern = f'ATM現金（手入力以外）入金（{coin_value}円）枚数'
                        matching_cols = [col for col in atm_df.columns if col.replace(' ', '') == col_pattern.replace(' ', '')]
                        if matching_cols:
                            coin_cols.extend(matching_cols)
                    
                    self.branch_data[code] = {
                        'atm_df': atm_df,
                        'bill_cols': bill_cols,
                        'coin_cols': coin_cols
                    }
                    data_loaded = True
                    print(f"支店{code}のデータを読み込みました")
                    
            except Exception as e:
                print(f"支店{code}のデータ読み込みでエラー: {str(e)}")
                continue
        
        if not data_loaded:
            raise Exception("データファイルが見つかりませんでした。")

    def setup_page(self):
        """ページの基本設定"""
        try:
            # タイトルの設定
            st.title('ATM取引分析ダッシュボード')
            
            # サイドバーでページ選択
            st.sidebar.title('ページを選択')
            
            # セッションステートの初期化
            if 'page' not in st.session_state:
                st.session_state.page = '概要'
                print("ページ状態を初期化: 概要")
            
            # ページ選択
            self.page = st.sidebar.radio(
                'ページを選択してください',
                ['概要', '金種別分析', '支店間比較'],
                key='page_selector',
                label_visibility='collapsed'
            )
            
            print(f"現在のページ: {self.page}")
            
        except Exception as e:
            print(f"ページ設定エラー: {str(e)}")
            # デフォルト値の設定
            self.page = '概要'
            st.error("ページの初期化中にエラーが発生しました。デフォルトページを表示します。")

    def show_overview(self):
        """概要ページの表示"""
        st.title('ATM運用分析ダッシュボード')
        
        try:
            # データが存在しない場合はデモデータを作成
            if not self.branch_data:
                st.warning("データが読み込まれていません。デモデータを使用します。")
                self.create_demo_data()
            
            # 支店選択
            branch_codes = list(self.branch_data.keys())
            if not branch_codes:
                st.error("利用可能な支店データがありません。")
                return
                
            selected_branch = st.selectbox(
                '支店を選択してください',
                branch_codes
            )
            
            if selected_branch in self.branch_data:
                data = self.branch_data[selected_branch]
                df = data['atm_df']
                
                # 月選択
                available_months = df['日付'].dt.to_period('M').unique()
                if len(available_months) == 0:
                    st.error("選択された支店の月別データがありません。")
                    return
                    
                selected_month = st.selectbox(
                    '月を選択してください',
                    available_months,
                    format_func=lambda x: f"{x.year}年{x.month}月"
                )
                
                # 選択された月のデータでフィルタリング
                df_filtered = df[df['日付'].dt.to_period('M') == selected_month]
                
                if len(df_filtered) == 0:
                    st.warning(f"選択された月（{selected_month}）のデータがありません。")
                    return
                
                # 基本統計
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric('取引件数', f"{len(df_filtered):,}件")
                with col2:
                    avg_balance = df_filtered['在高合計金額'].mean()
                    st.metric('平均在高金額', f"{int(avg_balance):,}円")
                with col3:
                    max_balance = df_filtered['在高合計金額'].max()
                    st.metric('最大在高金額', f"{int(max_balance):,}円")
                
                # グラフを横並びに配置
                col_left, col_right = st.columns(2)
                
                with col_left:
                    # 時間帯別取引数
                    st.subheader('時間帯別ATM現金入金取引数')
                    df_filtered['hour'] = pd.to_datetime(df_filtered['時刻'].astype(str)).dt.hour
                    
                    # ATM現金入金取引のみを集計（入金額が0より大きい取引）
                    df_filtered['ATM現金入金取引'] = (df_filtered['ATM現金入金計金額'] > 0).astype(int)
                    hourly_counts = df_filtered.groupby('hour')['ATM現金入金取引'].sum()
                    
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.bar(hourly_counts.index, hourly_counts.values)
                    ax.set_xlabel('時間帯')
                    ax.set_ylabel('ATM現金入金取引数（件）')
                    
                    # X軸の目盛りを設定（0-23時）
                    ax.set_xticks(range(24))
                    ax.set_xticklabels([f'{h}時' for h in range(24)])
                    plt.xticks(rotation=45)
                    
                    # グリッド線を追加
                    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                    
                    # データソースの説明
                    st.markdown(f"""
                    **データソース**:
                    - 対象データ: ATM現金入金取引データ
                    - 集計期間: {selected_month.strftime('%Y年%m月')}
                    - 集計項目: ATM現金入金取引数
                    - 集計方法: 時間帯別の取引件数
                    """)
                
                with col_right:
                    # 日別推移
                    st.subheader('日別在高金額推移')
                    daily_balance = df_filtered.groupby(['日付', '曜日'])['在高合計金額'].mean().reset_index()
                    fig, ax = plt.subplots(figsize=(6, 4))
                    # 百万円単位に変換
                    daily_balance['在高合計金額_百万円'] = daily_balance['在高合計金額'] / 1_000_000
                    ax.plot(daily_balance['日付'], daily_balance['在高合計金額_百万円'], marker='o')
                    ax.set_xlabel('日付')
                    ax.set_ylabel('在高金額（百万円）')
                    
                    # Y軸のフォーマットを設定
                    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
                    
                    # X軸の日付フォーマットを設定
                    plt.xticks(daily_balance['日付'], 
                             [f"{d.strftime('%m/%d')}({w})" for d, w in zip(daily_balance['日付'], daily_balance['曜日'])],
                             rotation=45)
                    plt.grid(True)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                    
                    # データソースの説明
                    st.markdown(f"""
                    **データソース**:
                    - 対象データ: ATM現金入金取引データ
                    - 集計期間: {selected_month.strftime('%Y年%m月')}
                    - 集計項目: 在高合計金額
                    - 集計方法: 日別平均在高金額（百万円単位）
                    """)
        
        except Exception as e:
            st.error(f"データの表示中にエラーが発生しました: {str(e)}")
            print(f"エラーの詳細: {str(e)}")
            if not self.branch_data:
                st.warning("データが読み込まれていません。デモデータを使用します。")
                self.create_demo_data()

    def show_money_analysis(self):
        """金種分析ページの表示"""
        st.title('金種別分析')
        
        try:
            # データが存在しない場合はデモデータを作成
            if not self.branch_data:
                st.warning("データが読み込まれていません。デモデータを使用します。")
                self.create_demo_data()
            
            # 支店選択
            branch_codes = list(self.branch_data.keys())
            if not branch_codes:
                st.error("利用可能な支店データがありません。")
                return
                
            selected_branch = st.selectbox(
                '支店を選択してください',
                branch_codes
            )
            
            if selected_branch in self.branch_data:
                data = self.branch_data[selected_branch]
                df = data['atm_df']
                
                # 月選択
                available_months = df['日付'].dt.to_period('M').unique()
                if len(available_months) == 0:
                    st.error("選択された支店の月別データがありません。")
                    return
                    
                selected_month = st.selectbox(
                    '月を選択してください',
                    available_months,
                    format_func=lambda x: f"{x.year}年{x.month}月"
                )
                
                # 選択された月のデータでフィルタリング
                df_filtered = df[df['日付'].dt.to_period('M') == selected_month]
                
                if len(df_filtered) == 0:
                    st.warning(f"選択された月（{selected_month}）のデータがありません。")
                    return
                
                # 表示する金種の選択
                money_type = st.radio('金種タイプ', ['紙幣', '硬貨'])
                
                if money_type == '紙幣':
                    cols = data['bill_cols']
                    title = '紙幣種別の推移'
                    labels = {col: f"{col.split('（')[2].split('円')[0]}円札" for col in cols}
                else:
                    cols = data['coin_cols']
                    title = '硬貨種別の推移'
                    labels = {col: f"{col.split('（')[2].split('円')[0]}円玉" for col in cols}
                
                if not cols:
                    st.warning(f'{money_type}のデータが見つかりません。')
                    return
                
                # 金種別推移グラフ
                st.subheader(title)
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # 日付と曜日でグループ化してプロット
                df_filtered['date_str'] = df_filtered['日付'].dt.strftime('%m/%d') + '(' + df_filtered['曜日'] + ')'
                for col in cols:
                    daily_values = df_filtered.groupby('date_str')[col].mean()
                    ax.plot(daily_values.index, daily_values.values, label=labels[col], marker='o')
                
                ax.set_xlabel('日付')
                ax.set_ylabel('枚数')
                ax.legend()
                plt.xticks(rotation=45)
                plt.grid(True)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
                
                # データソースの説明
                st.markdown(f"""
                **データソース**:
                - 対象データ: ATM現金入金取引データ
                - 集計期間: {selected_month.strftime('%Y年%m月')}のデータ
                - 集計項目: 各金種の入金枚数
                - 集計方法: 日付ごとの平均入金枚数
                """)
                
                # 時間帯別ヒートマップ
                st.subheader(f'時間帯別{money_type}取扱枚数')
                
                # 時刻を時間に変換
                df_filtered['hour'] = pd.to_datetime(df_filtered['時刻'].astype(str)).dt.hour
                
                for col in cols:
                    pivot_data = df_filtered.pivot_table(
                        values=col,
                        index='hour',
                        columns='date_str',
                        aggfunc='mean'
                    ).round(1)
                    
                    fig, ax = plt.subplots(figsize=(15, 8))
                    sns.heatmap(pivot_data, cmap='YlOrRd', annot=True, fmt='.1f',
                              cbar_kws={'label': '平均枚数'})
                    plt.title(f'{labels[col]}の時間帯別平均取扱枚数')
                    plt.xlabel('日付')
                    plt.ylabel('時間帯')
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                    
                    # ヒートマップのデータソース説明
                    st.markdown(f"""
                    **データソース（{labels[col]}の時間帯別平均取扱枚数）**:
                    - 対象データ: ATM現金入金取引データ
                    - 集計期間: {selected_month.strftime('%Y年%m月')}のデータ
                    - 集計項目: {labels[col]}の入金枚数
                    - 集計方法: 
                        - 時間帯（0-23時）ごとの平均入金枚数
                        - 日付別・時間帯別の集計値
                        - 小数点以下1桁まで表示
                    - 表示形式: ヒートマップ（色が濃いほど取扱枚数が多いことを示す）
                    """)
        
        except Exception as e:
            st.error(f"データの表示中にエラーが発生しました: {str(e)}")
            print(f"エラーの詳細: {str(e)}")
            if not self.branch_data:
                st.warning("データが読み込まれていません。デモデータを使用します。")
                self.create_demo_data()

    def show_comparison(self):
        """支店間比較ページの表示"""
        st.title('支店間比較')
        
        try:
            # データが存在しない場合はデモデータを作成
            if not self.branch_data:
                st.warning("データが読み込まれていません。デモデータを使用します。")
                self.create_demo_data()
            
            if not self.branch_data:
                st.error("比較可能な支店データがありません。")
                return
            
            # 月選択
            first_branch_data = next(iter(self.branch_data.values()))
            available_months = first_branch_data['atm_df']['日付'].dt.to_period('M').unique()
            
            if len(available_months) == 0:
                st.error("利用可能な月別データがありません。")
                return
                
            selected_month = st.selectbox(
                '月を選択してください',
                available_months,
                format_func=lambda x: f"{x.year}年{x.month}月"
            )
            
            # 2列のレイアウトを作成
            col1, col2 = st.columns(2)
            
            with col1:
                # 取引件数の比較
                st.subheader('取引件数の比較')
                transaction_counts = {}
                for code, data in self.branch_data.items():
                    df_filtered = data['atm_df'][data['atm_df']['日付'].dt.to_period('M') == selected_month]
                    transaction_counts[code] = len(df_filtered)
                
                if not transaction_counts:
                    st.warning("選択された月のデータがありません。")
                    return
                
                # 取引件数の最大値と最小値を取得して色の濃淡を計算
                max_count = max(transaction_counts.values())
                min_count = min(transaction_counts.values())
                if max_count != min_count:
                    colors = [(count - min_count) / (max_count - min_count) for count in transaction_counts.values()]
                else:
                    colors = [0.5] * len(transaction_counts)
                
                fig, ax = plt.subplots(figsize=(6, 4))
                bars = ax.bar(transaction_counts.keys(), transaction_counts.values())
                
                # 各バーに色を設定
                for bar, color in zip(bars, colors):
                    bar.set_color(plt.cm.Blues(0.3 + color * 0.5))  # 青の濃淡
                
                ax.set_xlabel('支店コード')
                ax.set_ylabel('取引件数')
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
                
                # データソースの説明
                st.markdown(f"""
                **データソース（取引件数）**:
                - 対象データ: ATM現金入金取引データ
                - 集計期間: {selected_month.strftime('%Y年%m月')}
                - 集計方法: 支店ごとの総取引件数
                """)
            
            with col2:
                # 平均在高金額の比較
                st.subheader('平均在高金額の比較')
                avg_balances = {}
                for code, data in self.branch_data.items():
                    df_filtered = data['atm_df'][data['atm_df']['日付'].dt.to_period('M') == selected_month]
                    # 百万円単位に変換
                    avg_balances[code] = df_filtered['在高合計金額'].mean() / 1_000_000
                
                if not avg_balances:
                    st.warning("選択された月のデータがありません。")
                    return
                
                # 平均在高金額の最大値と最小値を取得して色の濃淡を計算
                max_balance = max(avg_balances.values())
                min_balance = min(avg_balances.values())
                if max_balance != min_balance:
                    colors = [(balance - min_balance) / (max_balance - min_balance) for balance in avg_balances.values()]
                else:
                    colors = [0.5] * len(avg_balances)
                
                fig, ax = plt.subplots(figsize=(6, 4))
                bars = ax.bar(avg_balances.keys(), avg_balances.values())
                
                # 各バーに色を設定
                for bar, color in zip(bars, colors):
                    bar.set_color(plt.cm.Greens(0.3 + color * 0.5))  # 緑の濃淡
                
                ax.set_xlabel('支店コード')
                ax.set_ylabel('平均在高金額（百万円）')
                
                # Y軸のフォーマットを設定（カンマ区切りの整数表示）
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
                
                # データソースの説明
                st.markdown(f"""
                **データソース（平均在高金額）**:
                - 対象データ: ATM現金入金取引データ
                - 集計期間: {selected_month.strftime('%Y年%m月')}
                - 集計方法: 支店ごとの平均在高金額（百万円単位）
                """)
        
        except Exception as e:
            st.error(f"データの表示中にエラーが発生しました: {str(e)}")
            print(f"エラーの詳細: {str(e)}")
            if not self.branch_data:
                st.warning("データが読み込まれていません。デモデータを使用します。")
                self.create_demo_data()

    def create_denomination_analysis(self, selected_branch, selected_month):
        """金種別分析を作成"""
        # データのフィルタリング
        df = self.branch_data[selected_branch]['atm_df']
        if selected_month != 'すべて':
            month_date = datetime.strptime(selected_month, '%Y年%m月')
            df = df[(df['日付'].dt.year == month_date.year) & 
                   (df['日付'].dt.month == month_date.month)]

        # 紙幣と硬貨の種別
        bill_types = ['10000', '5000', '2000', '1000']
        coin_types = ['500', '100', '50', '10', '5', '1']

        st.subheader('金種別分析')
        
        # 支店選択
        st.write('支店を選択してください')
        branch = st.selectbox('', list(self.branch_data.keys()), key='branch_selector')
        
        # 月選択
        st.write('月を選択してください')
        month_options = ['すべて'] + sorted(self.branch_data[branch]['atm_df']['日付'].dt.strftime('%Y年%m月').unique().tolist())
        month = st.selectbox('', month_options, key='month_selector')
        
        # 金種タイプの選択（紙幣/硬貨）
        st.write('金種タイプ')
        denomination_type = st.radio('', ['紙幣', '硬貨'])

        if denomination_type == '紙幣':
            # 紙幣の推移グラフ
            st.subheader('紙幣種別の推移')
            fig, ax = plt.subplots(figsize=(15, 6))
            
            for bill in bill_types:
                col = f'ATM現金（手入力以外）入金（{bill}円）枚数'
                if col in df.columns:
                    # 日付と曜日を結合
                    df['date_str'] = df['日付'].dt.strftime('%Y-%m-%d') + '(' + df['曜日'].str[0] + ')'
                    daily_avg = df.groupby('date_str')[col].mean()
                    ax.plot(daily_avg.index, daily_avg.values, marker='o', label=f'{bill}円札')
            
            plt.title(f'紙幣種別の日次推移 - {selected_branch}')
            plt.xlabel('日付')
            plt.ylabel('平均枚数')
            plt.grid(True)
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
            # 紙幣の時間帯別ヒートマップ
            st.subheader('紙幣種別の時間帯別平均取扱枚数')
            for bill in bill_types:
                col = f'ATM現金（手入力以外）入金（{bill}円）枚数'
                if col in df.columns:
                    # 時刻を時間に変換
                    df['時間'] = pd.to_datetime(df['時刻'].astype(str)).dt.hour
                    pivot_data = df.pivot_table(
                        values=col,
                        index='時間',
                        columns='date_str',
                        aggfunc='mean'
                    ).round(1)
                    
                    fig, ax = plt.subplots(figsize=(15, 8))
                    sns.heatmap(pivot_data, cmap='YlOrRd', annot=True, fmt='.1f', 
                              cbar_kws={'label': '平均枚数'})
                    plt.title(f'{bill}円札の時間帯別平均取扱枚数')
                    plt.xlabel('日付')
                    plt.ylabel('時間帯')
                    plt.tight_layout()
                    st.pyplot(fig)
        
        else:
            # 硬貨の推移グラフ
            st.subheader('硬貨種別の推移')
            fig, ax = plt.subplots(figsize=(15, 6))
            
            for coin in coin_types:
                col = f'ATM現金（手入力以外）入金（{coin}円）枚数'
                if col in df.columns:
                    # 日付と曜日を結合
                    df['date_str'] = df['日付'].dt.strftime('%Y-%m-%d') + '(' + df['曜日'].str[0] + ')'
                    daily_avg = df.groupby('date_str')[col].mean()
                    ax.plot(daily_avg.index, daily_avg.values, marker='o', label=f'{coin}円玉')
            
            plt.title(f'硬貨種別の日次推移 - {selected_branch}')
            plt.xlabel('日付')
            plt.ylabel('平均枚数')
            plt.grid(True)
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

            # 硬貨種別の推移グラフのデータソース説明
            st.markdown("""
            **データソース（硬貨種別の推移）**:
            - 対象データ: ATM現金入金取引データ
            - 集計期間: 選択された月のデータ
            - 集計項目: 
                - 500円玉の入金枚数
                - 100円玉の入金枚数
                - 50円玉の入金枚数
                - 10円玉の入金枚数
                - 5円玉の入金枚数
                - 1円玉の入金枚数
            - 集計方法: 日付ごとの各硬貨種別の平均入金枚数
            """)
            
            # 硬貨の時間帯別ヒートマップ
            st.subheader('硬貨種別の時間帯別平均取扱枚数')
            for coin in coin_types:
                col = f'ATM現金（手入力以外）入金（{coin}円）枚数'
                if col in df.columns:
                    # 時刻を時間に変換
                    df['時間'] = pd.to_datetime(df['時刻'].astype(str)).dt.hour
                    pivot_data = df.pivot_table(
                        values=col,
                        index='時間',
                        columns='date_str',
                        aggfunc='mean'
                    ).round(1)
                    
                    fig, ax = plt.subplots(figsize=(15, 8))
                    sns.heatmap(pivot_data, cmap='YlOrRd', annot=True, fmt='.1f',
                              cbar_kws={'label': '平均枚数'})
                    plt.title(f'{coin}円玉の時間帯別平均取扱枚数')
                    plt.xlabel('日付')
                    plt.ylabel('時間帯')
                    plt.tight_layout()
                    st.pyplot(fig)

                    # 各硬貨のヒートマップのデータソース説明
                    st.markdown(f"""
                    **データソース（{coin}円玉の時間帯別平均取扱枚数）**:
                    - 対象データ: ATM現金入金取引データ
                    - 集計期間: 選択された月のデータ
                    - 集計項目: {coin}円玉の入金枚数
                    - 集計方法: 
                        - 時間帯（0-23時）ごとの平均入金枚数
                        - 日付別・時間帯別の集計値
                        - 小数点以下1桁まで表示
                    - 表示形式: ヒートマップ（色が濃いほど取扱枚数が多いことを示す）
                    """)

    def create_demo_data(self):
        """デモデータの作成"""
        print("デモデータを作成中...")
        
        # サンプルの支店コード
        branch_codes = ['00643', '00669', '00748', '00796']
        
        for code in branch_codes:
            # デモデータの作成
            dates = pd.date_range(start='2023-11-01', end='2024-01-31')
            n_rows = len(dates)
            
            # 基本データの作成
            df = pd.DataFrame({
                '日付': dates,
                '時刻': [pd.to_datetime(f"{np.random.randint(8, 22):02d}:00:00").time() for _ in range(n_rows)],
                '在高合計金額': np.random.randint(1000000, 10000000, n_rows),
                'ATM現金入金計金額': np.random.randint(0, 1000000, n_rows)
            })
            
            # 曜日の追加
            df['曜日'] = df['日付'].dt.day_name().map(WEEKDAY_MAP)
            
            # 金種データの追加（より現実的な分布に）
            for bill in self.bills.keys():
                col_name = f'ATM現金（手入力以外）入金（{bill}円）枚数'
                if bill == '10000':
                    df[col_name] = np.random.poisson(30, n_rows)  # 10000円札は比較的多い
                elif bill == '5000':
                    df[col_name] = np.random.poisson(20, n_rows)
                else:
                    df[col_name] = np.random.poisson(10, n_rows)
            
            for coin in self.coins.keys():
                col_name = f'ATM現金（手入力以外）入金（{coin}円）枚数'
                if coin in ['100', '500']:
                    df[col_name] = np.random.poisson(100, n_rows)  # 100円玉と500円玉は多い
                elif coin in ['50', '10']:
                    df[col_name] = np.random.poisson(50, n_rows)
                else:
                    df[col_name] = np.random.poisson(20, n_rows)
            
            # 金種の列を特定
            bill_cols = [f'ATM現金（手入力以外）入金（{bill}円）枚数' for bill in self.bills.keys()]
            coin_cols = [f'ATM現金（手入力以外）入金（{coin}円）枚数' for coin in self.coins.keys()]
            
            self.branch_data[code] = {
                'atm_df': df,
                'bill_cols': bill_cols,
                'coin_cols': coin_cols
            }
            
            print(f"支店{code}のデモデータを作成しました")

    def run(self):
        """ダッシュボードを実行"""
        try:
            # データの存在確認
            if not self.branch_data:
                print("データが存在しないため、デモデータを作成します")
                self.create_demo_data()
            
            # 利用可能な支店コードの確認
            available_branches = list(self.branch_data.keys())
            if not available_branches:
                st.error("利用可能な支店データがありません。")
                return
            
            print(f"利用可能な支店: {available_branches}")
            
            # ページに応じた表示
            if self.page == '概要':
                print("概要ページを表示します")
                self.show_overview()
            elif self.page == '金種別分析':
                print("金種別分析ページを表示します")
                self.show_money_analysis()
            elif self.page == '支店間比較':
                print("支店間比較ページを表示します")
                self.show_comparison()
            else:
                print(f"不明なページが選択されました: {self.page}")
                st.error("無効なページが選択されました。")
                
        except Exception as e:
            print(f"実行時エラー: {str(e)}")
            st.error(f"エラーが発生しました: {str(e)}")
            
            # エラー発生時にデモデータを使用
            try:
                print("デモデータでの再試行を開始します")
                self.create_demo_data()
                
                if self.page == '概要':
                    self.show_overview()
                elif self.page == '金種別分析':
                    self.show_money_analysis()
                elif self.page == '支店間比較':
                    self.show_comparison()
                    
            except Exception as e2:
                print(f"デモデータでの実行時エラー: {str(e2)}")
                st.error("デモデータでの表示にも失敗しました。")

def main():
    try:
        print("アプリケーションを起動します")
        
        # ページ設定
        st.set_page_config(
            page_title='ATM運用分析ダッシュボード',
            page_icon='💹',
            layout='wide'
        )
        
        # グローバルなフォント設定
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
        
        # セッションステートの初期化
        if 'initialized' not in st.session_state:
            print("セッションステートを初期化します")
            st.session_state.initialized = True
            st.session_state.page = '概要'
            print("セッションステートを初期化しました")
        
        print("ダッシュボードを初期化します")
        dashboard = ATMDashboard()
        print("ダッシュボードの実行を開始します")
        dashboard.run()
        
    except Exception as e:
        print(f"アプリケーション起動時エラー: {str(e)}")
        st.error(f"アプリケーションの起動中にエラーが発生しました: {str(e)}")
        
        try:
            print("デモデータでの再試行を開始します")
            dashboard = ATMDashboard()
            dashboard.create_demo_data()
            dashboard.run()
        except Exception as e2:
            print(f"デモデータ実行時のエラー: {str(e2)}")
            st.error("アプリケーションの起動に失敗しました。管理者に連絡してください。")

if __name__ == "__main__":
    main() 