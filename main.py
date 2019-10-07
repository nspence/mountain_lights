import machine
from machine import Pin
from neopixel import NeoPixel
import time
import urequests

STEP_MS = 250
NEOPIXEL_PIN = 2   # set GPIO2 (D4) to output to drive NeoPixels
NUM_PIXELS = 16
SUNRISE_DURATION = 300.0
SUNRISE_DURATION_MS = 300 * 1000.0
SUNRISE_COLORS_START = [(255, 190, 90), (227, 114, 173), (144, 132, 219)] # from center out
SUNRISE_COLORS_END = [(255, 190, 90), (227, 114, 173)] # from center out

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
        return tuple([int(v * state * self.full_luminosity) for v in color])

class Sky:
    def __init__(self, num_pixels, start_colors, end_colors):
        self.num_pixels = num_pixels
        self.start_colors = start_colors
        self.end_colors = end_colors
        self.lum_multipliers = _lum_multplier_parabolic(num_pixels)
        self.start_gradient = _mirrored_color_gradient(start_colors)
        self.end_gradient = _mirrored_color_gradient(end_colors)
        self.pixels = [Pixel(start_gradient[i], end_color=end_gradient[i], full_luminosity=lum_multipliers[i]) for i in range(num_pixels)]

    def colors_at(self, state):
        return [pixel.color_at(state) for pixel in pixels]

    def _lum_multplier_parabolic(self, n):
        midpoint = (n-1) / 2.0
        parabolic = lambda midpoint, x: -1 * ((x-midpoint)**2)/(midpoint**2.0) + 1.1
        return [_clip(parabolic(midpoint, i)) for i in range(n)]

    def _clip(self, color):
        tuple([max(min(v, 255), 0) for v in color])

    def _mirrored_color_gradient(self, colors, midpoint=None):
        colors = colors[::-1] + colors
        midpoint = midpoint or (num_pixels - 1) / 2.0
        color_points = [ColorPoint(index / float(len(colors) - 1) * (num_pixels - 1), color) for index, color in enumerate(colors)]

        results = []
        for i in range(num_pixels):
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
            results.append(_merge_colors_weighted(color_point1.color, color_point2.color, ratio))
        return results

    def _merge_colors_weighted(self, color1, color2, ratio):
        return tuple([(color2[index] - v) * ratio + v for index, v in enumerate(color1)])


def main():
    pin = Pin(NEOPIXEL_PIN, Pin.OUT)
    np = NeoPixel(pin, NUM_PIXELS)
    #  colors = mirrored_color_gradient(NUM_PIXELS, colors=SUNRISE_COLORS)
    #  lum_multipliers = lum_multplier_parabolic(NUM_PIXELS)
    sky = Sky(NUM_PIXELS, SUNRISE_COLORS_START, SUNRISE_COLORS_END)

    start_time = time.tick_ms()
    elapsed_ms = 0

    while elapsed_ms < SUNRISE_DURATION_MS:
        display_values = sky.colors_at(elapsed_ms / SUNRISE_DURATION_MS)
        #  display_values = apply_single_lum_multiplier(apply_lum_array(colors, lum_multipliers), elapsed_ms / SUNRISE_DURATION_MS)
        print(display_values)
        display_pixels(np, display_values)

        elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
        time.sleep_ms(STEP_MS)

def get_sky_info():
    response = urequests.get("https://api.sunrise-sunset.org/json?lat=47.2529&lng=122.4443&formatted=0")
    if response.status_code != 200:
        return None
    response.json()['results']

#  def apply_single_lum_multiplier(rgb_array, luminosity):
    #  return [apply_lum_multiplier(pixel, luminosity) for pixel in rgb_array]

#  def apply_lum_array(rgb_array, lum_array):
    #  return [apply_lum_multiplier(pixel, lum_array[index]) for index, pixel in enumerate(rgb_array)]

#  def apply_lum_multiplier(pixel, lum_value):
    #  return tuple([v * lum_value for v in pixel])

def normalize_float_color(pixel):
    return tuple([int(v) for v in pixel])

def display_pixels(neo_pixel, rgb_array):
    for color in rgb_array:
      #  neo_pixel[i] = normalize_float_color(rgb_array[i])
      neo_pixel[i] = color
    neo_pixel.write()

main()
