from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame

# ── Thresholds ────────────────────────────────────────────────────────────────
DUTY_ZERO_THRESHOLD = 0.05   # below this  → treat as 0 %
DUTY_PEAK_THRESHOLD = 99.5   # above this  → treat as 100 %
BREATH_EDGE_DUTY    = 90.0   # edge detection threshold (duty %)
EDGE_HYSTERESIS     = 1.0    # suppress chatter around threshold
TIMEOUT_SECONDS     = 4.0    # gap between PWM frames → reset state machine


class BreathDetector(HighLevelAnalyzer):
    """
    Stacks on top of the C++ PWM Decoder analyzer.
    Detects one full breath period (0 → 100 → 0) and emits an alternating
    high/low frame so the track looks like a square wave toggling every period.
    """

    result_types = {
        'breath_period': { 'format': '{{data.period_ms}} ms' },
    }

    # ── States ────────────────────────────────────────────────────────────────
    BELOW = 'BELOW'
    ABOVE = 'ABOVE'

    def __init__(self):
        self.state        = None
        self.breath_start = None   # Time of the current period's start
        self.last_time    = None   # for timeout detection

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _duty(self, frame) -> float:
        """
        Compute duty cycle from the incoming LLA frame.
        Supports both FrameV2 named fields and legacy Frame data keys.
        """
        pulse, period = self._extract_measurements(frame)

        if period == 0:
            return 0.0

        d = 100.0 * pulse / period

        # Apply tolerances agreed in architecture discussion
        if d < DUTY_ZERO_THRESHOLD:
            return 0.0
        if d > DUTY_PEAK_THRESHOLD:
            return 100.0
        return d

    def _extract_measurements(self, frame):
        """
        Return (pulse_width, period) from common LLA frame formats.
        """
        data = frame.data or {}

        # Preferred: FrameV2 from C++ analyzer.
        if 'pulse_width' in data and 'period' in data:
            return data.get('pulse_width', 0), data.get('period', 0)

        # Fallback: legacy Frame fields forwarded by Logic into HLA.
        if 'data1' in data and 'data2' in data:
            return data.get('data1', 0), data.get('data2', 0)

        return 0, 0

    def _timeout(self, frame) -> bool:
        """Return True if the gap since the last frame exceeds TIMEOUT_SECONDS."""
        if self.last_time is None:
            return False
        gap = float(frame.start_time - self.last_time)
        return gap > TIMEOUT_SECONDS

    def _reset(self):
        self.state        = None
        self.breath_start = None

    def _band(self, duty: float):
        low = BREATH_EDGE_DUTY - EDGE_HYSTERESIS
        high = BREATH_EDGE_DUTY + EDGE_HYSTERESIS

        if duty <= low:
            return self.BELOW
        if duty >= high:
            return self.ABOVE
        return None

    def _emit(self, end_time) -> AnalyzerFrame:
        period_s  = float(end_time - self.breath_start)
        period_ms = round(period_s * 1000)

        return AnalyzerFrame(
            'breath_period',
            self.breath_start,
            end_time,
            {'period_ms': period_ms}
        )

    # ── Main decode entry point ───────────────────────────────────────────────

    def decode(self, frame: AnalyzerFrame):
        # Accept both FrameV2 and legacy frames from the stacked C++ analyzer.
        _, period = self._extract_measurements(frame)
        if period == 0:
            return None

        # Timeout guard — reset if signal was absent too long
        if self._timeout(frame):
            self._reset()
        self.last_time = frame.start_time

        duty = self._duty(frame)
        band = self._band(duty)
        result = None

        # Need a stable side of threshold before looking for crossings.
        if self.state is None:
            if band is not None:
                self.state = band
            return None

        # Ignore samples in the hysteresis zone.
        if band is None:
            return None

        # Emit one breath period on each rising crossing through threshold duty.
        if self.state == self.BELOW and band == self.ABOVE:
            if self.breath_start is not None:
                result = self._emit(frame.start_time)
            self.breath_start = frame.start_time

        self.state = band

        return result
