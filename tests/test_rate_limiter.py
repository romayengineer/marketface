import time
import unittest

from marketface.router import TokenBucketRateLimiter


class TestRateLimiter(unittest.TestCase):

    def test_token_bucket(self):
        requests_per_second = 1
        rate_limiter = TokenBucketRateLimiter(capacity=requests_per_second)

        tokens_per_request = 1
        requests_count = 10
        time_should_take = requests_count * tokens_per_request

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