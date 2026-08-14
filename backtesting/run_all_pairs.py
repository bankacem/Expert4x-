#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تشغيل الاختبارات على جميع أزواج العملات
اختبار شامل لجميع العملات المدعومة
"""

import json
from datetime import datetime
from martingale_backtester import MartingaleBacktester
from optimizer import SettingsOptimizer
import pandas as pd

class ComprehensiveBacktester:
    def __init__(self, data_dir='forex_data'):
        self.backtester = MartingaleBacktester(data_dir)
        self.optimizer = SettingsOptimizer(data_dir)
        self.all_results = {}
        self.pairs = [
            'EURUSD', 'GBPUSD', 'USDCHF', 'USDJPY',
            'AUDUSD', 'USDCAD', 'EURCHF', 'EURGBP', 'EURJPY'
        ]
    
    def test_all_pairs(self, year=2024):
        """
        اختبار جميع الأزواج بالإعدادات الافتراضية
        """
        print(f"\n{'='*100}")
        print(f"🌍 اختبار جميع أزواج العملات - {year}")
        print(f"{'='*100}\n")
        
        results_df = []
        
        for pair in self.pairs:
            print(f"\n🔍 اختبار {pair}...")
            result = self.backtester.backtest(pair, year)
            
            if result:
                self.all_results[pair] = result
                results_df.append({
                    'Pair': pair,
                    'Final Balance': f"${result['final_balance']}",
                    'P&L': f"${result['profit_loss']}",
                    'ROI %': f"{result['roi_percent']:.2f}%",
                    'Total Trades': result['total_trades'],
                    'Win Rate %': f"{result['win_rate_percent']:.2f}%",
                    'Max DD %': f"{result['max_drawdown_percent']:.2f}%"
                })
        
        # طباعة الملخص
        self.print_summary(results_df)
        return self.all_results
    
    def optimize_all_pairs(self, year=2024, num_combinations=20):
        """
        تحسين الإعدادات لجميع الأزواج
        """
        print(f"\n{'='*100}")
        print(f"🚀 تحسين الإعدادات لجميع أزواج العملات")
        print(f"{'='*100}\n")
        
        optimization_results = {}
        
        for pair in self.pairs:
            print(f"\n{'─'*100}")
            print(f"⚙️ تحسين {pair}...")
            print(f"{'─'*100}")
            
            top_results = self.optimizer.optimize(pair, year, num_combinations)
            if top_results:
                optimization_results[pair] = top_results[0]  # الأفضل فقط
        
        return optimization_results
    
    def print_summary(self, results_df):
        """
        طباعة ملخص النتائج
        """
        print(f"\n{'='*100}")
        print(f"📊 ملخص النتائج")
        print(f"{'='*100}\n")
        
        df = pd.DataFrame(results_df)
        print(df.to_string(index=False))
        
        # إحصائيات عامة
        print(f"\n{'='*100}")
        print(f"📈 الإحصائيات العامة")
        print(f"{'='*100}\n")
        
        total_roi = sum([float(r['P&L'].replace('$', '')) for r in results_df if '$' in r['P&L']])
        avg_win_rate = sum([float(r['Win Rate %'].replace('%', '')) for r in results_df if '%' in r['Win Rate %']]) / len(results_df)
        
        print(f"   • إجمالي الربح/الخسارة: ${total_roi:.2f}")
        print(f"   • متوسط معدل الفوز: {avg_win_rate:.2f}%")
        print(f"   • عدد الأزواج المختبرة: {len(results_df)}")
    
    def export_all_results(self, filename='all_pairs_results.json'):
        """
        تصدير جميع النتائج
        """
        # تنظيف النتائج للتصدير
        clean_results = {}
        for pair, result in self.all_results.items():
            clean_result = result.copy()
            clean_result.pop('trades_sample', None)
            clean_results[pair] = clean_result
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'results': clean_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ تم حفظ النتائج في: {filename}")


if __name__ == "__main__":
    comprehensive = ComprehensiveBacktester()
    
    # اختبار جميع الأزواج
    all_results = comprehensive.test_all_pairs(year=2024)
    
    # حفظ النتائج
    comprehensive.export_all_results()
    
    # اختبار اختياري: تحسين الإعدادات (قد يستغرق وقتاً طويلاً)
    # optimize_results = comprehensive.optimize_all_pairs(year=2024, num_combinations=15)
