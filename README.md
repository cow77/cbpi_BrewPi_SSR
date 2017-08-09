# cbpi_BrewPi_SSR
BrewPi SSR Controller Plugin for CraftBeerPi

This is the code for a BrewPi plugin for the CraftBeerPi brewing/fermentation controller to make it possible to use BrewPi SSR's.
This are 1-wire based SSR-controllers. Normally connected using the "w1-" file based 1-wire software of the pi, but also by connecting using a i2c-hub (The 1 Wire Pi Plus from AB Electronics UK). This creates a more reliable 1-wire infrastructure incase a larger network is needed. It then use owfs and pyowfs.

# BrewPi Onewire SSR Expansion is fully working.

SSR:

![brewpi_onewire_ssr_expansion_board](https://store.brewpi.com/media/catalog/product/cache/1/image/9df78eab33525d08d6e5fb8d27136e95/b/r/brewpi_onewire_ssr_expansion_board_1.jpg)

BrewPiSSR switch a SSR: consist of a ds2413 as 1-wire 2 pio device, driving a SSR


    BrewPiSSR is the type to select as actor for SSR via BrewPi, the 1-wire id 3a-.... as device, port A or B as target.


# cbpi_BrewPi_SSR
