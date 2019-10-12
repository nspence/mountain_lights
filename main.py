import machine
from machine import Pin
from neopixel import NeoPixel
import utime
import urequests

STEP_MS = 250
NEOPIXEL_PIN = 2   # set GPIO2 (D4) to output to drive NeoPixels
NUM_PIXELS = 16
SUNRISE_DURATION = 600.0
SUNRISE_DURATION_MS = 300 * 1000.0
SUNRISE_COLORS_START = [(255, 176, 59), (227, 114, 173), (144, 132, 219)] # from center out
SUNRISE_COLORS_END = [(255, 183, 59), (255, 190, 90)] # from center out

class ColorPoint:
    def __init__(self, index, color):
        self.index = index
        self.color = color

    def __repr__(self):
        return "({0}, {1})".format(self.index, self.color)

class Pixel:
    def __init__(self, start_color, end_color=None, full_luminosity=1.0):
        self.start_color = start_color
        self.end_color = end_color or start_color
        self.full_luminosity = full_luminosity

    def __repr__(self):
        return "{0}".format(self.color)

    # state is between 0 and 1
    def color_at(self, state):
        color = tuple([(self.end_color[index] - v) * state + v for index, v in enumerate(self.start_color)])
        return tuple([self._normalize_color_value(v * self._luminosity_function(state) * self.full_luminosity) for v in color])

    def _normalize_color_value(self, v):
        return max(min(int(v), 255), 0)

    def _luminosity_function(self, state):
        return state**3

class Sky:
    def __init__(self, num_pixels, start_colors, end_colors):
        self.num_pixels = num_pixels
        self.start_colors = start_colors
        self.end_colors = end_colors
        self.lum_multipliers = self._lum_multplier_parabolic(self.num_pixels)
        self.start_gradient = self._mirrored_color_gradient(self.start_colors)
        self.end_gradient = self._mirrored_color_gradient(self.end_colors)
        self.pixels = [Pixel(self.start_gradient[i], end_color=self.end_gradient[i], full_luminosity=self.lum_multipliers[i]) for i in range(self.num_pixels)]

    def colors_at(self, state):
        return [pixel.color_at(state) for pixel in self.pixels]

    def _lum_multplier_parabolic(self, n):
        midpoint = (n-1) / 2.0
        parabolic = lambda midpoint, x: -1 * ((x-midpoint)**2)/(midpoint**2.0) + 1.1
        return [min(1, parabolic(midpoint, i)) for i in range(n)]

    def _clip(self, color):
        tuple([max(min(v, 255), 0) for v in color])

    def _mirrored_color_gradient(self, colors, midpoint=None):
        colors = colors[::-1] + colors
        midpoint = midpoint or (self.num_pixels - 1) / 2.0
        color_points = [ColorPoint(index / float(len(colors) - 1) * (self.num_pixels - 1), color) for index, color in enumerate(colors)]

        results = []
        for i in range(self.num_pixels):
            color_point1 = None
            color_point2 = None
            for cp in color_points:
                if cp.index <= i:
                    color_point1 = cp
                if cp.index >= i:
                    color_point2 = color_point2 or cp
                    break
            difference = color_point2.index - color_point1.index
            ratio = 1 if difference == 0 else (i - color_point1.index) / difference
            results.append(self._merge_colors_weighted(color_point1.color, color_point2.color, ratio))
        return results

    def _merge_colors_weighted(self, color1, color2, ratio):
        return tuple([(color2[index] - v) * ratio + v for index, v in enumerate(color1)])

class NeoPixelRunner:
    def __init__(self, neopixel, sky, duration_ms, step_ms=STEP_MS):
        self.neopixel = neopixel
        self.sky = sky
        self.duration_ms = duration_ms
        self.step_ms = step_ms

    def run(self):
        start_time = utime.ticks_ms()
        elapsed_ms = 0

        while elapsed_ms < self.duration_ms:
            display_values = self.sky.colors_at(elapsed_ms / self.duration_ms)
            #  print(display_values)
            self._display_pixels(display_values)

            elapsed_ms = utime.ticks_diff(utime.ticks_ms(), start_time)
            utime.sleep_ms(self.step_ms)

    def _display_pixels(self, rgb_array):
        for i, color in enumerate(rgb_array):
          self.neopixel[i] = color
        self.neopixel.write()


def main():
    pin = Pin(NEOPIXEL_PIN, Pin.OUT)
    np = NeoPixel(pin, NUM_PIXELS)
    sky = Sky(NUM_PIXELS, SUNRISE_COLORS_START, SUNRISE_COLORS_END)
    runner = NeoPixelRunner(np, sky, SUNRISE_DURATION_MS)
    runner.run()


def get_sky_info():
    response = urequests.get("https://api.sunrise-sunset.org/json?lat=47.2529&lng=122.4443&formatted=0")
    if response.status_code != 200:
        return None
    response.json()['results']

def normalize_float_color(pixel):
    return tuple([max(min(int(v), 255), 0) for v in pixel])

def display_pixels(neo_pixel, rgb_array):
    for i, color in enumerate(rgb_array):
      #  neo_pixel[i] = normalize_float_color(rgb_array[i])
      neo_pixel[i] = color
    neo_pixel.write()

main()
