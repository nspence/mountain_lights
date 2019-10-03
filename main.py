import machine
from machine import Pin
from neopixel import NeoPixel
import time
import urequests

NEOPIXEL_PIN = 2   # set GPIO2 (D4) to output to drive NeoPixels
NUM_PIXELS = 16
SUNRISE_DURATION = 300.0
SUNRISE_COLOR = (251, 171, 23)

class ColorPoint:
    def __init__(self, index, color):
        self.index = index
        self.color = color

    def __repr__(self):
        return "({0}, {1})".format(self.index, self.color)

def main():
    pin = Pin(NEOPIXEL_PIN, Pin.OUT)
    np = NeoPixel(pin, NUM_PIXELS)
    colors = [SUNRISE_COLOR for _i in range(NUM_PIXELS)]
    result = mirrored_color_gradient(NUM_PIXELS, colors=[SUNRISE_COLOR, (255,0,0)])
    lum_multipliers = lum_multplier_parabolic(NUM_PIXELS)

    for sec in range(SUNRISE_DURATION):
        display_values = apply_single_lum_multiplier(apply_lum_array(colors, lum_multipliers), sec / SUNRISE_DURATION)
        print(display_values)
        display_pixels(np, display_values)
        time.sleep(1)

def get_sky_info():
    response = urequests.get("https://api.sunrise-sunset.org/json?lat=47.2529&lng=122.4443&formatted=0")
    if response.status_code != 200:
        return None
    response.json()['results']

def apply_single_lum_multiplier(rgb_array, luminosity):
    return [apply_lum_multiplier(pixel, luminosity) for pixel in rgb_array]

def apply_lum_array(rgb_array, lum_array):
    return [apply_lum_multiplier(pixel, lum_array[index]) for index, pixel in enumerate(rgb_array)]

def apply_lum_multiplier(pixel, lum_value):
    return tuple([v * lum_value for v in pixel])

def normalize_float_color(pixel):
    return tuple([int(v) for v in pixel])

def display_pixels(neo_pixel, rgb_array):
    for i in range(NUM_PIXELS):
      neo_pixel[i] = normalize_float_color(rgb_array[i])
    neo_pixel.write()

def lum_multplier_parabolic(n):
    midpoint = (n-1) / 2.0
    parabolic = lambda midpoint, x: -1 * ((x-midpoint)**2)/(midpoint**2.0) + 1
    return [parabolic(midpoint, i) for i in range(n)]

def mirrored_color_gradient(n, colors=[SUNRISE_COLOR], midpoint=None):
    colors = colors[::-1]
    midpoint = midpoint or (n - 1) / 2.0
    for color in colors[:-1]:
        colors.append(color)
    color_points = [ColorPoint(index / float(len(colors) - 1) * (n - 1), color) for index, color in enumerate(colors)]

    results = []
    for i in range(n):
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
        results.append(merge_colors_weighted(color_point1.color, color_point2.color, ratio))
    return results

def merge_colors_weighted(color1, color2, ratio):
    return tuple([(color1[index] - v) * ratio + v for index, v in enumerate(color2)])

main()
