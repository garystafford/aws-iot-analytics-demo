# Setup Notes for Raspberry Pi

Turn on SPI on Raspberry PI

```bash
sudo apt-get update
yes | sudo apt-get upgrade

yes | sudo apt-get install cmake libssl-dev libgpiod2

python3 -m pip install --user -r requirements.txt
```

## View MQTT Messages

```bash
yes | sudo apt-get install tcpdump
sudo tcpdump -i wlan0 port 443 -e -v -tttt
```

## Stop Collector Script

```bash
ps aux # find pid
kill <pid>
```

## References
-<https://learn.sparkfun.com/tutorials/raspberry-pi-spi-and-i2c-tutorial/all>
-<https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/>
-<https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup>
-<https://gpiozero.readthedocs.io/en/stable/recipes.html#motion-sensor>
-<https://danielmiessler.com/study/tcpdump/>
-<https://stackoverflow.com/a/41817024/580268>
