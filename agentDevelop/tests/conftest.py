import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pool_split import split_pool as split_fixed
from pool_split_original import split_pool as split_original

IMPLEMENTATIONS = {"original": split_original, "fixed": split_fixed}


def pytest_addoption(parser):
    parser.addoption(
        "--impl",
        action="store",
        default="fixed",
        choices=sorted(IMPLEMENTATIONS),
        help="选择被测实现：original = 题目附件原始版本，fixed = 修复版本",
    )


def pytest_report_header(config):
    impl = config.getoption("--impl")
    return f"被测实现: {impl}"


@pytest.fixture(scope="session")
def under_test(pytestconfig):
    """同一套测试，通过 --impl 切换被测实现。"""
    return IMPLEMENTATIONS[pytestconfig.getoption("--impl")]
