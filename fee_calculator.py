"""
Fee Calculator Module

Calculates trading fees for Kalshi contracts.

Kalshi uses a tiered fee structure:
- Contracts priced near 50¢: ~3.5% fee (highest)
- Contracts at extremes (near 0¢ or 100¢): ~1% fee (lowest)
- Maker orders (limit orders): 50% discount on fees

This module provides accurate fee calculations for profit analysis.
"""
from typing import Dict, List


class FeeCalculator:
    """Calculate trading fees for Kalshi contracts."""
    
    # Fee structure based on contract price (in cents)
    # Fees are typically higher for contracts priced near 50¢
    # This is an approximation - actual fees may vary
    FEE_SCHEDULE = {
        (0, 5): 0.01,      # Very low prices: 1% fee
        (5, 10): 0.015,    # Low prices: 1.5% fee
        (10, 20): 0.02,    # Low-medium: 2% fee
        (20, 30): 0.025,   # Medium-low: 2.5% fee
        (30, 40): 0.03,    # Medium: 3% fee
        (40, 50): 0.035,   # Medium-high: 3.5% fee
        (50, 60): 0.035,   # Medium-high: 3.5% fee
        (60, 70): 0.03,    # Medium: 3% fee
        (70, 80): 0.025,   # Medium-low: 2.5% fee
        (80, 90): 0.02,    # Low-medium: 2% fee
        (90, 95): 0.015,   # High prices: 1.5% fee
        (95, 100): 0.01,   # Very high prices: 1% fee
    }
    
    # Maker vs Taker fees (makers pay less)
    MAKER_FEE_MULTIPLIER = 0.5  # Makers pay 50% of taker fees
    
    @classmethod
    def get_fee_rate(cls, price_cents: int, is_maker: bool = False) -> float:
        """
        Get the fee rate for a given contract price.
        
        Args:
            price_cents: Contract price in cents (0-100)
            is_maker: Whether this is a maker order (resting on book)
        
        Returns:
            Fee rate as a decimal (e.g., 0.035 for 3.5%)
        """
        # Clamp price to valid range
        price_cents = max(0, min(100, price_cents))
        
        # Find the appropriate fee bracket
        for (min_price, max_price), fee_rate in cls.FEE_SCHEDULE.items():
            if min_price <= price_cents < max_price:
                base_fee = fee_rate
                break
        else:
            # Default to highest fee if somehow out of range
            base_fee = 0.035
        
        # Apply maker discount if applicable
        if is_maker:
            return base_fee * cls.MAKER_FEE_MULTIPLIER
        
        return base_fee
    
    @classmethod
    def calculate_fee(cls, price_cents: int, quantity: int, is_maker: bool = False) -> float:
        """
        Calculate the total fee for a trade.
        
        Args:
            price_cents: Contract price in cents
            quantity: Number of contracts
            is_maker: Whether this is a maker order
        
        Returns:
            Total fee in dollars
        """
        fee_rate = cls.get_fee_rate(price_cents, is_maker)
        total_cost = (price_cents / 100) * quantity
        return total_cost * fee_rate
    
    @classmethod
    def calculate_net_profit(cls, gross_profit: float, trades: List[Dict], 
                            all_maker: bool = False) -> float:
        """
        Calculate net profit after fees for multiple trades.
        
        Args:
            gross_profit: Gross profit before fees
            trades: List of trade dicts with 'price' and 'quantity' keys
            all_maker: Whether all trades are maker orders
        
        Returns:
            Net profit after fees
        """
        total_fees = 0.0
        for trade in trades:
            fee = cls.calculate_fee(
                trade['price'],
                trade['quantity'],
                is_maker=all_maker
            )
            total_fees += fee
        
        return gross_profit - total_fees

