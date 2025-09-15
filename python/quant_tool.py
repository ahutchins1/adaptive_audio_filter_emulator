import math

class FixedPointValue:
    def __init__(self, NB_total, NB_float, value, signed=True, rounding='trunc', overflow='saturate'):
        self.NB_total = NB_total
        self.NB_float = NB_float
        self.NB_int = NB_total - NB_float
        self.signed = signed
        self.rounding = rounding
        self.overflow = overflow
        self.scale = 2 ** NB_float

        if signed:
            self.max_value = (2 ** (NB_total - 1)) - 1
            self.min_value = -(2 ** (NB_total - 1))
        else:
            self.max_value = (2 ** NB_total) - 1
            self.min_value = 0

        self.value = self._clip_and_convert(value)

    def _round(self, value):
        """Implements rounding modes; uses math.floor() for negative truncation."""
        if self.rounding == 'trunc':
            return math.floor(value) if value < 0 else int(value)
        elif self.rounding == 'round':
            return round(value)
        elif self.rounding == 'round_even':
            fract, integer = math.modf(value)
            abs_int = abs(int(integer))
            if abs(fract) == 0.5:
                if abs_int % 2 == 0:
                    return int(integer)
                else:
                    return int(integer + math.copysign(1, value))
            else:
                return int(round(value))
        else:
            raise ValueError(f"Unsupported rounding mode: {self.rounding}")

    def _clip_and_convert(self, value):
        scaled = value * self.scale
        fixed_val = self._round(scaled)

        if fixed_val > self.max_value or fixed_val < self.min_value:
            if self.overflow == 'saturate':
                fixed_val = min(max(fixed_val, self.min_value), self.max_value)
            elif self.overflow == 'wrap':
                mask = (1 << self.NB_total) - 1
                fixed_val = fixed_val & mask
                if self.signed and fixed_val >= (1 << (self.NB_total - 1)):
                    fixed_val -= (1 << self.NB_total)
            else:
                raise OverflowError("Fixed-point overflow and unsupported overflow mode.")
        return int(fixed_val)

    def to_float(self):
        return self.value / self.scale

    def to_quant_float(self):
        return self.to_float()

    def to_hex(self):
        width = self.NB_total
        mask = (1 << width) - 1
        unsigned_value = self.value & mask
        hex_digits = (width + 3) // 4
        return f"0x{unsigned_value:0{hex_digits}X}"

    def to_binary(self):
        if self.value < 0 and self.signed:
            return bin((1 << self.NB_total) + self.value)[2:].zfill(self.NB_total)
        return bin(self.value)[2:].zfill(self.NB_total)

    def __repr__(self):
        mode = "S" if self.signed else "U"
        return f"<{self.value} ({self.to_float():.6f}) {mode}({self.NB_total - self.NB_float},{self.NB_float})>"

    def __eq__(self, other):
        return isinstance(other, FixedPointValue) and self.to_float() == other.to_float()

    def show_range(self):
        min_val = self.min_value / self.scale
        max_val = self.max_value / self.scale
        mode = "S" if self.signed else "U"
        print(f"{mode}({self.NB_total - self.NB_float},{self.NB_float}): {min_val:.6f} to {max_val:.6f}")
