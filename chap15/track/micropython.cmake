# 模块命名（遵循MicroPython规范）
set(MODULE_NAME usermod_mp_track)

# 为C模块创建一个INTERFACE库（每个外部c模块都必须如此）
add_library(${MODULE_NAME} INTERFACE)

# 源文件添加到lib  ${CMAKE_CURRENT_LIST_DIR}
target_sources(${MODULE_NAME} INTERFACE 
	${CMAKE_CURRENT_LIST_DIR}/py_track.c
)

# 添加当前目录作为include目录
target_include_directories(${MODULE_NAME} INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

# 将INTERFACE库与usermod目标相关联
target_link_libraries(usermod INTERFACE ${MODULE_NAME})

