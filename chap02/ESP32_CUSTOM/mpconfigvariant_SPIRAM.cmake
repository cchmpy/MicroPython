set(SDKCONFIG_DEFAULTS
    ${SDKCONFIG_DEFAULTS}
    boards/sdkconfig.spiram
)

list(APPEND MICROPY_DEF_BOARD
    MICROPY_HW_BOARD_NAME="Custom ESP32 module with SPIRAM"
)
