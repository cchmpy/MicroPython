list(APPEND SDKCONFIG_DEFAULTS
    boards/sdkconfig.spiram_esp32
	boards/ESP32_GENERIC/sdkconfig.camera
)
list(APPEND MICROPY_DEF_BOARD
    MICROPY_HW_BOARD_NAME="Generic ESP32 module \(CAMERA and SPIRAM\)"
)
set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/manifest.py)