"""爬虫测试 fixtures。"""

import pytest


@pytest.fixture()
def sample_notification():
    counter = getattr(sample_notification, '_counter', 0) + 1
    sample_notification._counter = counter
    return {
        'id': 90000 + counter,
        'title': f'测试通知标题-{counter}',
        'content': '<p>测试内容</p>',
        'startTime': '2025-01-01 00:00:00',
        'endTime': '2099-01-01 00:00:00',
        'invalidTopTime': None,
        'createId': 'test001',
        'createUser': '测试用户',
        'createTime': '2025-01-01 00:00:00',
        'publishTime': '2025-01-01 00:00:00',
    }
