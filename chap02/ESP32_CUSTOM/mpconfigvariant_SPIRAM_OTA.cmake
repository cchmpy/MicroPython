set(SDKCONFIG_DEFAULTS
    ${SDKCONFIG_DEFAULTS}
    boards/sdkconfig.spiram
    boards/ESP32_CUSTOM/sdkconfig.ota
)

list(APPEND MICROPY_DEF_BOARD
    MICROPY_HW_BOARD_NAME="Custom ESP32 module \(SPIRAM and OTA\)"
)
