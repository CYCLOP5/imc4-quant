from collections import defaultdict
from functools import reduce
from prosperity4bt.models.output import BacktestResult

class ResultMerger:

    def __init__(self, merge_timestamps: bool=True, merge_profit_loss: bool=False):
        self.merge_timestamps = merge_timestamps
        self.merge_profit_loss = merge_profit_loss

    def merge(self, results: list[BacktestResult]) -> BacktestResult:
        merged_result = reduce(lambda a, b: self.__merge_results(a, b), results)
        return merged_result

    def __merge_results(self, a: BacktestResult, b: BacktestResult) -> BacktestResult:
        sandbox_logs = a.sandbox_logs[:]
        activity_logs = a.activity_logs[:]
        trades = a.trades[:]
        timestamp_offset = self.__timestamp_offset(a)
        sandbox_logs.extend([row.with_offset(timestamp_offset) for row in b.sandbox_logs])
        trades.extend([row.with_offset(timestamp_offset) for row in b.trades])
        profit_loss_offsets = self.__profile_loss_offset(a)
        activity_logs.extend([row.with_offset(timestamp_offset, profit_loss_offsets[row.symbol]) for row in b.activity_logs])
        return BacktestResult(a.round_num, a.day_num, sandbox_logs, activity_logs, trades)

    def __timestamp_offset(self, previous: BacktestResult) -> int:
        if not self.merge_timestamps:
            return 0
        last_timestamp = previous.activity_logs[-1].timestamp
        return last_timestamp + 100

    def __profile_loss_offset(self, previous: BacktestResult) -> dict[str, float]:
        profit_loss_offsets = defaultdict(float)
        last_timestamp = previous.activity_logs[-1].timestamp
        last_activities = [al for al in previous.activity_logs if al.timestamp == last_timestamp]
        for activity in last_activities:
            profit_loss_offsets[activity.symbol] = activity.profit_loss if self.merge_profit_loss else 0
        return profit_loss_offsets
