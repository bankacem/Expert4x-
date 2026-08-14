#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام الاختبار الخلفي متعدد الأصول والوساطات (Forex, Stocks, Bonds)
يختبر أداء الأداة على البيانات الحقيقية (2020 - 2026) لمختلف الأصول والمنصات/الوسطاء
"""

import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from itertools import product

class MultiAssetBacktester:
    def __init__(self, data_dir='backtesting/forex_data', results_dir='backtesting/results'):
        self.data_dir = data_dir
        self.results_dir = results_dir

        # تصنيف الأصول
        self.assets = {
            'FOREX': {
                'EURUSD': {'ticker': 'EURUSD=X', 'type': 'forex', 'point': 0.0001, 'contract_size': 100000},
                'GBPUSD': {'ticker': 'GBPUSD=X', 'type': 'forex', 'point': 0.0001, 'contract_size': 100000},
                'USDJPY': {'ticker': 'USDJPY=X', 'type': 'forex', 'point': 0.01,   'contract_size': 100000}
            },
            'STOCKS': {
                'AAPL': {'ticker': 'AAPL', 'type': 'stock', 'point': 0.01, 'contract_size': 100},
                'NVDA': {'ticker': 'NVDA', 'type': 'stock', 'point': 0.01, 'contract_size': 100},
                'SPY':  {'ticker': 'SPY',  'type': 'stock', 'point': 0.01, 'contract_size': 100}
            },
            'BONDS': {
                'TLT': {'ticker': 'TLT', 'type': 'bond', 'point': 0.01, 'contract_size': 100}, # سندات الخزانة طويلة الأجل
                'IEF': {'ticker': 'IEF', 'type': 'bond', 'point': 0.01, 'contract_size': 100}, # سندات الخزانة متوسطة الأجل
                'BND': {'ticker': 'BND', 'type': 'bond', 'point': 0.01, 'contract_size': 100}  # مؤشر السندات الشامل
            }
        }

        # بروفايلات الوساطة والسرعة والسبريد
        self.broker_profiles = {
            'ECN_RAW_ULTRA_FAST': {
                'name': 'حساب ECN الخام (أسرع تنفيذ + أقل سبريد)',
                'spread_pips_forex': 0.1,    # سبريد شبه معدوم
                'spread_pips_stock': 0.02,   # 2 سنت
                'commission_per_lot': 7.0,   # $7 لكل لوت دورة كاملة
                'slippage_pips': 0.0
            },
            'STANDARD_PRO': {
                'name': 'حساب قياسي احترافي (Standard Pro)',
                'spread_pips_forex': 1.0,    # 1 نقطة
                'spread_pips_stock': 0.05,   # 5 سنتات
                'commission_per_lot': 0.0,
                'slippage_pips': 0.2
            },
            'HIGH_SPREAD_SLOW': {
                'name': 'وسيط تقليدي بطيء / سبريد مرتفع',
                'spread_pips_forex': 2.5,    # 2.5 نقطة
                'spread_pips_stock': 0.15,   # 15 سنت
                'commission_per_lot': 10.0,
                'slippage_pips': 0.5
            }
        }

        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

    def download_data(self, start_date='2020-01-01', end_date='2026-08-14'):
        """
        تحميل بيانات الأصول الحقيقية من Yahoo Finance
        """
        print(f"\n🔄 جاري تحميل بيانات جميع الأصول (2020 - 2026)...")
        downloaded = {}

        for category, symbols in self.assets.items():
            for symbol, info in symbols.items():
                filename = os.path.join(self.data_dir, f"{symbol}_D1_2020_2026.csv")
                if os.path.exists(filename):
                    df = pd.read_csv(filename, index_col=0, parse_dates=True)
                    downloaded[symbol] = len(df)
                    print(f"   • {category} - {symbol}: موجود محلياً ({len(df)} يوم).")
                    continue

                print(f"   • تحميل {category} - {symbol} ({info['ticker']})...", end=' ')
                try:
                    df = yf.download(info['ticker'], start=start_date, end=end_date, interval='1d', progress=False)
                    if df.empty:
                        print("❌ لا توجد بيانات!")
                        continue

                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    df = df.dropna()
                    df.to_csv(filename)
                    downloaded[symbol] = len(df)
                    print(f"✅ تم تحميل {len(df)} يوم.")
                except Exception as e:
                    print(f"❌ خطأ: {str(e)}")

        return downloaded

    def calculate_indicators(self, df):
        """
        حساب المؤشرات الفنية للتحليل
        """
        df = df.copy()

        # 1. RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        loss = loss.replace(0, 1e-10)
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 2. MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # 3. Bollinger Bands
        df['BB_Mid'] = df['Close'].rolling(window=20).mean()
        df['BB_Std'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)

        return df.dropna()

    def run_backtest_asset(self, symbol, asset_info, broker_key='ECN_RAW_ULTRA_FAST', custom_settings=None):
        """
        اختبار خلفي للأصل بناءً على مواصفاته ونوع الحساب والوسيط
        """
        filename = os.path.join(self.data_dir, f"{symbol}_D1_2020_2026.csv")
        if not os.path.exists(filename):
            return None

        df_raw = pd.read_csv(filename, index_col=0, parse_dates=True)
        df = self.calculate_indicators(df_raw)

        broker = self.broker_profiles[broker_key]

        # ضبط الإعدادات الموصى بها حسب نوع الأصل
        asset_type = asset_info['type']
        point = asset_info['point']

        if custom_settings:
            settings = custom_settings
        else:
            if asset_type == 'forex':
                settings = {'tp_pips': 50, 'sl_pips': 100, 'rsi_os': 30, 'rsi_ob': 70, 'lot_size': 0.1}
            elif asset_type == 'stock':
                settings = {'tp_pips': 200, 'sl_pips': 300, 'rsi_os': 35, 'rsi_ob': 65, 'lot_size': 0.1}
            else: # bond
                settings = {'tp_pips': 100, 'sl_pips': 150, 'rsi_os': 30, 'rsi_ob': 70, 'lot_size': 0.1}

        initial_balance = 10000.0
        balance = initial_balance
        max_balance = balance
        min_balance = balance
        position = None
        entry_price = 0.0
        trades_count = 0
        winning_trades = 0
        losing_trades = 0

        # تحديد تكلفة السبريد والعمولة
        if asset_type == 'forex':
            spread = broker['spread_pips_forex'] * point
            pip_usd_value = settings['lot_size'] * 10.0 # لوت 0.1 = $1 لكل نقطة في الفوركس
        else: # stock & bond
            spread = broker['spread_pips_stock']
            # للأسهم والسندات 0.1 لوت يعبر عن 10 أسهم، كل 1 دولار تغير في السعر = $10 ربح/خسارة
            pip_usd_value = settings['lot_size'] * 100.0

        commission = broker['commission_per_lot'] * settings['lot_size']
        slippage = broker['slippage_pips'] * point

        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values
        rsis = df['RSI'].values
        macd_hists = df['MACD_Histogram'].values

        for i in range(1, len(df)):
            close_price = closes[i]
            high_price = highs[i]
            low_price = lows[i]
            rsi = rsis[i]
            macd_hist = macd_hists[i]
            prev_macd_hist = macd_hists[i-1]

            if position is not None:
                tp_pips = settings['tp_pips']
                sl_pips = settings['sl_pips']

                if position == 'buy':
                    tp_price = entry_price + (tp_pips * point)
                    sl_price = entry_price - (sl_pips * point)

                    if low_price <= sl_price:
                        loss = (sl_pips * point / point) * (pip_usd_value if asset_type == 'forex' else pip_usd_value * point) + commission
                        balance -= loss
                        losing_trades += 1
                        position = None

                    elif high_price >= tp_price and position is not None:
                        profit = (tp_pips * point / point) * (pip_usd_value if asset_type == 'forex' else pip_usd_value * point) - commission
                        balance += profit
                        winning_trades += 1
                        position = None

                elif position == 'sell':
                    tp_price = entry_price - (tp_pips * point)
                    sl_price = entry_price + (sl_pips * point)

                    if high_price >= sl_price:
                        loss = (sl_pips * point / point) * (pip_usd_value if asset_type == 'forex' else pip_usd_value * point) + commission
                        balance -= loss
                        losing_trades += 1
                        position = None

                    elif low_price <= tp_price and position is not None:
                        profit = (tp_pips * point / point) * (pip_usd_value if asset_type == 'forex' else pip_usd_value * point) - commission
                        balance += profit
                        winning_trades += 1
                        position = None

            if position is None:
                # إشارات الدخول المعززة بالظروف السعرية والسبريد
                if rsi < settings['rsi_os'] and macd_hist > 0 and prev_macd_hist <= 0:
                    position = 'buy'
                    entry_price = close_price + (spread / 2) + slippage
                    trades_count += 1

                elif rsi > settings['rsi_ob'] and macd_hist < 0 and prev_macd_hist >= 0:
                    position = 'sell'
                    entry_price = close_price - (spread / 2) - slippage
                    trades_count += 1

            max_balance = max(max_balance, balance)
            min_balance = min(min_balance, balance)

        profit_loss = balance - initial_balance
        roi = (profit_loss / initial_balance) * 100.0
        max_dd = ((max_balance - min_balance) / max_balance) * 100.0 if max_balance > 0 else 0.0
        win_rate = (winning_trades / trades_count * 100.0) if trades_count > 0 else 0.0

        return {
            'symbol': symbol,
            'asset_type': asset_type,
            'broker_profile': broker['name'],
            'initial_balance': initial_balance,
            'final_balance': round(balance, 2),
            'profit_loss': round(profit_loss, 2),
            'roi_percent': round(roi, 2),
            'total_trades': trades_count,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_percent': round(win_rate, 2),
            'max_drawdown_percent': round(max_dd, 2)
        }

    def run_all_tests(self):
        """
        تشغيل كافة التقييمات عبر جميع الأصول وبروفايلات الوسطاء
        """
        self.download_data()

        full_report = {}

        print("\n" + "="*85)
        print("📊 نتائج الاختبارات المتقدمة متعددة الأصول وبروفايلات الوسطاء (2020 - 2026)")
        print("="*85)

        for category, symbols in self.assets.items():
            full_report[category] = {}
            print(f"\n📌 أصول قسم: {category}")
            print("-" * 85)

            for symbol, info in symbols.items():
                full_report[category][symbol] = {}
                for b_key, b_info in self.broker_profiles.items():
                    res = self.run_backtest_asset(symbol, info, broker_key=b_key)
                    if res:
                        full_report[category][symbol][b_key] = res
                        print(f"   • {symbol:6s} | {b_info['name'][:30]:30s} | العائد: {res['roi_percent']:+6.2f}% | الربح: ${res['profit_loss']:+8.2f} | الفوز: {res['win_rate_percent']:5.1f}% | التراجع: {res['max_drawdown_percent']:4.1f}%")

        out_path = os.path.join(self.results_dir, "multiasset_report_2020_2026.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'report': full_report
            }, f, ensure_ascii=False, indent=2)

        print(f"\n✅ تم حفظ تقرير الأصول الشامل في: {out_path}")
        return full_report

if __name__ == "__main__":
    tester = MultiAssetBacktester()
    tester.run_all_tests()
