from vitae.limits import RateLimiter


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_a_visitor_gets_four_questions_a_minute():
    clock = Clock()
    limiter = RateLimiter(clock=clock)

    assert [limiter.check("1.1.1.1") for _ in range(4)] == [None, None, None, None]
    clock.now += 15
    assert limiter.check("1.1.1.1") == 45.0
    assert limiter.check("2.2.2.2") is None
    clock.now += 45
    assert limiter.check("1.1.1.1") is None


def test_a_visitor_gets_thirty_questions_a_day():
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    for _ in range(30):
        assert limiter.check("1.1.1.1") is None
        clock.now += 60

    assert limiter.check("1.1.1.1") == 86400.0 - 30 * 60


def test_everyone_together_gets_three_hundred_a_day():
    clock = Clock()
    limiter = RateLimiter(clock=clock)
    for n in range(300):
        assert limiter.check(f"10.0.{n // 250}.{n % 250}") is None

    assert limiter.check("9.9.9.9") == 86400.0
    assert "9.9.9.9" not in limiter.visitors
