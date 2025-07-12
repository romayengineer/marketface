import time
import unittest

from marketface.router import TokenBucketRateLimiter


class TestRateLimiter(unittest.TestCase):

    def _calculate_tome_should_take(self, capacity: float, requests_count: int, tokens_per_request: float, tokens_per_second: float) -> float:
        seconds_per_token = (1 / tokens_per_second)
        total_tokens_used = requests_count * tokens_per_request
        return (
            (total_tokens_used - capacity) * seconds_per_token
        )

    def test_token_bucket_1(self):
        tokens_per_second = 1
        capacity = 1
        rate_limiter = TokenBucketRateLimiter(capacity=capacity, rate_limit=tokens_per_second)

        tokens_per_request = 1
        requests_count = 5
        time_should_take = self._calculate_tome_should_take(
            capacity, requests_count, tokens_per_request, tokens_per_second
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
        tokens_per_second = 0.5
        capacity = 1
        rate_limiter = TokenBucketRateLimiter(capacity=capacity, rate_limit=tokens_per_second)

        tokens_per_request = 1
        requests_count = 5
        time_should_take = self._calculate_tome_should_take(
            capacity, requests_count, tokens_per_request, tokens_per_second
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

    def test_token_bucket_3(self):
        # it can do 1 request every 0.5 seconds
        # because it takes 0.5 seconds to refill 1 token
        # or 1 second to refill 2 tokens (the same)
        tokens_per_second = 2
        capacity = 10
        rate_limiter = TokenBucketRateLimiter(capacity=capacity, rate_limit=tokens_per_second)

        tokens_per_request = 1
        requests_count = 20
        time_should_take = self._calculate_tome_should_take(
            capacity, requests_count, tokens_per_request, tokens_per_second
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