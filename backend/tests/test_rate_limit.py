"""限流逻辑测试：IP 封禁、邮件限制、滥用检测、Redis 锁。"""

import time
from utils.helpers import (
    check_ip_rate_limit, record_ip_attempt, clear_ip_attempts,
    check_daily_email_limit, record_email_sent, clear_unverified_email,
    check_abuse_pattern,
)
from utils.redis_client import get_redis


class TestIPRateLimit:
    def test_no_limit_initially(self, app):
        with app.test_request_context():
            blocked, remaining = check_ip_rate_limit('10.0.0.1', 'login')
            assert blocked is False
            assert remaining == 0

    def test_block_after_max_attempts(self, app):
        ip = '10.0.0.2'
        with app.test_request_context():
            for i in range(5):
                is_blocked, attempts = record_ip_attempt(ip, 'login', max_attempts=5, block_time=3600)
                if i < 4:
                    assert is_blocked is False
                    assert attempts == i + 1
                else:
                    assert is_blocked is True
                    assert attempts == 5

            # 第 6 次应被阻止
            blocked, remaining = check_ip_rate_limit(ip, 'login')
            assert blocked is True
            assert remaining > 0

    def test_clear_after_success(self, app):
        ip = '10.0.0.3'
        with app.test_request_context():
            record_ip_attempt(ip, 'register', max_attempts=3, block_time=3600)
            record_ip_attempt(ip, 'register', max_attempts=3, block_time=3600)
            clear_ip_attempts(ip, 'register')
            blocked, _ = check_ip_rate_limit(ip, 'register')
            assert blocked is False

    def test_different_actions_independent(self, app):
        ip = '10.0.0.4'
        with app.test_request_context():
            # 登录 fail 5 次被封
            for _ in range(5):
                record_ip_attempt(ip, 'login', max_attempts=5, block_time=3600)
            assert check_ip_rate_limit(ip, 'login')[0] is True

            # register 不受影响
            assert check_ip_rate_limit(ip, 'register')[0] is False

    def test_block_expires(self, app):
        ip = '10.0.0.5'
        with app.test_request_context():
            for _ in range(3):
                record_ip_attempt(ip, 'login', max_attempts=3, block_time=2)
            blocked, remaining = check_ip_rate_limit(ip, 'login')
            assert blocked is True  # 刚刚被封

            time.sleep(3)
            blocked, _ = check_ip_rate_limit(ip, 'login')
            assert blocked is False  # 过期解封


class TestDailyEmailLimit:
    def test_under_limit(self, app):
        with app.test_request_context():
            limited, count, max_daily = check_daily_email_limit('10.0.0.10')
            assert limited is False
            assert count < max_daily

    def test_limit_after_10(self, app):
        ip = '10.0.0.12'
        with app.test_request_context():
            for i in range(10):
                record_email_sent(ip, f'user{i}@tongji.edu.cn')
            limited, count, _ = check_daily_email_limit(ip)
            assert limited is True
            assert count >= 10


class TestAbusePattern:
    def test_not_suspicious_initially(self, app):
        with app.test_request_context():
            suspicious, count = check_abuse_pattern('10.0.0.20')
            assert suspicious is False

    def test_suspicious_after_5_unverified(self, app):
        ip = '10.0.0.21'
        with app.test_request_context():
            for i in range(5):
                record_email_sent(ip, f'user{i}@tongji.edu.cn')
            suspicious, count = check_abuse_pattern(ip)
            assert suspicious is True
            assert count >= 5

    def test_clear_after_verification(self, app):
        ip = '10.0.0.22'
        with app.test_request_context():
            for i in range(3):
                record_email_sent(ip, f'user{i}@tongji.edu.cn')
            clear_unverified_email(ip, 'user0@tongji.edu.cn')
            # 清除一个不影响其他
            _, count = check_abuse_pattern(ip)
            assert count == 2


class TestRedisLock:
    def test_lock_acquire_and_reject(self):
        """Redis 锁：第一次获取成功，第二次被拒绝。"""
        r = get_redis()
        email = 'lock_test@tongji.edu.cn'
        lock_key = f'email_lock:{email}'

        # 第一次获取成功
        acquired = r.set(lock_key, str(time.time()), nx=True, ex=10)
        assert acquired is True

        # 第二次被拒绝（Redis SET NX 返回 None 表示 key 已存在）
        acquired2 = r.set(lock_key, str(time.time()), nx=True, ex=10)
        assert not acquired2

        # 释放后可以重新获取
        r.delete(lock_key)
        acquired3 = r.set(lock_key, str(time.time()), nx=True, ex=10)
        assert acquired3 is True

    def test_lock_auto_expire(self):
        """锁自动过期后可以被重新获取。"""
        r = get_redis()
        lock_key = 'email_lock:expire@tongji.edu.cn'

        r.set(lock_key, str(time.time()), nx=True, ex=1)
        time.sleep(1.5)
        # 过期后可以重新获取
        acquired = r.set(lock_key, str(time.time()), nx=True, ex=10)
        assert acquired is True
