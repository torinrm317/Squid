This python script is designed to take in the 7 Hex digit UID of a squid loyalty tag, and generate a .nfc file which can then be emulated on an nfc emulation device such as a flipper zero to get additional "stamps" on the squid loyalty app. (https://squidloyalty.ie/)

The script works both running directly from the flipper zero device or run from a desktop device. It works best running from desktop, then loading the .nfc files generated onto the flipper zero using the free qflipper software, as the micropython firmware that runs on the flipper zero requires a lot of ram, and will often crash when executing custom scripts such as this one.

Run the script and will be prompted to enter the UID that then will create the nfc file.