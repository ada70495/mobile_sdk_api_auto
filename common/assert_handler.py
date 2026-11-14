"""软断言：一条用例里的多个断言全部执行完，最后统一抛出失败"""


class AssertHandler:
    def __init__(self):
        self.failures = []

    def eq(self, actual, expected, msg: str = ""):
        if actual == expected:
            print(f"    [PASS] {msg}: {actual}")
        else:
            self.failures.append(f"{msg}: 期望={expected} 实际={actual}")
            print(f"    [FAIL] {msg}: 期望={expected} 实际={actual}")

    def not_none(self, actual, msg: str = ""):
        if actual is not None:
            print(f"    [PASS] {msg}: {actual}")
        else:
            self.failures.append(f"{msg}: 值为 None")
            print(f"    [FAIL] {msg}: 值为 None")

    def contains(self, container, item, msg: str = ""):
        if item in container:
            print(f"    [PASS] {msg}: 包含 '{item}'")
        else:
            self.failures.append(f"{msg}: '{item}' 不在 {container}")
            print(f"    [FAIL] {msg}: '{item}' 不在 {container}")

    def gt(self, actual, expected, msg: str = ""):
        if actual > expected:
            print(f"    [PASS] {msg}: {actual} > {expected}")
        else:
            self.failures.append(f"{msg}: {actual} 不大于 {expected}")
            print(f"    [FAIL] {msg}: {actual} 不大于 {expected}")

    def finish(self):
        if self.failures:
            raise AssertionError("断言失败汇总:\n" + "\n".join(self.failures))
