cmake_minimum_required(VERSION 3.13)
project(PWMAnalyzer)

set(CMAKE_CXX_STANDARD 17)

# Saleae SDK as submodule
set(CMAKE_PREFIX_PATH "${CMAKE_CURRENT_SOURCE_DIR}/analyzer-sdk")
find_package(AnalyzerSDK REQUIRED)

set(SOURCES
    src/PWMAnalyzer.cpp
    src/PWMAnalyzerSettings.cpp
    src/PWMAnalyzerResults.cpp
)

add_library(PWMAnalyzer SHARED ${SOURCES})

target_compile_definitions(PWMAnalyzer PRIVATE
    LOGIC2
)

target_include_directories(PWMAnalyzer PRIVATE
    src
)

target_link_libraries(PWMAnalyzer PRIVATE Saleae::AnalyzerSDK)

# Output .dll/.so/.dylib directly to build root — easy to find
set_target_properties(PWMAnalyzer PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)
