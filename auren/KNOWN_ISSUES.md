# AUREN 2.0 - Known Issues

## Minor Issues (Non-Blocking)

### 1. MediaPipe Protobuf Warnings
- **Issue**: MediaPipe may show protobuf version warnings
- **Impact**: None - functionality works correctly
- **Resolution**: Using protobuf 4.25.3 as compromise

### 2. Test Import Warnings
- **Issue**: Some tests may show import warnings
- **Impact**: Tests run successfully despite warnings
- **Resolution**: Set PYTHONPATH before running tests

### 3. CrewAI Memory Parameter
- **Issue**: Newer CrewAI versions don't support memory parameter
- **Impact**: None - using memory_config instead
- **Resolution**: Agent factory handles version compatibility

## Resolved Issues

### 1. Dependency Conflicts ✅
- All major conflicts resolved using version ranges

### 2. Type Annotations ✅
- Critical files have proper type annotations

### 3. Security Issues ✅
- All high and medium severity issues resolved

## Future Improvements

1. Upgrade to CrewAI 0.41.0+ when stable
2. Implement full type coverage (currently 60%)
3. Add comprehensive unit test suite
4. Implement performance benchmarking 