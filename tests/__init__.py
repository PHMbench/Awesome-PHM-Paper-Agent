# -*- coding: utf-8 -*-
"""
APPA Test Suite
===============

测试套件用于验证APPA系统的各项功能，包括：
- 论文质量过滤功能 (test_paper_quality_filter.py)
- Agent功能集成测试
- 配置加载和应用
- 性能和鲁棒性测试

运行测试：
    python -m pytest tests/
    python -m pytest tests/test_paper_quality_filter.py -v
    python tests/run_tests.py
"""

import os
import sys

# 确保测试可以导入项目模块
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

__version__ = "1.0.0"
__author__ = "APPA Development Team"
