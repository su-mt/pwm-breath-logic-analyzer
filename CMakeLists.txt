cmake_minimum_required(VERSION 3.13)
project(PWMAnalyzer)

set(CMAKE_CXX_STANDARD 17)

# Saleae SDK as submodule
add_subdirectory(analyzer-sdk)

set(SOURCES
    src/PWMAnalyzer.cpp
    src/PWMAnalyzerSettings.cpp
    src/PWMAnalyzerResults.cpp
)

add_library(PWMAnalyzer SHARED ${SOURCES})

target_include_directories(PWMAnalyzer PRIVATE
    src
    analyzer-sdk/include
)

target_link_libraries(PWMAnalyzer PRIVATE Analyzer)

# Output .dll/.so/.dylib directly to build root — easy to find
set_target_properties(PWMAnalyzer PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}"
)
