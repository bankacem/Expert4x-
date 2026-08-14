#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimizer - تحسين وإيجاد أفضل الإعدادات
اختبار مجموعات مختلفة من الإعدادات للعثور على الأفضل
"""

import itertools
import json
from datetime import datetime
from martingale_backtester import MartingaleBacktester
import pandas as pd

class SettingsOptimizer:
    def __init__(self, data_dir='forex_data'):
        self.backtester = MartingaleBacktester(data_dir)
        self.optimization_results = []
    
    def optimize(self, pair, year=2024, num_combinations=50):
        """
        تحسين الإعدادات للعثور على أفضل مجموعة
        pair: زوج العملات
        year: السنة
        num_combinations: عدد المجموعات المراد اختبارها
        """
        
        print(f"\n🔄 جاري تحسين الإعدادات لـ {pair}...\n")
        
        # نطاقات الإعدادات المراد اختبارها
        tp_range = [30, 50, 75, 100]              # Take Profit
        sl_range = [50, 75, 100, 150]            # Stop Loss
        rsi_oversold_range = [20, 25, 30, 35]    # RSI Oversold
        rsi_overbought_range = [65, 70, 75, 80]  # RSI Overbought
        
        best_results = []
        test_count = 0
        
        # اختبار المجموعات
        for tp in tp_range:
            for sl in sl_range:
                for rsi_os in rsi_oversold_range:
                    for rsi_ob in rsi_overbought_range:
                        if test_count >= num_combinations:
                            break
                        
                        settings = {
                            'initial_balance': 1000,
                            'lot_size': 0.1,
                            'martingale_multiplier': 2,
                            'tp_pips': tp,
                            'sl_pips': sl,
                            'max_dd_percent': 30,
                            'rsi_overbought': rsi_ob,
                            'rsi_oversold': rsi_os,
                            'use_martingale': True
                        }
                        
                        result = self.backtester.backtest(pair, year, settings)
                        
                        if result:
                            # حساب درجة الأداء
                            score = self.calculate_score(result)
                            result['score'] = score
                            best_results.append(result)
                            test_count += 1
                            
                            print(f"   [{test_count:2d}] TP:{tp:3d} SL:{sl:3d} RSI:{rsi_os:2d}-{rsi_ob:2d} | "
                                  f"ROI: {result['roi_percent']:+7.2f}% | WR: {result['win_rate_percent']:5.1f}% | "
                                  f"Score: {score:.2f}")
                    
                    if test_count >= num_combinations:
                        break
        
        # ترتيب النتائج حسب الدرجة
        best_results.sort(key=lambda x: x['score'], reverse=True)
        self.optimization_results = best_results
        
        return best_results[:10]  # إرجاع أفضل 10 نتائج
    
    def calculate_score(self, result):
        """
        حساب درجة الأداء (من 0 إلى 100)
        تأخذ بعين الاعتبار: ROI، معدل الفوز، والتراجع
        """
        roi_score = min(result['roi_percent'] / 10, 40)  # max 40 نقطة
        win_rate_score = result['win_rate_percent'] / 2.5  # max 40 نقطة
        dd_score = max(0, (50 - result['max_drawdown_percent']) / 5)  # max 10 نقاط
        
        score = roi_score + win_rate_score + dd_score
        return score
    
    def print_top_results(self, top_n=5):
        """
        طباعة أفضل النتائج
        """
        if not self.optimization_results:
            print("❌ لا توجد نتائج للعرض")
            return
        
        print(f"\n{'='*100}")
        print(f"🏆 أفضل {top_n} إعدادات")
        print(f"{'='*100}\n")
        
        for rank, result in enumerate(self.optimization_results[:top_n], 1):
            print(f"\n🥇 ترتيب #{rank} | Score: {result['score']:.2f}")
            print(f"   {'-'*96}")
            print(f"   الإعدادات:")
            print(f"      • TP: {result['settings']['tp_pips']} pips | SL: {result['settings']['sl_pips']} pips")
            print(f"      • RSI: {result['settings']['rsi_oversold']}-{result['settings']['rsi_overbought']}")
            print(f"   النتائج:")
            print(f"      • ROI: {result['roi_percent']:+.2f}% | الربح: ${result['profit_loss']:.2f}")
            print(f"      • معدل الفوز: {result['win_rate_percent']:.1f}% ({result['winning_trades']}/{result['total_trades']})")
            print(f"      • أقصى تراجع: {result['max_drawdown_percent']:.2f}%")
    
    def export_results(self, filename='optimization_results.json'):
        """
        تصدير النتائج إلى JSON
        """
        # تحويل النتائج إلى قاموس قابل للتسلسل
        exportable_results = []
        for result in self.optimization_results:
            exportable = result.copy()
            exportable.pop('trades_sample', None)  # إزالة العمليات لتقليل الحجم
            exportable_results.append(exportable)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(exportable_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ تم حفظ النتائج في: {filename}")
    
    def create_recommendations(self):
        """
        إنشاء توصيات بناءً على نتائج التحسين
        """
        if not self.optimization_results:
            return None
        
        best = self.optimization_results[0]
        
        recommendations = {
            'recommended_settings': best['settings'],
            'expected_roi': best['roi_percent'],
            'expected_win_rate': best['win_rate_percent'],
            'expected_max_dd': best['max_drawdown_percent'],
            'confidence_level': self._calculate_confidence(best),
            'warnings': self._get_warnings(best),
            'notes': self._get_notes(best)
        }
        
        return recommendations
    
    def _calculate_confidence(self, result):
        """
        حساب مستوى الثقة (منخفض، متوسط، عالي)
        """
        if result['roi_percent'] > 20 and result['win_rate_percent'] > 55 and result['max_drawdown_percent'] < 20:
            return "🟢 عالي"
        elif result['roi_percent'] > 5 and result['win_rate_percent'] > 50 and result['max_drawdown_percent'] < 30:
            return "🟡 متوسط"
        else:
            return "🔴 منخفض"
    
    def _get_warnings(self, result):
        """
        الحصول على تحذيرات بناءً على النتائج
        """
        warnings = []
        
        if result['max_drawdown_percent'] > 25:
            warnings.append("⚠️ التراجع القصوى عالي جداً - مخاطرة عالية")
        if result['win_rate_percent'] < 50:
            warnings.append("⚠️ معدل الفوز أقل من 50% - قد تكون خسائر متكررة")
        if result['total_trades'] < 20:
            warnings.append("⚠️ عدد العمليات قليل - بيانات غير كافية للحكم")
        
        return warnings
    
    def _get_notes(self, result):
        """
        ملاحظات إضافية
        """
        notes = []
        
        if result['roi_percent'] > 15:
            notes.append("✅ أداء ممتازة جداً")
        if result['win_rate_percent'] > 60:
            notes.append("✅ معدل فوز عالي جداً")
        if result['max_drawdown_percent'] < 15:
            notes.append("✅ إدارة مخاطر ممتازة")
        
        return notes


if __name__ == "__main__":
    optimizer = SettingsOptimizer()
    
    # تحسين الإعدادات لـ EURUSD
    print("\n" + "="*100)
    print("🚀 برنامج تحسين إعدادات المتداول الآلي")
    print("="*100)
    
    top_results = optimizer.optimize('EURUSD', year=2024, num_combinations=30)
    optimizer.print_top_results(top_n=5)
    
    # حفظ النتائج
    optimizer.export_results('eurusd_optimization_results.json')
    
    # التوصيات
    recommendations = optimizer.create_recommendations()
    if recommendations:
        print(f"\n{'='*100}")
        print("📋 التوصيات النهائية")
        print(f"{'='*100}\n")
        print(f"مستوى الثقة: {recommendations['confidence_level']}")
        print(f"\nالإعدادات الموصى بها:")
        for key, value in recommendations['recommended_settings'].items():
            print(f"   • {key}: {value}")
        
        if recommendations['warnings']:
            print(f"\nالتحذيرات:")
            for warning in recommendations['warnings']:
                print(f"   {warning}")
        
        if recommendations['notes']:
            print(f"\nملاحظات إيجابية:")
            for note in recommendations['notes']:
                print(f"   {note}")
