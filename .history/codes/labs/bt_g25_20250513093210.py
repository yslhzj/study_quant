import backtrader as bt
import math

class AShareETFSizer(bt.Sizer):
    params = (
        # Parameters moved from strategy or new for sizer
        ('etf_type_param_name', 'etf_type'), # Name of the etf_type param in strategy
        ('risk_per_trade_trend', 0.01),
        ('risk_per_trade_range', 0.005),
        ('max_position_per_etf_percent', 0.30),
        # 'max_total_account_risk_percent' is harder to implement purely in sizer
        # as it requires knowledge of all other potential trades/positions' risk.
        # For simplicity, we'll focus the sizer on single trade constraints.
        # Strategy can provide an overall risk check before calling buy/sell.
        ('trend_stop_loss_atr_mult_param_name', 'trend_stop_loss_atr_mult'),
        ('range_stop_loss_buffer_param_name', 'range_stop_loss_buffer'),
        ('atr_indicator_name_prefix', 'atr_'), # If strategy stores ATRs like self.atr_DATANAME
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        if not isbuy: # This strategy/sizer is for long entries
            return 0

        position = self.broker.getposition(data)
        if position.size != 0: # Already in market for this data
            return 0 

        d_name = data._name
        strategy = self.strategy # Access to the strategy instance

        # Get etf_type for this data (assuming it's a global strategy param for now)
        # A more robust way would be if the strategy provides a per-data etf_type
        current_etf_type = getattr(strategy.params, self.p.etf_type_param_name, 'trend') # Default to trend

        if current_etf_type == 'trend':
            risk_per_trade_percent = self.p.risk_per_trade_trend
            atr_mult_param_name = self.p.trend_stop_loss_atr_mult_param_name
            atr_mult = getattr(strategy.params, atr_mult_param_name)
            
            # Sizer needs to access ATR calculated by the strategy
            # Assuming strategy stores ATR indicators in a dict like self.atrs keyed by data name
            if not hasattr(strategy, 'atrs') or d_name not in strategy.atrs:
                strategy.log(f"Sizer: ATR indicator for {d_name} not found in strategy.atrs. Skipping trade.", data=data)
                return 0
            current_atr = strategy.atrs[d_name][0]
            if math.isnan(current_atr) or current_atr <= 1e-9:
                strategy.log(f"Sizer: Invalid ATR value ({current_atr}) for {d_name}. Skipping trade.", data=data)
                return 0

            entry_price_ref = data.close[0] # Reference for SL calculation
            stop_loss_price_ref = entry_price_ref - atr_mult * current_atr
        
        elif current_etf_type == 'range':
            risk_per_trade_percent = self.p.risk_per_trade_range
            sl_buffer_param_name = self.p.range_stop_loss_buffer_param_name
            sl_buffer = getattr(strategy.params, sl_buffer_param_name)

            entry_price_ref = data.close[0] # Reference for SL calculation
            # For range, SL is based on current low. Sizer uses current data.
            # Strategy will use current low for its bracket order's stop price.
            # Sizer calculates its reference SL similarly.
            if not hasattr(strategy, 'lows') or d_name not in strategy.lows:
                strategy.log(f"Sizer: Low price series for {d_name} not found in strategy.lows. Skipping trade.", data=data)
                return 0

            stop_loss_price_ref = strategy.lows[d_name][0] * (1 - sl_buffer)
        else:
            strategy.log(f"Sizer: Unknown ETF type '{current_etf_type}' for {d_name}. Skipping trade.", data=data)
            return 0

        if stop_loss_price_ref >= entry_price_ref:
            strategy.log(
                f"Sizer: Stop loss {stop_loss_price_ref:.2f} not below entry {entry_price_ref:.2f} for {d_name}. Cannot size.", data=data)
            return 0

        risk_per_share = entry_price_ref - stop_loss_price_ref
        if risk_per_share <= 1e-9:
            strategy.log(
                f"Sizer: Risk per share for {d_name} is zero or too small ({risk_per_share:.2f}). Cannot size.", data=data)
            return 0

        # Access current_risk_multiplier from strategy
        effective_risk_percent = risk_per_trade_percent * strategy.current_risk_multiplier
        equity = self.broker.getvalue()
        
        max_amount_to_risk_on_this_trade = equity * effective_risk_percent
        
        size_raw = max_amount_to_risk_on_this_trade / risk_per_share
        size = int(size_raw / 100) * 100 # Round down for A-shares

        if size <= 0:
            strategy.log(
                f"Sizer: Calculated size for {d_name} based on risk is {size}. Risk/share: {risk_per_share:.2f}. Amount to risk: {max_amount_to_risk_on_this_trade:.2f}", data=data)
            return 0

        # Max position value per ETF
        max_pos_value_for_etf = equity * self.p.max_position_per_etf_percent
        price_for_value_calc = entry_price_ref # Use the same reference price
        
        if price_for_value_calc <= 1e-9:
            strategy.log(
                f"Sizer: Invalid price ({price_for_value_calc:.2f}) for {d_name} value calculation.", data=data)
            return 0
            
        size_limited_by_max_etf_pos = int(max_pos_value_for_etf / price_for_value_calc / 100) * 100
        if size > size_limited_by_max_etf_pos:
            strategy.log(
                f"Sizer: Size for {d_name} reduced from {size} to {size_limited_by_max_etf_pos} by max_position_per_etf_percent.", data=data)
            size = size_limited_by_max_etf_pos

        if size <= 0:
            strategy.log(
                f"Sizer: Calculated size for {d_name} after max ETF position limit is {size}.", data=data)
            return 0

        # Cash limit
        potential_trade_total_cost = size * price_for_value_calc
        if potential_trade_total_cost > cash:
            size_limited_by_cash = int(cash / price_for_value_calc / 100) * 100
            if size_limited_by_cash < size:
                strategy.log(
                    f"Sizer: Size for {d_name} reduced from {size} to {size_limited_by_cash} by cash limit. Cash: {cash:.2f}, Cost approx: {potential_trade_total_cost:.2f}", data=data)
                size = size_limited_by_cash
        
        if size <= 0:
            strategy.log(
                f"Sizer: Final calculated size for {d_name} is {size}. Cannot place order.", data=data)
            return 0
        
        strategy.log(f"Sizer for {d_name} calculated size: {size} based on entry_ref: {entry_price_ref:.2f}, sl_ref: {stop_loss_price_ref:.2f}", data=data)
        return size
