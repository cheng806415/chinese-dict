import unittest
import sys
import os

# Add project root to path for CI compatibility
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.utils.decorators import safe_operation, safe_void_operation, retry_on_error


class TestSafeOperation(unittest.TestCase):
    def test_success(self):
        @safe_operation(default='fallback')
        def success_func():
            return 'success'

        self.assertEqual(success_func(), 'success')

    def test_failure_with_default(self):
        @safe_operation(default='fallback')
        def fail_func():
            raise ValueError('test error')

        self.assertEqual(fail_func(), 'fallback')

    def test_failure_with_none_default(self):
        @safe_operation()
        def fail_func():
            raise ValueError('test error')

        self.assertIsNone(fail_func())

    def test_failure_with_list_default(self):
        @safe_operation(default=[])
        def fail_func():
            raise ValueError('test error')

        self.assertEqual(fail_func(), [])


class TestSafeVoidOperation(unittest.TestCase):
    def test_success(self):
        @safe_void_operation()
        def success_func():
            pass

        success_func()  # Should not raise

    def test_failure(self):
        @safe_void_operation()
        def fail_func():
            raise ValueError('test error')

        fail_func()  # Should not raise


class TestRetryOnError(unittest.TestCase):
    def test_success(self):
        call_count = [0]

        @retry_on_error(max_retries=3)
        def success_func():
            call_count[0] += 1
            return 'success'

        self.assertEqual(success_func(), 'success')
        self.assertEqual(call_count[0], 1)

    def test_retry_then_success(self):
        call_count = [0]

        @retry_on_error(max_retries=3, delay=0.01)
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError('temporary error')
            return 'success'

        self.assertEqual(flaky_func(), 'success')
        self.assertEqual(call_count[0], 3)

    def test_retry_exhausted(self):
        call_count = [0]

        @retry_on_error(max_retries=3, delay=0.01)
        def always_fail():
            call_count[0] += 1
            raise ValueError('persistent error')

        with self.assertRaises(ValueError):
            always_fail()
        self.assertEqual(call_count[0], 3)


if __name__ == '__main__':
    unittest.main()
