# Correlation Risk Analyzer

**Purpose:** Detect concentration risk from correlated positions, suggest diversification  
**Use Case:** Prevent "hidden" portfolio concentration when assets move together

## The Code

```python
"""
Correlation Risk Analyzer
Identify correlated positions, calculate portfolio risk concentration,
suggest rebalancing to reduce systematic exposure.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum, auto
import math
from collections import defaultdict


@dataclass
class Position:
    symbol: str
    value: float
    sector: str
    beta: float = 1.0  # Market beta
    volatility: float = 0.0  # Annualized volatility


@dataclass
class CorrelationPair:
    symbol1: str
    symbol2: str
    correlation: float  # -1 to 1
    risk_contribution: float  # Combined risk from correlation


@dataclass
class Cluster:
    """Group of highly correlated assets."""
    id: int
    symbols: Set[str]
    total_value: float
    avg_correlation: float
    risk_concentration: float


@dataclass
class RiskReport:
    """Complete correlation risk analysis."""
    total_portfolio_value: float
    num_positions: int
    correlation_matrix: Dict[Tuple[str, str], float]
    high_correlation_pairs: List[CorrelationPair]
    clusters: List[Cluster]
    concentration_risk_score: float  # 0-100
    sector_exposure: Dict[str, float]
    recommendations: List[str]
    
    def is_diversified(self, threshold: float = 70.0) -> bool:
        return self.concentration_risk_score < threshold


class CorrelationRiskAnalyzer:
    """
    Analyze portfolio for correlation-based concentration risk.
    
    Usage:
        analyzer = CorrelationRiskAnalyzer(correlation_threshold=0.70)
        report = analyzer.analyze(positions)
        print(f"Risk score: {report.concentration_risk_score:.1f}")
    """
    
    def __init__(
        self,
        correlation_threshold: float = 0.70,
        cluster_threshold: float = 0.60,
        high_risk_threshold: float = 80.0,
        max_sector_pct: float = 30.0
    ):
        self.corr_threshold = correlation_threshold
        self.cluster_threshold = cluster_threshold
        self.high_risk_threshold = high_risk_threshold
        self.max_sector_pct = max_sector_pct
    
    def analyze(self, positions: List[Position]) -> RiskReport:
        """Generate complete correlation risk report."""
        if len(positions) < 2:
            return RiskReport(
                total_portfolio_value=sum(p.value for p in positions),
                num_positions=len(positions),
                correlation_matrix={},
                high_correlation_pairs=[],
                clusters=[],
                concentration_risk_score=0.0,
                sector_exposure={},
                recommendations=["Need at least 2 positions for correlation analysis"]
            )
        
        total_value = sum(p.value for p in positions)
        
        # Build correlation matrix (in real use, load from historical data)
        corr_matrix = self._estimate_correlations(positions)
        
        # Find high correlation pairs
        high_corr_pairs = self._find_high_correlations(positions, corr_matrix, total_value)
        
        # Identify clusters
        clusters = self._find_clusters(positions, corr_matrix, total_value)
        
        # Calculate sector exposure
        sector_exposure = self._calculate_sector_exposure(positions, total_value)
        
        # Calculate concentration risk score
        risk_score = self._calculate_risk_score(
            positions, high_corr_pairs, clusters, sector_exposure
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            positions, high_corr_pairs, clusters, sector_exposure, risk_score, total_value
        )
        
        return RiskReport(
            total_portfolio_value=total_value,
            num_positions=len(positions),
            correlation_matrix=corr_matrix,
            high_correlation_pairs=high_corr_pairs,
            clusters=clusters,
            concentration_risk_score=risk_score,
            sector_exposure=sector_exposure,
            recommendations=recommendations
        )
    
    def _estimate_correlations(self, positions: List[Position]) -> Dict[Tuple[str, str], float]:
        """
        Estimate correlations between positions.
        In production, load from historical price correlation matrix.
        """
        matrix = {}
        
        for i, p1 in enumerate(positions):
            for j, p2 in enumerate(positions):
                if i >= j:
                    continue
                
                # Estimate correlation based on sector and beta similarity
                corr = self._estimate_pair_correlation(p1, p2)
                matrix[(p1.symbol, p2.symbol)] = corr
                matrix[(p2.symbol, p1.symbol)] = corr
        
        return matrix
    
    def _estimate_pair_correlation(self, p1: Position, p2: Position) -> float:
        """Estimate correlation between two positions."""
        # Same sector = higher correlation
        if p1.sector == p2.sector:
            base_corr = 0.75
        else:
            # Different sectors have lower correlation
            sector_correlations = {
                ("tech", "financial"): 0.40,
                ("tech", "healthcare"): 0.25,
                ("tech", "energy"): 0.15,
                ("financial", "energy"): 0.35,
                ("healthcare", "consumer"): 0.30,
            }
            key = tuple(sorted([p1.sector, p2.sector]))
            base_corr = sector_correlations.get(key, 0.20)
        
        # Beta similarity increases correlation
        beta_diff = abs(p1.beta - p2.beta)
        beta_adjustment = max(0, 0.20 - beta_diff * 0.10)
        
        # Volatility similarity
        vol_diff = abs(p1.volatility - p2.volatility)
        vol_adjustment = max(0, 0.10 - vol_diff * 0.05)
        
        correlation = min(0.95, base_corr + beta_adjustment + vol_adjustment)
        return correlation
    
    def _find_high_correlations(
        self,
        positions: List[Position],
        corr_matrix: Dict[Tuple[str, str], float],
        total_value: float
    ) -> List[CorrelationPair]:
        """Find position pairs with high correlation."""
        pairs = []
        
        for i, p1 in enumerate(positions):
            for j, p2 in enumerate(positions):
                if i >= j:
                    continue
                
                corr = corr_matrix.get((p1.symbol, p2.symbol), 0)
                
                if corr >= self.corr_threshold:
                    # Calculate risk contribution
                    combined_value = p1.value + p2.value
                    risk_contribution = (combined_value / total_value) * corr * 100
                    
                    pairs.append(CorrelationPair(
                        symbol1=p1.symbol,
                        symbol2=p2.symbol,
                        correlation=corr,
                        risk_contribution=risk_contribution
                    ))
        
        # Sort by risk contribution (highest first)
        pairs.sort(key=lambda x: x.risk_contribution, reverse=True)
        return pairs
    
    def _find_clusters(
        self,
        positions: List[Position],
        corr_matrix: Dict[Tuple[str, str], float],
        total_value: float
    ) -> List[Cluster]:
        """Find clusters of highly correlated assets using simple clustering."""
        symbols = [p.symbol for p in positions]
        position_map = {p.symbol: p for p in positions}
        
        # Build adjacency list (high correlation connections)
        adjacency = defaultdict(set)
        for (s1, s2), corr in corr_matrix.items():
            if corr >= self.cluster_threshold:
                adjacency[s1].add(s2)
                adjacency[s2].add(s1)
        
        # Find connected components (clusters)
        visited = set()
        clusters = []
        cluster_id = 0
        
        for symbol in symbols:
            if symbol in visited:
                continue
            
            # BFS to find cluster
            cluster_symbols = set()
            queue = [symbol]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                cluster_symbols.add(current)
                
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if len(cluster_symbols) > 1:
                # Calculate cluster stats
                cluster_value = sum(position_map[s].value for s in cluster_symbols)
                
                # Average correlation within cluster
                correlations = []
                for s1 in cluster_symbols:
                    for s2 in cluster_symbols:
                        if s1 < s2:
                            corr = corr_matrix.get((s1, s2), 0)
                            correlations.append(corr)
                
                avg_corr = sum(correlations) / len(correlations) if correlations else 0
                risk_concentration = (cluster_value / total_value) * avg_corr * 100
                
                clusters.append(Cluster(
                    id=cluster_id,
                    symbols=cluster_symbols,
                    total_value=cluster_value,
                    avg_correlation=avg_corr,
                    risk_concentration=risk_concentration
                ))
                cluster_id += 1
        
        return sorted(clusters, key=lambda x: x.risk_concentration, reverse=True)
    
    def _calculate_sector_exposure(
        self,
        positions: List[Position],
        total_value: float
    ) -> Dict[str, float]:
        """Calculate percentage exposure by sector."""
        sector_values = defaultdict(float)
        
        for p in positions:
            sector_values[p.sector] += p.value
        
        return {
            sector: (value / total_value) * 100
            for sector, value in sector_values.items()
        }
    
    def _calculate_risk_score(
        self,
        positions: List[Position],
        high_corr_pairs: List[CorrelationPair],
        clusters: List[Cluster],
        sector_exposure: Dict[str, float]
    ) -> float:
        """
        Calculate overall concentration risk score (0-100).
        Higher = more risk.
        """
        score = 0.0
        
        # Factor 1: Number of high correlation pairs (max 25 points)
        pair_risk = min(len(high_corr_pairs) * 5, 25)
        score += pair_risk
        
        # Factor 2: Cluster concentration (max 30 points)
        if clusters:
            max_cluster_risk = max(c.risk_concentration for c in clusters)
            score += min(max_cluster_risk * 0.5, 30)
        
        # Factor 3: Sector concentration (max 25 points)
        max_sector = max(sector_exposure.values()) if sector_exposure else 0
        if max_sector > self.max_sector_pct:
            excess = max_sector - self.max_sector_pct
            score += min(excess, 25)
        
        # Factor 4: Portfolio Herfindahl index (concentration) (max 20 points)
        total_value = sum(p.value for p in positions)
        herfindahl = sum((p.value / total_value) ** 2 for p in positions) if total_value > 0 else 0
        # Normalize: 1 position = 1.0, infinite positions = 0
        concentration_score = herfindahl * 20
        score += min(concentration_score, 20)
        
        return min(100, score)
    
    def _generate_recommendations(
        self,
        positions: List[Position],
        high_corr_pairs: List[CorrelationPair],
        clusters: List[Cluster],
        sector_exposure: Dict[str, float],
        risk_score: float,
        total_value: float
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        position_map = {p.symbol: p for p in positions}
        
        # High correlation pair recommendations
        for pair in high_corr_pairs[:3]:  # Top 3
            p1, p2 = pair.symbol1, pair.symbol2
            v1, v2 = position_map[p1].value, position_map[p2].value
            combined = v1 + v2
            
            if combined / total_value > 0.20:
                recommendations.append(
                    f"⚠️  {p1} & {p2} are {pair.correlation:.0%} correlated "
                    f"and comprise {(combined/total_value)*100:.1f}% of portfolio. "
                    f"Consider reducing one position."
                )
        
        # Cluster recommendations
        for cluster in clusters[:2]:  # Top 2 clusters
            symbols_str = ", ".join(sorted(cluster.symbols)[:5])
            if len(cluster.symbols) > 5:
                symbols_str += f" (+{len(cluster.symbols) - 5} more)"
            
            recommendations.append(
                f"🔗 Cluster detected: {symbols_str} "
                f"(avg correlation: {cluster.avg_correlation:.0%}, "
                f"{cluster.risk_concentration:.1f}% risk concentration)"
            )
        
        # Sector recommendations
        for sector, pct in sorted(sector_exposure.items(), key=lambda x: x[1], reverse=True):
            if pct > self.max_sector_pct:
                excess = pct - self.max_sector_pct
                recommendations.append(
                    f"📊 {sector.upper()} exposure at {pct:.1f}% "
                    f"({excess:.1f}% over {self.max_sector_pct}% limit). "
                    f"Consider diversifying into other sectors."
                )
        
        # Overall risk recommendation
        if risk_score >= self.high_risk_threshold:
            recommendations.append(
                f"🚨 HIGH CONCENTRATION RISK: Score {risk_score:.0f}/100. "
                f"Immediate rebalancing recommended."
            )
        elif risk_score >= 50:
            recommendations.append(
                f"⚡ Moderate concentration risk: Score {risk_score:.0f}/100. "
                f"Monitor correlations and consider gradual rebalancing."
            )
        else:
            recommendations.append(
                f"✅ Portfolio well diversified: Score {risk_score:.0f}/100. "
                f"Maintain current allocation."
            )
        
        return recommendations
    
    def suggest_hedge(
        self,
        positions: List[Position],
        report: RiskReport,
        available_hedges: List[str] = None
    ) -> List[Dict]:
        """Suggest hedging strategies based on exposure."""
        available_hedges = available_hedges or ["SPY", "QQQ", "IWM", "VIX", "TLT", "GLD"]
        total_value = sum(p.value for p in positions)
        
        suggestions = []
        
        # Calculate portfolio beta
        portfolio_beta = sum(
            (p.value / total_value) * p.beta for p in positions
        ) if total_value > 0 else 1.0
        
        # Suggest market hedge if high beta
        if portfolio_beta > 1.2:
            hedge_value = total_value * (portfolio_beta - 1.0) * 0.5
            suggestions.append({
                "type": "market_hedge",
                "instrument": "SPY puts" if "SPY" in available_hedges else "Index puts",
                "suggested_value": hedge_value,
                "reason": f"Portfolio beta {portfolio_beta:.2f} suggests high market sensitivity"
            })
        
        # Suggest sector hedges for concentrated sectors
        for sector, pct in report.sector_exposure.items():
            if pct > 30:
                sector_etf = self._sector_to_etf(sector)
                if sector_etf:
                    suggestions.append({
                        "type": "sector_hedge",
                        "instrument": f"{sector_etf} puts or short",
                        "suggested_value": total_value * (pct / 100) * 0.3,
                        "reason": f"{sector} exposure at {pct:.1f}%"
                    })
        
        return suggestions
    
    def _sector_to_etf(self, sector: str) -> Optional[str]:
        """Map sector to hedging ETF."""
        mapping = {
            "tech": "XLK",
            "financial": "XLF",
            "healthcare": "XLV",
            "energy": "XLE",
            "consumer": "XLY",
            "industrial": "XLI",
            "utilities": "XLU",
            "materials": "XLB",
            "real_estate": "XLRE",
        }
        return mapping.get(sector.lower())


def diversification_score(positions: List[Position]) -> float:
    """
    Quick diversification score (0-100).
    100 = perfectly diversified, 0 = single position.
    """
    n = len(positions)
    if n <= 1:
        return 0.0
    
    total = sum(p.value for p in positions)
    if total == 0:
        return 0.0
    
    # Herfindahl index
    weights = [p.value / total for p in positions]
    herf = sum(w ** 2 for w in weights)
    
    # Convert to diversification score (0-100)
    # Perfect equal weight = 1/n, Single position = 1
    perfect = 1 / n
    score = max(0, (herf - 1) / (perfect - 1)) * 100 if herf != 1 else 0
    
    return min(100, score)


# === Examples ===

if __name__ == "__main__":
    print("=" * 70)
    print("Correlation Risk Analyzer")
    print("=" * 70)
    
    # Example portfolio with concentration issues
    positions = [
        # Tech cluster (high correlation)
        Position("AAPL", 50000, "tech", beta=1.2, volatility=0.25),
        Position("MSFT", 45000, "tech", beta=1.1, volatility=0.22),
        Position("GOOGL", 40000, "tech", beta=1.15, volatility=0.24),
        Position("NVDA", 35000, "tech", beta=1.8, volatility=0.45),
        
        # Financial positions
        Position("JPM", 30000, "financial", beta=1.0, volatility=0.20),
        Position("BAC", 25000, "financial", beta=1.1, volatility=0.22),
        
        # Healthcare
        Position("JNJ", 20000, "healthcare", beta=0.7, volatility=0.15),
        Position("PFE", 15000, "healthcare", beta=0.6, volatility=0.18),
        
        # Diversifiers
        Position("XOM", 20000, "energy", beta=0.9, volatility=0.28),
        Position("GLD", 15000, "commodity", beta=0.0, volatility=0.15),
    ]
    
    total = sum(p.value for p in positions)
    print(f"\nPortfolio: ${total:,.0f} across {len(positions)} positions")
    
    # Analyze
    analyzer = CorrelationRiskAnalyzer(
        correlation_threshold=0.65,
        max_sector_pct=30.0
    )
    
    report = analyzer.analyze(positions)
    
    # Display results
    print(f"\n{'=' * 70}")
    print(f"Concentration Risk Score: {report.concentration_risk_score:.1f}/100")
    print(f"Status: {'⚠️  HIGH RISK' if report.concentration_risk_score >= 80 else '⚡ MODERATE' if report.concentration_risk_score >= 50 else '✅ DIVERSIFIED'}")
    print(f"{'=' * 70}")
    
    # Sector exposure
    print(f"\n📊 Sector Exposure:")
    for sector, pct in sorted(report.sector_exposure.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(pct / 2)
        warning = " ⚠️" if pct > 30 else ""
        print(f"  {sector:<12} {pct:>5.1f}% {bar}{warning}")
    
    # High correlation pairs
    if report.high_correlation_pairs:
        print(f"\n🔗 High Correlation Pairs (>65%):")
        for pair in report.high_correlation_pairs[:5]:
            print(f"  {pair.symbol1} ↔ {pair.symbol2}: {pair.correlation:.0%} "
                  f"(risk: {pair.risk_contribution:.1f}%)")
    
    # Clusters
    if report.clusters:
        print(f"\n📦 Correlation Clusters:")
        for cluster in report.clusters:
            symbols = ", ".join(sorted(cluster.symbols))
            print(f"  Cluster {cluster.id}: {symbols}")
            print(f"    Value: ${cluster.total_value:,.0f} | "
                  f"Avg corr: {cluster.avg_correlation:.0%} | "
                  f"Risk: {cluster.risk_concentration:.1f}%")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    for rec in report.recommendations:
        print(f"  • {rec}")
    
    # Hedge suggestions
    print(f"\n🛡️  Hedge Suggestions:")
    hedges = analyzer.suggest_hedge(positions, report)
    for hedge in hedges:
        print(f"  • {hedge['type']}: {hedge['instrument']}")
        print(f"    Suggested: ${hedge['suggested_value']:,.0f}")
        print(f"    Reason: {hedge['reason']}")
    
    # Diversification score
    print(f"\n📈 Diversification Score: {diversification_score(positions):.1f}/100")
    
    print("\n" + "=" * 70)
    print("Key Insight: Diversification isn't just # of positions—")
    print("it's how they move together. Correlated positions = hidden risk.")
    print("=" * 70)
```

## Correlation Threshold Guide

| Correlation | Relationship | Risk Level |
|-------------|--------------|------------|
| 0.90+ | Nearly identical | ⚠️ Extreme |
| 0.70-0.90 | Highly correlated | ⚡ High |
| 0.50-0.70 | Moderately correlated | ⚡ Moderate |
| 0.30-0.50 | Weak correlation | ✅ Low |
| <0.30 | Uncorrelated | ✅ Diversified |
| Negative | Inverse | ✅ Hedge |

## Risk Score Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| 0-30 | Well diversified | Maintain |
| 30-50 | Slight concentration | Monitor |
| 50-70 | Moderate concentration | Reduce gradually |
| 70-85 | High concentration | Rebalance soon |
| 85-100 | Extreme concentration | Immediate action |

## Quick Reference

```python
# Standard analysis
analyzer = CorrelationRiskAnalyzer(correlation_threshold=0.70)
report = analyzer.analyze(positions)

if not report.is_diversified():
    print("Reduce correlated positions:", report.recommendations)

# Check specific pair
corr = report.correlation_matrix.get(("AAPL", "MSFT"), 0)
if corr > 0.80:
    print("AAPL and MSFT move together—reduce one")

# Get hedge suggestions
hedges = analyzer.suggest_hedge(positions, report)
```

## Key Insights

1. **Sector ≠ diversification** — Tech stocks move together regardless of sub-sector
2. **Beta clustering** — High-beta stocks correlate in sell-offs
3. **2 uncorrelated positions > 10 correlated ones** — Quality over quantity
4. **Correlations spike in crises** — Normal times: 0.4, Crash times: 0.8+
5. **Hedges are positions too** — Cost of insurance, size appropriately

## Why This Matters

During the 2020 COVID crash:
- Diversified portfolios (low correlation) fell 15-20%
- Concentrated tech portfolios fell 35-40%
- "Diversified" portfolios with hidden correlation fell almost as much

**Correlation risk is the risk you don't see until it's too late.**

---

**Created by Ghost 👻 | Feb 20, 2026 | 13-min learning sprint**  
*Lesson: "I have 20 positions" means nothing if they all move together. Real diversification = low correlation. Measure it, manage it, or watch correlated drawdowns destroy your edge.*
