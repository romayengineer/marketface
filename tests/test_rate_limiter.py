import time
import unittest

from marketface.router import TokenBucketRateLimiter


class TestRateLimiter(unittest.TestCase):

    def _calculate_tome_should_take(self, requests_count: int, tokens_per_request: float, requests_per_second: float) -> float:
        requests_per_second_inverse = (1 / requests_per_second)
        return (
            requests_count * tokens_per_request * requests_per_second_inverse - requests_per_second_inverse
        )

    def test_token_bucket_1(self):
        requests_per_second = 1
        rate_limiter = TokenBucketRateLimiter(capacity=1, rate_limit=requests_per_second)

        tokens_per_request = 1
        requests_count = 5
        time_should_take = self._calculate_tome_should_take(
            requests_count, tokens_per_request, requests_per_second
        )

        # this should take requests_count seconds or more NOT less
        start = time.perf_counter()
        for i in range(requests_count):
            rate_limiter.acquire(tokens_needed=tokens_per_request)
            print("doing my thing... ", i)
        end = time.perf_counter()
        time_elapsed = end - start
        print("time_should_take: ", time_should_take)
        print("time_elapsed: ", time_elapsed)
        # assert time_should_take <= time_elapsed
        self.assertLessEqual(time_should_take, time_elapsed)
        # assert the time it took to run is not higher than time expected + 0.8%
        self.assertLessEqual(time_elapsed, time_should_take * 1.008)

    def test_token_bucket_2(self):
        # it can do 1 request every 2 seconds
        # because it takes 2 seconds to refill 1 token
        requests_per_second = 0.5
        rate_limiter = TokenBucketRateLimiter(capacity=1, rate_limit=requests_per_second)

        tokens_per_request = 1
        requests_count = 5
        time_should_take = self._calculate_tome_should_take(
            requests_count, tokens_per_request, requests_per_second
        )

        # this should take requests_count seconds or more NOT less
        start = time.perf_counter()
        for i in range(requests_count):
            rate_limiter.acquire(tokens_needed=tokens_per_request)
            print("doing my thing... ", i)
        end = time.perf_counter()
        time_elapsed = end - start
        print("time_should_take: ", time_should_take)
        print("time_elapsed: ", time_elapsed)
        # assert time_should_take <= time_elapsed
        self.assertLessEqual(time_should_take, time_elapsed)
        # assert the time it took to run is not higher than time expected + 0.8%
        self.assertLessEqual(time_elapsed, time_should_take * 1.008)