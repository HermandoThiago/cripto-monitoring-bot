from trading.monitoring import MonitoringPrice

monitoring = MonitoringPrice(
    symbol="BTCUSDT",
    timeframe="1m",
    position=0
)

monitoring.start_monitoring(historical_days=1/2)