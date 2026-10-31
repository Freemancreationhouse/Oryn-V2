# ORYN CP2E — Magic Home RGB Wi-Fi Add-on (candidate)

- Additive, isolated provider: `magic_home`. Does not change 10:1 ratio, machine motion, GRBL, homing, patterns, WLED or GPIO LED paths.
- For the pictured 12–24 V RGB (R/G/B common positive) device, **first pair and test the strip using Magic Home Pro over a 2.4 GHz Wi-Fi LAN**.
- Find its IPv4 address in the router DHCP clients (preferred: reserve this address).
- Put the ORYN Windows PC on the same LAN; allow local TCP port 5577.
- In ORYN **System / Settings → LED Controller → Magic Home RGB (Wi-Fi)**, enter the IPv4 address and save. Then choose **Light** to test Check connection, ON, OFF, Apply color and brightness.
- Legacy Magic Home RGB TCP protocol only. A newer device with another protocol may fail and requires device-specific verification. No cloud account or API key is required by ORYN for local control.
- RGB strip (4 wire) is **not** WS2812 addressable; effect control is solid color/basic mode only. WLED effect indexes must not be sent to this controller.
- If already paired and working, DO NOT reset it. Maintain proper DC voltage/current, wire with power disconnected, and keep controller/strip separate from GRBL motor supply control.
- The new interface was exercised with loopback simulated Magic Home responses, not with user's physical LED controller.

## Optional Windows IP discovery

Run `DISCOVER_MAGIC_HOME_LED_WINDOWS.cmd` from the extracted `oryn` folder. It broadcasts a legacy, read-only UDP discovery request; verify any IP against your router or Magic Home Pro app. Some variants do not respond. No motors are controlled by this script.
