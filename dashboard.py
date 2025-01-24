import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime, timedelta
import japanize_matplotlib
import glob

class ATMDashboard:
    def __init__(self):
        self.base_dir = os.getcwd()
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
        self.load_data()
        self.setup_page()

    def load_data(self):
        """データの読み込み"""
        branch_codes = ['00512', '00524', '00525', '00609', '00616', 
                       '00643', '00669', '00748', '00796']
        
        # 曜日の変換辞書を追加
        weekday_map = {
            'Monday': '月',
            'Tuesday': '火',
            'Wednesday': '水',
            'Thursday': '木',
            'Friday': '金',
            'Saturday': '土',
            'Sunday': '日'
        }
        
        for code in branch_codes:
            try:
                # ATM精算データ
                atm_files = [f for f in os.listdir(self.base_dir) if f.startswith(f"{code}_ATM精算")]
                if atm_files:
                    atm_path = os.path.join(self.base_dir, atm_files[0])
                    print(f"読み込むファイル: {atm_path}")
                    atm_df = pd.read_csv(atm_path, encoding='cp932')
                    print("列名一覧:", atm_df.columns.tolist())
                    
                    atm_df['日付'] = pd.to_datetime(atm_df['日付'].astype(str), format='%Y%m%d')
                    atm_df['曜日'] = atm_df['日付'].dt.day_name().map(weekday_map)
                    atm_df['時刻'] = pd.to_datetime(atm_df['時刻'].astype(str).str.zfill(6), format='%H%M%S').dt.time
                    
                    # 金種データの列を特定
                    bill_cols = []
                    coin_cols = []
                    
                    # 紙幣の列を検索（スペースを考慮）
                    for bill_value in self.bills.keys():
                        patterns = [
                            f'ATM現金（手入力以外）入金（{bill_value}円）枚数',
                            f'ATM現金（手入力以外）入金（{bill_value}円） 枚数',
                            f'ATM現金（手入力以外）入金（{bill_value}円）枚数 ',
                            f'ATM現金（手入力以外）入金（{bill_value}円） 枚数 '
                        ]
                        
                        for pattern in patterns:
                            matching_cols = [col for col in atm_df.columns if col.replace(' ', '') == pattern.replace(' ', '')]
                            if matching_cols:
                                bill_cols.extend(matching_cols)
                                break
                    
                    # 硬貨の列を検索
                    for coin_value in self.coins.keys():
                        patterns = [
                            f'ATM現金（手入力以外）入金（{coin_value}円）枚数',
                            f'ATM現金（手入力以外）入金（{coin_value}円） 枚数',
                            f'ATM現金（手入力以外）入金（{coin_value}円）枚数 ',
                            f'ATM現金（手入力以外）入金（{coin_value}円） 枚数 '
                        ]
                        
                        for pattern in patterns:
                            matching_cols = [col for col in atm_df.columns if col.replace(' ', '') == pattern.replace(' ', '')]
                            if matching_cols:
                                coin_cols.extend(matching_cols)
                                break
                    
                    print(f"検出された紙幣の列: {bill_cols}")
                    print(f"検出された硬貨の列: {coin_cols}")
                    
                    self.branch_data[code] = {
                        'atm_df': atm_df,
                        'bill_cols': bill_cols,
                        'coin_cols': coin_cols
                    }
                    print(f"支店{code}のデータを読み込みました")
                    
            except Exception as e:
                print(f"エラーの詳細: {str(e)}")
                st.error(f"支店{code}のデータ読み込みでエラーが発生: {str(e)}")

    def setup_page(self):
        """ページの基本設定"""
        st.title('ATM取引分析ダッシュボード')
        st.sidebar.title('ページを選択')
        self.page = st.sidebar.selectbox('', ['概要', '金種別分析', '支店間比較'])
        
    def show_overview(self):
        """概要ページの表示"""
        st.title('ATM運用分析ダッシュボード')
        
        # 支店選択
        selected_branch = st.selectbox(
            '支店を選択してください',
            list(self.branch_data.keys())
        )
        
        if selected_branch in self.branch_data:
            data = self.branch_data[selected_branch]
            df = data['atm_df']
            
            # 月選択
            available_months = df['日付'].dt.to_period('M').unique()
            selected_month = st.selectbox(
                '月を選択してください',
                available_months,
                format_func=lambda x: f"{x.year}年{x.month}月"
            )
            
            # 選択された月のデータでフィルタリング
            df_filtered = df[df['日付'].dt.to_period('M') == selected_month]
            
            # 基本統計
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric('取引件数', f"{len(df_filtered):,}件")
            with col2:
                st.metric('平均在高金額', f"{df_filtered['在高合計金額'].mean():,.0f}円")
            with col3:
                st.metric('最大在高金額', f"{df_filtered['在高合計金額'].max():,.0f}円")
            
            # グラフを横並びに配置
            col_left, col_right = st.columns(2)
            
            with col_left:
                # 時間帯別取引数
                st.subheader('時間帯別ATM現金入金取引数')
                df_filtered['hour'] = pd.to_datetime(df_filtered['時刻'].astype(str), format='%H:%M:%S').dt.hour
                
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
                
                # データソースの説明
                st.markdown("""
                **データソース**:
                - ファイル: `{branch_code}_ATM精算POSレジ自動釣銭機確定データ.csv`
                - 使用項目: 
                    - `時刻`: 取引の発生時刻
                    - `ATM現金入金計金額`: ATMへの現金入金金額
                - 集計方法: 各時間帯でATM現金入金のあった取引数をカウント
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
                
                # X軸の日付フォーマットを設定（曜日を日本語一文字で表示）
                plt.xticks(daily_balance['日付'], [f"{d.strftime('%m/%d')}({w})" for d, w in zip(daily_balance['日付'], daily_balance['曜日'])], rotation=45)
                plt.grid(True)
                plt.tight_layout()
                st.pyplot(fig)
                
                # データソースの説明
                st.markdown("""
                **データソース**:
                - ファイル: `{branch_code}_ATM精算POSレジ自動釣銭機確定データ.csv`
                - 使用項目:
                    - `日付`: 取引日
                    - `在高合計金額`: ATM内の現金保有額の合計
                        - 内訳: 在高（10000円）枚数 × 10000円 + 在高（5000円）枚数 × 5000円 + ...
                              + 在高（1円）枚数 × 1円
                - 集計方法: 日付ごとの在高合計金額の平均値を算出（百万円単位で表示）
                """)

    def show_money_analysis(self):
        """金種分析ページの表示"""
        st.title('金種別分析')
        
        # 支店選択
        selected_branch = st.selectbox(
            '支店を選択してください',
            list(self.branch_data.keys())
        )
        
        if selected_branch in self.branch_data:
            data = self.branch_data[selected_branch]
            df = data['atm_df']
            
            # 月選択
            available_months = df['日付'].dt.to_period('M').unique()
            selected_month = st.selectbox(
                '月を選択してください',
                available_months,
                format_func=lambda x: f"{x.year}年{x.month}月"
            )
            
            # 選択された月のデータでフィルタリング
            df_filtered = df[df['日付'].dt.to_period('M') == selected_month]
            
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
            
            # 日付と曜日でグループ化してプロット（曜日を日本語一文字で表示）
            df_filtered['date_str'] = df_filtered['日付'].dt.strftime('%m/%d') + '(' + df_filtered['曜日'] + ')'
            for col in cols:
                daily_values = df_filtered.groupby('date_str')[col].mean()
                ax.plot(daily_values.index, daily_values.values, label=labels[col], marker='o')
            
            ax.set_xlabel('日付')
            ax.set_ylabel('枚数')
            ax.legend()
            plt.xticks(rotation=45)
            plt.grid(True)
            st.pyplot(fig)
            
            # データソースの説明
            st.markdown(f"""
            **データソース**:
            - ファイル: `{selected_branch}_ATM精算POSレジ自動釣銭機確定データ.csv`
            - 使用項目: 
                - 紙幣の場合:
                    - `ATM現金（手入力以外）入金（10000円）枚数`
                    - `ATM現金（手入力以外）入金（5000円）枚数`
                    - `ATM現金（手入力以外）入金（2000円）枚数`
                    - `ATM現金（手入力以外）入金（1000円）枚数`
                - 硬貨の場合:
                    - `ATM現金（手入力以外）入金（500円）枚数`
                    - `ATM現金（手入力以外）入金（100円）枚数`
                    - `ATM現金（手入力以外）入金（50円）枚数`
                    - `ATM現金（手入力以外）入金（10円）枚数`
                    - `ATM現金（手入力以外）入金（5円）枚数`
                    - `ATM現金（手入力以外）入金（1円）枚数`
            - 集計方法: 日付ごとの各金種の入金枚数の平均値を算出
            """)
            
            # 金種別箱ひげ図
            st.subheader(f'{money_type}種別の分布')
            fig, ax = plt.subplots(figsize=(12, 6))
            df_melt = df_filtered[cols].melt()
            df_melt['variable'] = df_melt['variable'].map(labels)
            sns.boxplot(data=df_melt, x='variable', y='value')
            plt.xticks(rotation=45)
            ax.set_xlabel(money_type)
            ax.set_ylabel('枚数')
            st.pyplot(fig)
            
            # 相関分析
            st.subheader(f'{money_type}種別の相関')
            if len(cols) > 1:
                corr = df_filtered[cols].corr()
                fig, ax = plt.subplots(figsize=(10, 8))
                mask = np.triu(np.ones_like(corr), k=1)
                sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, 
                          mask=mask, xticklabels=labels.values(), 
                          yticklabels=labels.values())
                plt.xticks(rotation=45)
                plt.yticks(rotation=0)
                st.pyplot(fig)
            else:
                st.warning(f'相関分析には2つ以上の{money_type}種別が必要です。')

    def show_comparison(self):
        """支店間比較ページの表示"""
        st.title('支店間比較')
        
        # 月選択
        first_branch_data = next(iter(self.branch_data.values()))
        available_months = first_branch_data['atm_df']['日付'].dt.to_period('M').unique()
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
            
            # 取引件数の最大値と最小値を取得して色の濃淡を計算
            max_count = max(transaction_counts.values())
            min_count = min(transaction_counts.values())
            colors = [(count - min_count) / (max_count - min_count) for count in transaction_counts.values()]
            
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
        
        with col2:
            # 平均在高金額の比較
            st.subheader('平均在高金額の比較')
            avg_balances = {}
            for code, data in self.branch_data.items():
                df_filtered = data['atm_df'][data['atm_df']['日付'].dt.to_period('M') == selected_month]
                # 百万円単位に変換
                avg_balances[code] = df_filtered['在高合計金額'].mean() / 1_000_000
            
            # 平均在高金額の最大値と最小値を取得して色の濃淡を計算
            max_balance = max(avg_balances.values())
            min_balance = min(avg_balances.values())
            colors = [(balance - min_balance) / (max_balance - min_balance) for balance in avg_balances.values()]
            
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

    def run(self):
        """ダッシュボードを実行"""
        if self.page == '概要':
            self.show_overview()
        elif self.page == '金種別分析':
            self.create_denomination_analysis(
                selected_branch=st.session_state.get('branch_selector', list(self.branch_data.keys())[0]),
                selected_month=st.session_state.get('month_selector', 'すべて')
            )
        else:
            self.show_comparison()

def main():
    st.set_page_config(
        page_title='ATM運用分析ダッシュボード',
        page_icon='💹',
        layout='wide'
    )
    
    dashboard = ATMDashboard()
    dashboard.run()

if __name__ == "__main__":
    main() 