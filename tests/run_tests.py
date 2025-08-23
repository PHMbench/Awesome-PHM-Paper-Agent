#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
APPA测试运行器
Test Runner for APPA System

功能：
- 运行所有测试用例
- 生成测试报告
- 显示覆盖率信息
- 提供详细的测试结果

用法：
    python tests/run_tests.py
    python tests/run_tests.py --verbose
    python tests/run_tests.py --coverage
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

# 添加项目根目录到路径
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_tests(verbose=False, coverage=False, specific_test=None):
    """
    运行测试用例
    
    Args:
        verbose (bool): 是否显示详细输出
        coverage (bool): 是否生成覆盖率报告
        specific_test (str): 运行特定测试文件
    """
    print("🧪 APPA系统测试运行器")
    print("=" * 50)
    
    # 构建pytest命令
    cmd = ["python", "-m", "pytest"]
    
    if specific_test:
        cmd.append(str(TEST_DIR / specific_test))
    else:
        cmd.append(str(TEST_DIR))
    
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # 添加其他有用的选项
    cmd.extend([
        "--color=yes",
        "-x",  # 遇到第一个失败就停止
        "--tb=short"  # 简化回溯信息
    ])
    
    print(f"🚀 执行命令: {' '.join(cmd)}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("-" * 50)
        print(f"⏱️  测试耗时: {duration:.2f}秒")
        
        if result.returncode == 0:
            print("✅ 所有测试通过！")
        else:
            print("❌ 部分测试失败")
            
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ pytest未安装。请运行: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False


def install_dependencies():
    """安装测试依赖"""
    print("📦 安装测试依赖...")
    
    dependencies = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "pyyaml>=6.0"
    ]
    
    for dep in dependencies:
        print(f"  安装 {dep}...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"⚠️  安装 {dep} 失败，请手动安装")


def check_test_environment():
    """检查测试环境"""
    print("🔍 检查测试环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    
    # 检查项目结构
    required_dirs = [
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "configs",
        TEST_DIR
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            print(f"❌ 缺少目录: {dir_path}")
            return False
    
    # 检查关键文件
    key_files = [
        PROJECT_ROOT / "src" / "utils" / "paper_quality_filter.py",
        PROJECT_ROOT / "configs" / "quality_filters.yaml"
    ]
    
    for file_path in key_files:
        if not file_path.exists():
            print(f"⚠️  缺少文件: {file_path}")
    
    print("✅ 测试环境检查完成")
    return True


def show_test_info():
    """显示测试信息"""
    print("📊 测试套件信息")
    print("=" * 50)
    
    test_files = list(TEST_DIR.glob("test_*.py"))
    print(f"📁 测试文件数量: {len(test_files)}")
    
    for test_file in test_files:
        print(f"  📄 {test_file.name}")
        
        # 简单统计测试用例数量
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                test_count = content.count('def test_')
                class_count = content.count('class Test')
                print(f"     🧪 测试方法: {test_count}")
                print(f"     📚 测试类: {class_count}")
        except Exception:
            print("     ⚠️  无法读取文件信息")
    
    print("-" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="APPA系统测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="显示详细测试输出"
    )
    
    parser.add_argument(
        "-c", "--coverage",
        action="store_true", 
        help="生成代码覆盖率报告"
    )
    
    parser.add_argument(
        "-t", "--test",
        type=str,
        help="运行特定测试文件 (例如: test_paper_quality_filter.py)"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="安装测试依赖"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="显示测试套件信息"
    )
    
    args = parser.parse_args()
    
    if args.install_deps:
        install_dependencies()
        return
    
    if args.info:
        show_test_info()
        return
    
    # 检查测试环境
    if not check_test_environment():
        sys.exit(1)
    
    # 显示测试信息
    if args.verbose:
        show_test_info()
    
    # 运行测试
    success = run_tests(
        verbose=args.verbose,
        coverage=args.coverage,
        specific_test=args.test
    )
    
    if not success:
        sys.exit(1)
    
    # 如果生成了覆盖率报告，提示用户查看
    if args.coverage:
        coverage_html = PROJECT_ROOT / "htmlcov" / "index.html"
        if coverage_html.exists():
            print(f"📊 覆盖率报告生成: {coverage_html}")
            print("   使用浏览器打开查看详细覆盖率信息")


if __name__ == "__main__":
    main()