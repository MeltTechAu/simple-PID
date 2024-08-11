import board
import digitalio
import adafruit_max31855

try:
    spi = board.SPI()
    cs = digitalio.DigitalInOut(board.D8)
    sensor = adafruit_max31855.MAX31855(spi, cs)

    while True:
        temp = sensor.temperature
        if temp is not None:
            print(f"Temperature: {temp} °C")
        else:
            print("Failed to read temperature")
        time.sleep(1)

except Exception as e:
    print(f"Error: {e}")
