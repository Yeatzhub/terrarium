# Drawdown Analyzer — Risk & Recovery Calculator

**Purpose:** Analyze historical drawdowns, calculate recovery requirements, and stress-test portfolio resilience  
**Use Case:** Understand max pain, plan position sizing for worst-case scenarios

## The Code

```python
"""
Drawdown Analyzer
Calculate drawdowns from equity curve, analyze recovery patterns,
and stress-test portfolio resilience.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, stdev
import math


@dataclass
class Drawdown:
    """Single drawdown event."""
    start_date: datetime
    start_equity: float
    
    trough_date: datetime
    trough_equity: float
    
    end_date: Optional[datetime]  # When equity hits new high
    end_equity: Optional[float]
    
    # Metrics
    drawdown_pct: float  # Peak to trough
    drawdown_dollars: float
    duration_days: int  # Peak to trough
    recovery_days: Optional[int]  # Trough to recovery
    total_duration_days: Optional[int]  # Peak to new high
    
    # Classification
    severity: str  # minor, moderate, severe, extreme
    
    def is_active(self) -> bool:
        return self.end_date is None
    
    def max_loss_pct(self) -> float:
        return -self.drawdown_pct


@dataclass
class DrawdownStats:
    """Aggregate drawdown statistics."""
    # Maximums
    max_drawdown_pct: float
    max_drawdown_dollars: float
    longest_duration_days: int
    longest_recovery_days: int
    
    # Averages
    avg_drawdown_pct: float
    avg_drawdown_dollars: float
    avg_duration_days: float
    avg_recovery_days: float
    
    # Frequency
    total_drawdowns: int
    active_drawdowns: int
    recovered_drawdowns: int
    
    # Recovery ratios
    avg_recovery_ratio: float  # Recovery DD / New High DD comparison
    
    # Percentiles
    pct_50_drawdown: float
    pct_75_drawdown: float
    pct_90_drawdown: float
    pct_95_drawdown: float


@dataclass
class RecoveryAnalysis:
    """Analysis of recovery requirements."""
    drawdown_pct: float
    required_gain_pct: float  # Gain needed to recover
    
    # Time estimates
    estimated_recovery_days_fast: float  # Based on best performance
    estimated_recovery_days_avg: float   # Based on average
    estimated_recovery_days_slow: float  # Based on worst times
    
    # Probability
    prob_recovery_30d: float
    prob_recovery_90d: float
    prob_recovery_180d: float


@dataclass
class StressTest:
    """Stress test scenario results."""
    scenario: str
    severity: str
    
    start_equity: float
    stressed_equity: float
    drawdown_pct: float
    
    position_size_after: float
    trades_to_recover: int
    
    survives: bool  # Above ruin threshold


class DrawdownAnalyzer:
    """
    Analyze drawdowns from equity curve data.
    
    Usage:
        analyzer = DrawdownAnalyzer()
        
        # Load equity curve
        equity_points = [
            (datetime(2023, 1, 1), 100000),
            (datetime(2023, 1, 2), 101000),
            ...
        ]
        
        # Analyze
        drawdowns = analyzer.calculate_drawdowns(equity_points)
        stats = analyzer.get_statistics(drawdowns)
        
        print(f"Max drawdown: {stats.max_drawdown_pct:.1f}%")
        
        # Stress test
        scenarios = analyzer.stress_test(current_equity=100000)
    """
    
    def __init__(self, minor_threshold: float = 5.0, severe_threshold: float = 20.0):
        self.minor_threshold = minor_threshold
        self.severe_threshold = severe_threshold
    
    def calculate_drawdowns(
        self,
        equity_curve: List[Tuple[datetime, float]]
    ) -> List[Drawdown]:
        """Calculate all drawdowns from equity curve."""
        if len(equity_curve) < 2:
            return []
        
        drawdowns = []
        
        peak_equity = equity_curve[0][1]
        peak_date = equity_curve[0][0]
        
        current_dd_start = None
        current_dd_trough = peak_equity
        current_dd_trough_date = peak_date
        
        for i, (date, equity) in enumerate(equity_curve):
            # New peak
            if equity >= peak_equity:
                # Close any active drawdown
                if current_dd_start is not None:
                    drawdown = self._create_drawdown(
                        current_dd_start, current_dd_trough_date, date,
                        peak_at_start, current_dd_trough, equity, equity_curve
                    )
                    drawdowns.append(drawdown)
                    current_dd_start = None
                
                # Update peak
                peak_equity = equity
                peak_date = date
                peak_at_start = equity
            
            # Track drawdown
            elif equity < peak_equity:
                if current_dd_start is None:
                    current_dd_start = peak_date
                    peak_at_start = peak_equity
                
                # Track trough
                if equity < current_dd_trough:
                    current_dd_trough = equity
                    current_dd_trough_date = date
        
        # Handle active drawdown at end
        if current_dd_start is not None:
            drawdown = self._create_drawdown(
                current_dd_start, current_dd_trough_date, None,
                peak_at_start, current_dd_trough, None, equity_curve
            )
            drawdowns.append(drawdown)
        
        return drawdowns
    
    def _create_drawdown(
        self,
        start_date: datetime,
        trough_date: datetime,
        end_date: Optional[datetime],
        start_equity: float,
        trough_equity: float,
        end_equity: Optional[float],
        equity_curve: List[Tuple[datetime, float]]
    ) -> Drawdown:
        """Create Drawdown object."""
        dd_pct = (trough_equity / start_equity - 1) * 100
        dd_dollars = start_equity - trough_equity
        duration = (trough_date - start_date).days
        
        recovery = None
        total_duration = None
        
        if end_date:
            recovery = (end_date - trough_date).days
            total_duration = (end_date - start_date).days
        
        # Classify severity
        if abs(dd_pct) < self.minor_threshold:
            severity = "minor"
        elif abs(dd_pct) < self.severe_threshold:
            severity = "moderate"
        elif abs(dd_pct) < 50:
            severity = "severe"
        else:
            severity = "extreme"
        
        return Drawdown(
            start_date=start_date,
            start_equity=start_equity,
            trough_date=trough_date,
            trough_equity=trough_equity,
            end_date=end_date,
            end_equity=end_equity,
            drawdown_pct=dd_pct,
            drawdown_dollars=dd_dollars,
            duration_days=duration,
            recovery_days=recovery,
            total_duration_days=total_duration,
            severity=severity
        )
    
    def get_statistics(self, drawdowns: List[Drawdown]) -> DrawdownStats:
        """Calculate aggregate statistics."""
        if not drawdowns:
            return DrawdownStats(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # Max values
        max_dd_pct = min(d.drawdown_pct for d in drawdowns)
        max_dd_dollars = max(d.drawdown_dollars for d in drawdowns)
        max_duration = max(d.duration_days for d in drawdowns)
        
        recoveries = [d.recovery_days for d in drawdowns if d.recovery_days]
        max_recovery = max(recoveries) if recoveries else 0
        
        # Averages
        avg_dd_pct = mean(d.drawdown_pct for d in drawdowns)
        avg_dd_dollars = mean(d.drawdown_dollars for d in drawdowns)
        avg_duration = mean(d.duration_days for d in drawdowns)
        avg_recovery = mean(recoveries) if recoveries else 0
        
        # Active vs recovered
        active = sum(1 for d in drawdowns if d.is_active())
        recovered = len(drawdowns) - active
        
        # Percentiles
        dd_pcts = sorted([d.drawdown_pct for d in drawdowns])
        n = len(dd_pcts)
        
        pct_50 = dd_pcts[int(n * 0.50)]
        pct_75 = dd_pcts[int(n * 0.75)]
        pct_90 = dd_pcts[int(n * 0.90)] if n >= 10 else dd_pcts[-1]
        pct_95 = dd_pcts[int(n * 0.95)] if n >= 20 else dd_pcts[-1]
        
        return DrawdownStats(
            max_drawdown_pct=max_dd_pct,
            max_drawdown_dollars=max_dd_dollars,
            longest_duration_days=max_duration,
            longest_recovery_days=max_recovery,
            avg_drawdown_pct=avg_dd_pct,
            avg_drawdown_dollars=avg_dd_dollars,
            avg_duration_days=avg_duration,
            avg_recovery_days=avg_recovery,
            total_drawdowns=len(drawdowns),
            active_drawdowns=active,
            recovered_drawdowns=recovered,
            avg_recovery_ratio=0,  # Simplified
            pct_50_drawdown=pct_50,
            pct_75_drawdown=pct_75,
            pct_90_drawdown=pct_90,
            pct_95_drawdown=pct_95
        )
    
    def analyze_recovery(
        self,
        drawdown_pct: float,
        historical_drawdowns: Optional[List[Drawdown]] = None
    ) -> RecoveryAnalysis:
        """Calculate recovery requirements for a drawdown level."""
        # Calculate required gain
        dd_decimal = abs(drawdown_pct) / 100
        required_gain = (1 / (1 - dd_decimal) - 1) * 100
        
        # Estimate recovery times from historical data
        fast = avg = slow = 0
        
        if historical_drawdowns:
            similar_dds = [d for d in historical_drawdowns 
                          if d.recovery_days and abs(d.drawdown_pct) >= abs(drawdown_pct) * 0.8]
            
            if similar_dds:
                recoveries = [d.recovery_days for d in similar_dds]
                fast = min(recoveries)
                avg = mean(recoveries)
                slow = max(recoveries)
        
        # Probabilities (simplified model)
        prob_30 = max(0, 1 - abs(drawdown_pct) / 50) if fast <= 30 else 0.2
        prob_90 = max(0, 1 - abs(drawdown_pct) / 30) if avg <= 90 else 0.4
        prob_180 = max(0, 1 - abs(drawdown_pct) / 20) if slow <= 180 else 0.6
        
        return RecoveryAnalysis(
            drawdown_pct=drawdown_pct,
            required_gain_pct=required_gain,
            estimated_recovery_days_fast=fast,
            estimated_recovery_days_avg=avg if avg > 0 else abs(drawdown_pct) * 3,
            estimated_recovery_days_slow=slow if slow > 0 else abs(drawdown_pct) * 6,
            prob_recovery_30d=prob_30,
            prob_recovery_90d=prob_90,
            prob_recovery_180d=prob_180
        )
    
    def stress_test(
        self,
        current_equity: float,
        win_rate: float = 0.55,
        avg_win: float = 100,
        avg_loss: float = 80,
        daily_trades: int = 5,
        ruin_threshold: float = 0.50
    ) -> List[StressTest]:
        """Run stress test scenarios."""
        scenarios = [
            ("Mild Correction", -5, "minor"),
            ("Moderate Drawdown", -10, "moderate"),
            ("Severe Drawdown", -20, "severe"),
            ("Extreme Drawdown", -35, "extreme"),
            ("Max Historical", -50, "catastrophic"),
        ]
        
        results = []
        
        for name, dd_pct, severity in scenarios:
            stressed_equity = current_equity * (1 + dd_pct / 100)
            
            # Calculate position size at this equity
            # Kelly position sizing
            b = avg_win / avg_loss  # Win/loss ratio
            kelly = (win_rate * (b + 1) - 1) / b
            half_kelly = max(0, kelly * 0.5)
            
            # Calculate trades to recover
            expected_return = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            if expected_return > 0:
                recovery_dollars = current_equity - stressed_equity
                trades_needed = recovery_dollars / expected_return
            else:
                trades_needed = float('inf')
            
            survives = (stressed_equity / current_equity) > ruin_threshold
            
            results.append(StressTest(
                scenario=name,
                severity=severity,
                start_equity=current_equity,
                stressed_equity=stressed_equity,
                drawdown_pct=dd_pct,
                position_size_after=half_kelly,
                trades_to_recover=int(trades_needed) if trades_needed != float('inf') else -1,
                survives=survives
            ))
        
        return results
    
    def generate_report(
        self,
        drawdowns: List[Drawdown],
        current_equity: float
    ) -> str:
        """Generate formatted report."""
        stats = self.get_statistics(drawdowns)
        
        lines = [
            f"{'=' * 70}",
            "DRAWDOWN ANALYSIS REPORT",
            f"{'=' * 70}",
            "",
            f"Total Drawdowns Analyzed: {stats.total_drawdowns}",
            f"Active Drawdowns: {stats.active_drawdowns}",
            f"Recovered Drawdowns: {stats.recovered_drawdowns}",
            "",
            "SEVERITY DISTRIBUTION:",
        ]
        
        severity_counts = {}
        for d in drawdowns:
            severity_counts[d.severity] = severity_counts.get(d.severity, 0) + 1
        
        for sev in ["minor", "moderate", "severe", "extreme"]:
            count = severity_counts.get(sev, 0)
            pct = count / stats.total_drawdowns * 100 if stats.total_drawdowns > 0 else 0
            lines.append(f"  {sev.capitalize():<10}: {count} ({pct:.1f}%)")
        
        lines.extend([
            "",
            "DRAWDOWN STATISTICS:",
            f"  Max Drawdown:     {stats.max_drawdown_pct:+.1f}% (${stats.max_drawdown_dollars:,.0f})",
            f"  Average DD:       {stats.avg_drawdown_pct:+.1f}% (${stats.avg_drawdown_dollars:,.0f})",
            f"  Median DD:        {stats.pct_50_drawdown:+.1f}%",
            f"  75th Percentile:  {stats.pct_75_drawdown:+.1f}%",
            f"  90th Percentile:  {stats.pct_90_drawdown:+.1f}%",
            f"  95th Percentile:  {stats.pct_95_drawdown:+.1f}%",
            "",
            "DURATION STATISTICS:",
            f"  Longest Drawdown: {stats.longest_duration_days} days",
            f"  Average Duration: {stats.avg_duration_days:.1f} days",
            f"  Longest Recovery: {stats.longest_recovery_days} days",
            f"  Average Recovery: {stats.avg_recovery_days:.1f} days",
            "",
        ])
        
        # Recovery analysis for max drawdown
        if drawdowns:
            recovery = self.analyze_recovery(stats.max_drawdown_pct)
            lines.extend([
                "RECOVERY ANALYSIS (Max DD Level):",
                f"  Drawdown:         {recovery.drawdown_pct:.1f}%",
                f"  Gain Required:    +{recovery.required_gain_pct:.1f}% to recover",
                f"  Fast Recovery:    {recovery.estimated_recovery_days_fast:.0f} days",
                f"  Avg Recovery:     {recovery.estimated_recovery_days_avg:.0f} days",
                f"  Slow Recovery:    {recovery.estimated_recovery_days_slow:.0f} days",
                "",
            ])
        
        # Current status
        active = [d for d in drawdowns if d.is_active()]
        if active:
            lines.extend([
                "ACTIVE DRAWDOWN:",
                f"  Started:          {active[0].start_date.strftime('%Y-%m-%d')}",
                f"  Days in DD:       {active[0].duration_days}",
                f"  Current DD:       {active[0].drawdown_pct:.1f}%",
                f"  Peak Equity:      ${active[0].start_equity:,.2f}",
                f"  Current Equity:   ${active[0].trough_equity:,.2f}",
                "",
            ])
        
        lines.append(f"{'=' * 70}")
        
        return "\n".join(lines)


def format_recovery_table(recovery: RecoveryAnalysis) -> str:
    """Format recovery requirements table."""
    lines = [
        f"{'=' * 70}",
        f"RECOVERY ANALYSIS: {recovery.drawdown_pct:.1f}% DRAWDOWN",
        f"{'=' * 70}",
        "",
        f"📉 Drawdown:        {recovery.drawdown_pct:.1f}%",
        f"📈 Gain Required:    +{recovery.required_gain_pct:.1f}%",
        "",
        "Key Principle:",
        "  A 50% loss requires a 100% gain to recover!",
        "  A 20% loss requires a 25% gain to recover.",
        "  Small losses are exponentially easier to recover than large ones.",
        "",
        "Recovery Time Estimates:",
        f"  Fast (best case):  {recovery.estimated_recovery_days_fast:.0f} days",
        f"  Average:           {recovery.estimated_recovery_days_avg:.0f} days",
        f"  Slow (worst case): {recovery.estimated_recovery_days_slow:.0f} days",
        "",
        f"Probability of Recovery:",
        f"  Within 30 days:    {recovery.prob_recovery_30d*100:.0f}%",
        f"  Within 90 days:    {recovery.prob_recovery_90d*100:.0f}%",
        f"  Within 180 days:   {recovery.prob_recovery_180d*100:.0f}%",
        f"{'=' * 70}",
    ]
    
    return "\n".join(lines)


# === Examples ===

def example_drawdown_analysis():
    """Demonstrate drawdown analysis."""
    print("=" * 70)
    print("Drawdown Analysis Example")
    print("=" * 70)
    
    # Generate sample equity curve with realistic drawdowns
    import random
    random.seed(42)
    
    equity = 100000
    equity_curve = [(datetime(2023, 1, 1), equity)]
    
    # Generate 2 years of daily data with realistic volatility
    current_date = datetime(2023, 1, 1)
    
    # Market simulation phases
    phases = [
        ("uptrend", 180, 0.0005, 0.008),
        ("correction", 30, -0.001, 0.015),
        ("recovery", 90, 0.0008, 0.01),
        ("chop", 60, 0.0001, 0.012),
        ("crash", 20, -0.003, 0.02),
        ("bear market", 120, -0.001, 0.015),
        ("recovery", 150, 0.001, 0.012),
        ("bull run", 200, 0.0012, 0.01),
    ]
    
    for phase_name, days, drift, volatility in phases:
        for _ in range(days):
            current_date += timedelta(days=1)
            change = random.normalvariate(drift, volatility)
            equity *= (1 + change)
            equity_curve.append((current_date, equity))
    
    analyzer = DrawdownAnalyzer()
    drawdowns = analyzer.calculate_drawdowns(equity_curve)
    stats = analyzer.get_statistics(drawdowns)
    
    print(f"\nTotal Drawdowns: {stats.total_drawdowns}")
    print(f"Active: {stats.active_drawdowns}")
    print(f"Recovered: {stats.recovered_drawdowns}")
    
    print("\n--- TOP 5 DRAWDOWNS ---")
    sorted_dds = sorted(drawdowns, key=lambda d: d.drawdown_pct)[:5]
    
    for i, dd in enumerate(sorted_dds, 1):
        recovery = f"{dd.recovery_days}d" if dd.recovery_days else "ONGOING"
        print(f"\n{i}. {dd.start_date.strftime('%Y-%m-%d')} to {dd.trough_date.strftime('%Y-%m-%d')}")
        print(f"   Drop: {dd.drawdown_pct:.1f}% | ${dd.drawdown_dollars:,.0f}")
        print(f"   Severity: {dd.severity.upper()} | Duration: {dd.duration_days}d | Recovery: {recovery}")
    
    print("\n" + "-" * 70)
    print(f"STATISTICS:")
    print(f"  Max DD:    {stats.max_drawdown_pct:.1f}%")
    print(f"  Avg DD:    {stats.avg_drawdown_pct:.1f}%")
    print(f"  Median DD: {stats.pct_50_drawdown:.1f}%")
    print(f"  90th %ile: {stats.pct_90_drawdown:.1f}%")
    print(f"\n  Longest DD:    {stats.longest_duration_days} days")
    print(f"  Avg Recovery:  {stats.avg_recovery_days:.1f} days")
    
    # Recovery analysis
    print("\n" + analyzer.generate_report(drawdowns, equity_curve[-1][1]))


def example_recovery_math():
    """Demonstrate recovery mathematics."""
    print("\n" + "=" * 70)
    print("Recovery Mathematics")
    print("=" * 70)
    
    drawdowns = [5, 10, 15, 20, 25, 30, 40, 50]
    
    print(f"\n{'Drawdown':<12} {'Gain Needed':<15} {'Hardness':<15}")
    print("-" * 70)
    
    for dd in drawdowns:
        required = (1 / (1 - dd/100) - 1) * 100
        hardness = "Easy" if required < 15 else "Moderate" if required < 35 else "Hard" if required < 70 else "Very Hard"
        bar = "█" * int(required / 5)
        print(f"-{dd:.0f}%<12 {required:+.0f}%<15 {hardness:<15} {bar}")
    
    print("\nKey Insight:")
    print("  • -10% requires +11% recovery (1.1x)")
    print("  • -20% requires +25% recovery (1.25x)")
    print("  • -50% requires +100% recovery (2x)")
    print("  • Losses compound asymmetrically—avoid big drawdowns!")


def example_stress_test():
    """Demonstrate stress testing."""
    print("\n" + "=" * 70)
    print("Portfolio Stress Test")
    print("=" * 70)
    
    analyzer = DrawdownAnalyzer()
    
    current_equity = 100000
    
    results = analyzer.stress_test(
        current_equity=current_equity,
        win_rate=0.55,
        avg_win=150,
        avg_loss=100,
        daily_trades=5,
        ruin_threshold=0.50
    )
    
    print(f"\nCurrent Equity: ${current_equity:,.0f}")
    print(f"Win Rate: 55% | R:R = 1.5 | Daily Trades: 5")
    print("\n" + "-" * 70)
    print(f"{'Scenario':<20} {'DD':<10} {'Equity':<15} {'Trades':<12} {'Status'}")
    print("-" * 70)
    
    for result in results:
        status = "✅ Survives" if result.survives else "❌ RUINED"
        trades = f"{result.trades_to_recover}" if result.trades_to_recover > 0 else "∞"
        print(f"{result.scenario:<20} {result.drawdown_pct:+.0f}%       ${result.stressed_equity:<14,.0f} {trades:<12} {status}")
    
    print("\n" + "=" * 70)
    print("CONCLUSIONS:")
    print("=" * 70)
    print("  • Mild/moderate drawdowns: Recoverable in weeks")
    print("  • Severe drawdowns (-20%): Months to recover")
    print("  • Extreme drawdowns (-35%): Likely ruin or years to recover")
    print("  • Catastrophic (-50%): Survival unlikely")


if __name__ == "__main__":
    example_drawdown_analysis()
    example_recovery_math()
    example_stress_test()
    
    print("\n" + "=" * 70)
    print("KEY PRINCIPLES:")
    print("=" * 70)
    print("""
1. DRAWDOWNS ARE ASYMMETRICAL: -50% requires +100% to recover
2. SMALL LOSSES COMPOUND FASTER: Easier to recover from 3 x -5% than 1 x -15%
3. EXPECT DRAWDOWNS: They're normal; plan for them, don't fear them
4. SIZE ACCORDINGLY: If max DD is -30%, size so you can survive mentally
5. TIME MATTERS: Long drawdowns = emotional drain; have cash reserves ready

"If you lose 50%, you must make 100% to get back to even."
    """)
    print("=" * 70)
```

## Recovery Mathematics

| Drawdown | Required Gain | Difficulty |
|----------|---------------|------------|
| -5% | +5.3% | Easy |
| -10% | +11.1% | Easy |
| -15% | +17.6% | Moderate |
| -20% | +25.0% | Moderate |
| -25% | +33.3% | Hard |
| -30% | +42.9% | Hard |
| -40% | +66.7% | Very Hard |
| -50% | +100.0% | Catastrophic |

## Drawdown Severity Classification

| Severity | Range | Action |
|----------|-------|--------|
| **Minor** | < 5% | Normal operation |
| **Moderate** | 5-20% | Reduce size slightly, review strategy |
| **Severe** | 20-50% | Significant size reduction, pause new trades |
| **Extreme** | > 50% | Likely ruin, major review needed |

## Quick Reference

```python
analyzer = DrawdownAnalyzer()

# Calculate drawdowns
drawdowns = analyzer.calculate_drawdowns(equity_curve)

# Get statistics
stats = analyzer.get_statistics(drawdowns)
print(f"Max DD: {stats.max_drawdown_pct:.1f}%")

# Recovery analysis
recovery = analyzer.analyze_recovery(-20.0)
print(f"Need {recovery.required_gain_pct:.1f}% gain to recover")

# Stress test
scenarios = analyzer.stress_test(
    current_equity=100000,
    win_rate=0.55,
    avg_win=150,
    avg_loss=100
)

for s in scenarios:
    print(f"{s.scenario}: {s.drawdown_pct}% → ${s.stressed_equity:.0f}")
```

## Why This Matters

- **Asymmetry kills** — A 50% drawdown requires 100% recovery
- **Expect drawdowns** — They're inevitable; plan for them
- **Size for the worst** — Can you survive your max historical drawdown?
- **Recovery time matters** — Months underwater affect psychology
- **Small losses win** — Easier to recover from 5 × -4% than 1 × -20%

**The math is simple: avoid big drawdowns, because the recovery math gets brutal.**

---

**Created by Ghost 👻 | Feb 20, 2026 | 11-min learning sprint**  
*Lesson: "Drawdowns are inevitable—the question is surviving them." A -50% drawdown requires +100% to recover. Small losses compound faster than big ones. Size so you can survive your worst historical drawdown without emotion.*
