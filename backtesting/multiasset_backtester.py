#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام الاختبار الخلفي متعدد الأصول والأسواق (Multi-Asset Backtester)
يدعم اختبار استراتيجية التداول على:
- العملات الرقمية (Crypto): BTC-USD, ETH-USD, SOL-USD
- فوركس (Forex): EURUSD, GBPUSD, USDJPY
- الأسهم الأمريكية (Stocks): AAPL, NVDA, TSLA, MSFT
- السلع والمعادن (Commodities): الذهب (GC=F), الفضة (SI=F), النفط (CL=F)

مع محاكاة حسابية لفروق الأسعار (Spreads) والعمولات وفقاً لبروفايلات الوسطاء (ECN Raw, Standard, High Spread).
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class MultiAssetDataFetcher:
    """
    جلب وتحضير البيانات التاريخية لمختلف الأصول مع دعم محاكاة البيانات في حالة عدم توفر الاتصال
    """
    def __init__(self, data_dir='backtesting/forex_data'):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_data(self, symbol, ticker, period='2y', interval='1d'):
        """
        جلب البيانات التاريخية بواسطة yfinance أو التوليد الاصطناعي
        """
        filename = os.path.join(self.data_dir, f"{symbol}_multiasset.csv")

        df = None
        if YFINANCE_AVAILABLE:
            try:
                print(f"   • جاري تحميل بيانات {symbol} ({ticker}) عبر Yahoo Finance...", end=' ')
                data = yf.download(ticker, period=period, interval=interval, progress=False)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                    df = data.dropna()
                    df.to_csv(filename)
                    print(f"✅ تم تحميل {len(df)} شمعة.")
            except Exception as e:
                print(f"⚠️ فشل التحميل ({str(e)}), سيتم الانتقال للبديل المحلي/الاصطناعي.")

        if df is None or df.empty:
            if os.path.exists(filename):
                df = pd.read_csv(filename, index_col=0, parse_dates=True)
                print(f"   • استخدام الملف المحلي لـ {symbol} ({len(df)} شمعة).")
            else:
                df = self._generate_synthetic_data(symbol)
                df.to_csv(filename)
                print(f"   • تم توليد بيانات محاكاة واقعية لـ {symbol} ({len(df)} شمعة).")

        return df

    def _generate_synthetic_data(self, symbol, num_days=500):
        """
        توليد بيانات أسعار محاكاة واقعية للغاية للأصول المختلفة
        """
        base_prices = {
            'BTC-USD': 60000.0, 'ETH-USD': 3000.0, 'SOL-USD': 140.0,
            'EURUSD': 1.0850, 'GBPUSD': 1.2800, 'USDJPY': 155.00,
            'AAPL': 220.0, 'NVDA': 120.0, 'TSLA': 210.0, 'MSFT': 440.0,
            'GOLD': 2400.0, 'SILVER': 28.5, 'CRUDE_OIL': 75.0
        }
        volatility = {
            'BTC-USD': 0.035, 'ETH-USD': 0.040, 'SOL-USD': 0.050,
            'EURUSD': 0.005, 'GBPUSD': 0.006, 'USDJPY': 0.007,
            'AAPL': 0.018, 'NVDA': 0.030, 'TSLA': 0.035, 'MSFT': 0.015,
            'GOLD': 0.012, 'SILVER': 0.020, 'CRUDE_OIL': 0.025
        }

        start_price = base_prices.get(symbol, 100.0)
        vol = volatility.get(symbol, 0.02)

        np.random.seed(hash(symbol) % 100000)
        returns = np.random.normal(0.0003, vol, num_days)
        price_path = start_price * np.exp(np.cumsum(returns))

        end_date = datetime.now()
        dates = [end_date - timedelta(days=num_days - i) for i in range(num_days)]

        df = pd.DataFrame({
            'Date': dates,
            'Open': price_path * (1 - np.random.uniform(0, 0.002, num_days)),
            'High': price_path * (1 + np.abs(np.random.normal(0, 0.008, num_days))),
            'Low': price_path * (1 - np.abs(np.random.normal(0, 0.008, num_days))),
            'Close': price_path,
            'Volume': np.random.randint(10000, 1000000, num_days)
        })
        df.set_index('Date', inplace=True)
        return df


class MultiAssetBacktester:
    """
    مختبر الأصول المتعددة لجميع الفئات المالية البروفايلات المختلفة للوسطاء
    """

    # بروفايلات التنفيذ لدى الوسطاء
    BROKER_PROFILES = {
        'ECN_RAW': {'spread_multiplier': 0.5, 'commission_per_trade_usd': 3.5},
        'STANDARD': {'spread_multiplier': 1.0, 'commission_per_trade_usd': 0.0},
        'HIGH_SPREAD': {'spread_multiplier': 2.0, 'commission_per_trade_usd': 0.0}
    }

    # الأصول المدعومة وتصنيفاتها
    ASSETS = {
        # Crypto
        'BTC-USD': {'name': 'Bitcoin', 'category': 'Crypto', 'ticker': 'BTC-USD', 'pip_value_pct': 0.001, 'spread_pips': 10},
        'ETH-USD': {'name': 'Ethereum', 'category': 'Crypto', 'ticker': 'ETH-USD', 'pip_value_pct': 0.001, 'spread_pips': 12},
        'SOL-USD': {'name': 'Solana', 'category': 'Crypto', 'ticker': 'SOL-USD', 'pip_value_pct': 0.001, 'spread_pips': 15},

        # Forex
        'EURUSD': {'name': 'EUR/USD', 'category': 'Forex', 'ticker': 'EURUSD=X', 'pip_value_pct': 0.0001, 'spread_pips': 1.2},
        'GBPUSD': {'name': 'GBP/USD', 'category': 'Forex', 'ticker': 'GBPUSD=X', 'pip_value_pct': 0.0001, 'spread_pips': 1.5},
        'USDJPY': {'name': 'USD/JPY', 'category': 'Forex', 'ticker': 'USDJPY=X', 'pip_value_pct': 0.01, 'spread_pips': 1.4},

        # Stocks
        'AAPL': {'name': 'Apple Inc.', 'category': 'Stocks', 'ticker': 'AAPL', 'pip_value_pct': 0.01, 'spread_pips': 2.0},
        'NVDA': {'name': 'NVIDIA Corp.', 'category': 'Stocks', 'ticker': 'NVDA', 'pip_value_pct': 0.01, 'spread_pips': 3.0},
        'TSLA': {'name': 'Tesla Inc.', 'category': 'Stocks', 'ticker': 'TSLA', 'pip_value_pct': 0.01, 'spread_pips': 3.5},
        'MSFT': {'name': 'Microsoft', 'category': 'Stocks', 'ticker': 'MSFT', 'pip_value_pct': 0.01, 'spread_pips': 2.0},

        # Commodities
        'GOLD': {'name': 'Gold Futures', 'category': 'Commodities', 'ticker': 'GC=F', 'pip_value_pct': 0.1, 'spread_pips': 3.0},
        'SILVER': {'name': 'Silver Futures', 'category': 'Commodities', 'ticker': 'SI=F', 'pip_value_pct': 0.01, 'spread_pips': 2.5},
        'CRUDE_OIL': {'name': 'Crude Oil', 'category': 'Commodities', 'ticker': 'CL=F', 'pip_value_pct': 0.01, 'spread_pips': 3.0}
    }

    def __init__(self, data_dir='backtesting/forex_data', results_dir='backtesting/results'):
        self.fetcher = MultiAssetDataFetcher(data_dir)
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

    def calculate_indicators(self, df):
        """
        حساب المؤشرات الفنية (RSI, MACD, Bollinger Bands)
        """
        df = df.copy()

        # 1. RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().replace(0, 1e-10)
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

    def run_single_backtest(self, symbol, broker_profile_name='STANDARD', initial_balance=10000):
        """
        تشغيل محاكاة اختبار لجنس/أصل معين وفق بروفايل وسيط محدد
        """
        asset_info = self.ASSETS[symbol]
        broker = self.BROKER_PROFILES[broker_profile_name]

        df_raw = self.fetcher.fetch_data(symbol, asset_info['ticker'])
        df = self.calculate_indicators(df_raw)

        balance = initial_balance
        position = None
        entry_price = 0
        trades_count = 0
        winning_trades = 0
        losing_trades = 0
        max_balance = balance
        min_balance = balance
        trades_list = []

        # حساب تكلفة السبريد الفعلية
        effective_spread = asset_info['spread_pips'] * broker['spread_multiplier'] * asset_info['pip_value_pct']
        commission = broker['commission_per_trade_usd']

        # قيم هدف الربح ووقف الخسارة بناء على تقلبات نوع الأصل
        if asset_info['category'] == 'Crypto':
            tp_pct, sl_pct = 0.04, 0.03
        elif asset_info['category'] == 'Forex':
            tp_pct, sl_pct = 0.01, 0.008
        elif asset_info['category'] == 'Stocks':
            tp_pct, sl_pct = 0.025, 0.02
        else:  # Commodities
            tp_pct, sl_pct = 0.02, 0.015

        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values
        rsis = df['RSI'].values
        macd_hists = df['MACD_Histogram'].values
        dates = df.index

        for i in range(1, len(df)):
            close_price = closes[i]
            high_price = highs[i]
            low_price = lows[i]
            rsi = rsis[i]
            macd_hist = macd_hists[i]
            prev_macd_hist = macd_hists[i-1]
            date_str = str(dates[i])[:10]

            # إغلاق ومتابعة الصفقة
            if position is not None:
                if position == 'buy':
                    tp_price = entry_price * (1 + tp_pct)
                    sl_price = entry_price * (1 - sl_pct)

                    if low_price <= sl_price:
                        # خسارة
                        pnl = -initial_balance * 0.02 - commission
                        balance += pnl
                        losing_trades += 1
                        trades_list.append({
                            'date': date_str, 'type': 'BUY', 'entry': entry_price,
                            'exit': sl_price, 'pnl': round(pnl, 2), 'result': 'LOSS'
                        })
                        position = None
                    elif high_price >= tp_price and position is not None:
                        # ربح
                        pnl = initial_balance * 0.02 * (tp_pct / sl_pct) - commission
                        balance += pnl
                        winning_trades += 1
                        trades_list.append({
                            'date': date_str, 'type': 'BUY', 'entry': entry_price,
                            'exit': tp_price, 'pnl': round(pnl, 2), 'result': 'WIN'
                        })
                        position = None

                elif position == 'sell':
                    tp_price = entry_price * (1 - tp_pct)
                    sl_price = entry_price * (1 + sl_pct)

                    if high_price >= sl_price:
                        pnl = -initial_balance * 0.02 - commission
                        balance += pnl
                        losing_trades += 1
                        trades_list.append({
                            'date': date_str, 'type': 'SELL', 'entry': entry_price,
                            'exit': sl_price, 'pnl': round(pnl, 2), 'result': 'LOSS'
                        })
                        position = None
                    elif low_price <= tp_price and position is not None:
                        pnl = initial_balance * 0.02 * (tp_pct / sl_pct) - commission
                        balance += pnl
                        winning_trades += 1
                        trades_list.append({
                            'date': date_str, 'type': 'SELL', 'entry': entry_price,
                            'exit': tp_price, 'pnl': round(pnl, 2), 'result': 'WIN'
                        })
                        position = None

            # إشارة دخول
            if position is None:
                # شراء
                if rsi < 35 and macd_hist > 0 and prev_macd_hist <= 0:
                    position = 'buy'
                    entry_price = close_price + (effective_spread / 2)
                    trades_count += 1
                # بيع
                elif rsi > 65 and macd_hist < 0 and prev_macd_hist >= 0:
                    position = 'sell'
                    entry_price = close_price - (effective_spread / 2)
                    trades_count += 1

            max_balance = max(max_balance, balance)
            min_balance = min(min_balance, balance)

        profit_loss = balance - initial_balance
        roi = (profit_loss / initial_balance) * 100
        max_dd = ((max_balance - min_balance) / max_balance) * 100 if max_balance > 0 else 0
        win_rate = (winning_trades / trades_count * 100) if trades_count > 0 else 0

        return {
            'symbol': symbol,
            'asset_name': asset_info['name'],
            'category': asset_info['category'],
            'broker_profile': broker_profile_name,
            'initial_balance': initial_balance,
            'final_balance': round(balance, 2),
            'profit_loss': round(profit_loss, 2),
            'roi_percent': round(roi, 2),
            'total_trades': trades_count,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_percent': round(win_rate, 2),
            'max_drawdown_percent': round(max_dd, 2),
            'trades_sample': trades_list[:5]
        }

    def run_all_assets_backtest(self, broker_profile='STANDARD'):
        """
        تشغيل اختبار خلفي شامل لجميع الفئات المالية الأربع
        """
        print(f"\n" + "═"*85)
        print(f"🌐 بدء الاختبار الشامل لجميع الأصول والأسواق (بروفايل الوسيط: {broker_profile})")
        print("═"*85)

        all_results = {}
        category_summary = {}

        for symbol in self.ASSETS.keys():
            res = self.run_single_backtest(symbol, broker_profile_name=broker_profile)
            all_results[symbol] = res

            cat = res['category']
            if cat not in category_summary:
                category_summary[cat] = {'total_pl': 0, 'trades': 0, 'wins': 0, 'count': 0}

            category_summary[cat]['total_pl'] += res['profit_loss']
            category_summary[cat]['trades'] += res['total_trades']
            category_summary[cat]['wins'] += res['winning_trades']
            category_summary[cat]['count'] += 1

            print(f"   [{res['category']:11}] {res['asset_name']:15} ({symbol:8}) | "
                  f"P&L: ${res['profit_loss']:+8.2f} | ROI: {res['roi_percent']:+6.2f}% | "
                  f"WinRate: {res['win_rate_percent']:5.1f}% | DD: {res['max_drawdown_percent']:4.1f}%")

        print("\n" + "═"*85)
        print("📊 ملخص الأداء حسب الفئة المالية (Category Summary)")
        print("═"*85)

        for cat, stats in category_summary.items():
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            print(f"   • {cat:12}: إجمالي الربح: ${stats['total_pl']:+9.2f} | "
                  f"الصفقات: {stats['trades']:3} | نسبة الفوز: {win_rate:5.1f}%")

        # حفظ النتائج
        output_file = os.path.join(self.results_dir, f"multiasset_report_{broker_profile.lower()}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'broker_profile': broker_profile,
                'results': all_results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n💾 تم حفظ التقرير الشامل بنجاح في: {output_file}")
        return all_results


if __name__ == "__main__":
    backtester = MultiAssetBacktester()
    backtester.run_all_assets_backtest(broker_profile='STANDARD')
