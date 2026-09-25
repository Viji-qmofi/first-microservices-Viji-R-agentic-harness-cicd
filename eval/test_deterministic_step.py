"""Unit tests for scripts/parse_test_result_deterministic.py.

Inputs are drawn from real Maven output this project has actually
produced (DEV-02, HO-06 transcripts), plus the noisy-output edge case
the ADR names explicitly: Eureka stack traces and retry-logic WARN lines
that must not be mistaken for a real failure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from parse_test_result_deterministic import parse

# Real output shape from DEV-02 (constructor-injection task): 36 tests, clean pass.
DEV02_OUTPUT = """
[INFO] -------------------------------------------------------
[INFO]  T E S T S
[INFO] -------------------------------------------------------
[INFO] Running com.productorder.service.OrderServiceImplTest
[INFO] Tests run: 36, Failures: 0, Errors: 0, Skipped: 0
[INFO]
[INFO] Results:
[INFO]
[INFO] Tests run: 36, Failures: 0, Errors: 0, Skipped: 0
[INFO]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
"""

# Real output shape from HO-06: 38 tests, clean pass, different count than DEV-02.
HO06_OUTPUT = """
[INFO] Running com.productorder.controllers.OrderControllerTest
[INFO] Tests run: 6, Failures: 0, Errors: 0, Skipped: 0
[INFO] Running com.productorder.service.OrderServiceImplTest
[INFO] Tests run: 32, Failures: 0, Errors: 0, Skipped: 0
[INFO]
[INFO] Results:
[INFO]
[INFO] Tests run: 38, Failures: 0, Errors: 0, Skipped: 0
[INFO]
[INFO] BUILD SUCCESS
"""

# Realistic invented failure case -- not drawn from a real transcript, since
# every real run this project has produced happened to pass.
REAL_FAILURE_OUTPUT = """
[INFO] Running com.productorder.service.OrderServiceImplTest
[ERROR] Tests run: 10, Failures: 2, Errors: 0, Skipped: 0
[INFO]
[INFO] Results:
[INFO]
[INFO] Tests run: 10, Failures: 2, Errors: 0, Skipped: 0
[INFO]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
"""

# The named edge case: real-shaped noise (a retry-logic WARN and a Eureka
# connection-refused stack trace, both containing the literal word "ERROR")
# from tests that deliberately exercise failure paths -- the summary line
# still reports a clean pass, and the script must trust the summary line,
# not the presence of "ERROR"/"WARN" text elsewhere in the output.
NOISY_BUT_PASSING_OUTPUT = """
[INFO] Running com.productorder.service.OrderServiceImplTest
14:32:10.221 WARN  --- [main] c.p.service.OrderServiceImpl : Retryable exception on attempt 1, retrying...
14:32:10.512 ERROR 1 --- [main] c.n.d.s.t.d.RetryableEurekaHttpClient : Request execution failed with message: Connection refused
	at com.netflix.discovery.shared.transport.decorator.RetryableEurekaHttpClient.execute(RetryableEurekaHttpClient.java:118)
	at com.netflix.discovery.DiscoveryClient.<init>(DiscoveryClient.java:335)
[INFO] Tests run: 32, Failures: 0, Errors: 0, Skipped: 0
[INFO]
[INFO] Results:
[INFO]
[INFO] Tests run: 32, Failures: 0, Errors: 0, Skipped: 0
[INFO]
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
"""

# Structural edge case: a compilation failure before any test could run at
# all -- no Surefire summary line exists anywhere in the output.
NO_SUMMARY_LINE_OUTPUT = """
[INFO] -------------------------------------------------------
[ERROR] COMPILATION ERROR :
[ERROR] /workspace/ecom-order-service/src/main/java/com/productorder/service/OrderServiceImpl.java:[42,5] cannot find symbol
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
"""


def test_normal_pass_dev02():
    """Real DEV-02-shaped output: 36 tests, clean pass, must be valid."""
    result = parse(DEV02_OUTPUT)
    assert result["valid"] is True
    assert result["tests_run"] == 36
    assert result["failures"] == 0
    assert result["errors"] == 0
    assert result["problems"] == []


def test_normal_pass_ho06_multi_class():
    """Real HO-06-shaped output: multiple per-class lines, one aggregate
    line -- the LAST summary line (38) must be reported, not an earlier
    per-class line (6 or 32)."""
    result = parse(HO06_OUTPUT)
    assert result["valid"] is True
    assert result["tests_run"] == 38
    assert result["failures"] == 0


def test_real_failure_case():
    """A genuine failure: 2 of 10 tests failed, must be reported invalid
    with the real failure count, not silently passed."""
    result = parse(REAL_FAILURE_OUTPUT)
    assert result["valid"] is False
    assert result["tests_run"] == 10
    assert result["failures"] == 2
    assert "2 test failure(s)" in result["problems"]


def test_noisy_output_still_passes():
    """Named edge case from the ADR: WARN/ERROR text from tests that
    deliberately exercise failure paths (a retry WARN, a Eureka stack
    trace containing the literal word ERROR) must not be mistaken for a
    real failure. Only the real summary line's own counts matter."""
    result = parse(NOISY_BUT_PASSING_OUTPUT)
    assert result["valid"] is True
    assert result["tests_run"] == 32
    assert result["failures"] == 0
    assert result["errors"] == 0


def test_no_summary_line_found():
    """A compilation failure before any test ran at all: no Surefire
    summary line exists anywhere in the output. Must be explicitly
    invalid, never silently treated as passing by default."""
    result = parse(NO_SUMMARY_LINE_OUTPUT)
    assert result["valid"] is False
    assert result["tests_run"] == 0
    assert "no test summary line found in output" in result["problems"][0]
