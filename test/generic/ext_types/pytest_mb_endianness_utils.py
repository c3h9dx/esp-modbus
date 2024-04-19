# SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: CC0-1.0

import pytest
from pytest_embedded import Dut


@pytest.mark.esp32
@pytest.mark.generic
def test_mb_endianness_utils(dut: Dut) -> None:
    dut.run_all_single_board_cases()
