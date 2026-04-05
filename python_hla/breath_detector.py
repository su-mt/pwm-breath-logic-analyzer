from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame

# ── Thresholds ────────────────────────────────────────────────────────────────
DUTY_ZERO_THRESHOLD = 0.05   # below this  → treat as 0 %
DUTY_PEAK_THRESHOLD = 99.5   # above this  → treat as 100 %
TIMEOUT_SECONDS     = 4.0    # gap between PWM frames → reset state machine


class BreathDetector(HighLevelAnalyzer):
    """
    Stacks on top of the C++ PWM Decoder analyzer.
    Detects one full breath period (0 → 100 → 0) and emits an alternating
    high/low frame so the track looks like a square wave toggling every period.
    """

    result_types = {
        'breath_high': { 'format': 'Breath ↑  {{data.period_ms}} ms' },
        'breath_low':  { 'format': 'Breath ↓  {{data.period_ms}} ms' },
    }

    # ── States ────────────────────────────────────────────────────────────────
    WAIT_ZERO = 'WAIT_ZERO'   # haven't found a clean zero yet
    RISING    = 'RISING'      # duty is climbing toward 100 %
    FALLING   = 'FALLING'     # duty is descending toward 0 %

    def __init__(self):
        self.state        = self.WAIT_ZERO
        self.breath_start = None   # Time of the current period's start
        self.toggle       = False  # alternates the output frame type
        self.last_time    = None   # for timeout detection
        self.seen_nonzero = False  # ensures we don't start on a spurious zero

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _duty(self, frame) -> float:
        """
        Compute duty cycle from FrameV2 named fields sent by C++ LLA.
        pulse_width and period are in sample counts — no sample rate needed
        because we only need the ratio.
        """
        pulse  = frame.data.get('pulse_width', 0)
        period = frame.data.get('period', 0)

        if period == 0:
            return 0.0

        d = 100.0 * pulse / period

        # Apply tolerances agreed in architecture discussion
        if d < DUTY_ZERO_THRESHOLD:
            return 0.0
        if d > DUTY_PEAK_THRESHOLD:
            return 100.0
        return d

    def _timeout(self, frame) -> bool:
        """Return True if the gap since the last frame exceeds TIMEOUT_SECONDS."""
        if self.last_time is None:
            return False
        gap = float(frame.start_time - self.last_time)
        return gap > TIMEOUT_SECONDS

    def _reset(self):
        self.state        = self.WAIT_ZERO
        self.breath_start = None
        self.seen_nonzero = False

    def _emit(self, end_time) -> AnalyzerFrame:
        period_s  = float(end_time - self.breath_start)
        period_ms = round(period_s * 1000)

        frame_type  = 'breath_high' if not self.toggle else 'breath_low'
        self.toggle = not self.toggle

        return AnalyzerFrame(
            frame_type,
            self.breath_start,
            end_time,
            {'period_ms': period_ms}
        )

    # ── Main decode entry point ───────────────────────────────────────────────

    def decode(self, frame: AnalyzerFrame):
        # Only handle frames from our C++ PWM Decoder
        if frame.type != 'pwm':
            return None

        # Timeout guard — reset if signal was absent too long
        if self._timeout(frame):
            self._reset()
        self.last_time = frame.start_time

        duty   = self._duty(frame)
        result = None

        # ── WAIT_ZERO ─────────────────────────────────────────────────────────
        # Wait for the first clean zero that follows at least one non-zero duty.
        # This avoids starting mid-breath on spurious zeros at recording start.
        if self.state == self.WAIT_ZERO:
            if duty > DUTY_ZERO_THRESHOLD:
                self.seen_nonzero = True
            if duty == 0.0 and self.seen_nonzero:
                self.state        = self.RISING
                self.breath_start = frame.start_time

        # ── RISING ────────────────────────────────────────────────────────────
        elif self.state == self.RISING:
            if duty == 100.0:
                self.state = self.FALLING

        # ── FALLING ───────────────────────────────────────────────────────────
        elif self.state == self.FALLING:
            if duty == 0.0:
                result            = self._emit(frame.start_time)
                self.breath_start = frame.start_time  # start of next period
                self.state        = self.RISING

        return result
