"""数据库层测试。"""

import uuid
import datetime

import pytest

from db import tjSql
from db.tjSql import DB


def _uid():
    return uuid.uuid4().hex[:8]


# ----- 分页测试辅助 -----

# 使用大 ID 避免与正式数据冲突
_TEST_ID_BASE = 9999900
_test_id_counter = 0


def _next_test_id():
    global _test_id_counter
    _test_id_counter += 1
    return _TEST_ID_BASE + _test_id_counter


def _now():
    return datetime.datetime.now()


def _future():
    return (_now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")


def _past():
    return '1970-01-01 00:00:00'


def _insert_notice(db, nid, title, invalid_top_time, publish_time,
                   end_time=None, start_time=None, create_id='test_creator_id',
                   create_user='test_creator', create_time=None):
    """插入一条测试通知。invalid_top_time 支持 None（NULL）、_future()、_past()。"""
    if end_time is None:
        end_time = '2099-12-31 23:59:59'
    if start_time is None:
        start_time = '2025-01-01 00:00:00'
    if create_time is None:
        create_time = '2025-01-01 00:00:00'
    sql = (
        "INSERT INTO notifications (id, title, content, start_time, end_time,"
        " invalid_top_time, create_id, create_user, create_time, publish_time)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    db.cursor.execute(sql, (
        nid, title, 'test content',
        start_time, end_time,
        invalid_top_time,
        create_id, create_user,
        create_time, publish_time
    ))


def _cleanup_notices(db, ids):
    """删除测试通知。"""
    for nid in ids:
        db.cursor.execute("DELETE FROM notifications WHERE id = %s", (nid,))


class TestNotifications:
    def test_not_exists(self):
        assert tjSql.sqlHaveRecorded(99999999) is False

    def test_find_notices_search_no_match(self):
        items, _ = tjSql.sqlFindNotices(page=1, page_size=20, search='不存在的内容')
        assert len(items) == 0

    def test_find_notices_returns_paginated(self):
        items, total = tjSql.sqlFindNotices(page=1, page_size=20)
        assert isinstance(items, list)
        assert isinstance(total, int)


class TestUsers:
    def test_user_crud(self):
        email = f'crud{_uid()}@tongji.edu.cn'
        assert tjSql.sqlUserExist(email) is False
        tjSql.sqlInsertUser(f'crud{_uid()}', email, 'hashed_pw', '2025-01-01 00:00:00')
        assert tjSql.sqlUserExist(email) is True
        info = tjSql.sqlGetUserInfo(email)
        assert info[0].startswith('crud')
        assert info[1] == email
        assert info[3] == 0

    def test_get_password(self):
        email = f'pwd{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'pwd{_uid()}', email, 'secure_hash_123', '2025-01-01 00:00:00')
        assert tjSql.sqlGetPassword(email) == 'secure_hash_123'

    def test_update_password(self):
        email = f'upd{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'upd{_uid()}', email, 'old_hash', '2025-01-01 00:00:00')
        tjSql.sqlUpdatePassword(email, 'new_hash')
        assert tjSql.sqlGetPassword(email) == 'new_hash'

    def test_toggle_receive_noti(self):
        email = f'tog{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'tog{_uid()}', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqltoggleReceiveNoti(email, 1)
        info = tjSql.sqlGetUserInfo(email)
        assert info[3] == 1

    def test_get_all_receive_noti_users(self):
        email = f'rcv{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'rcv{_uid()}', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqltoggleReceiveNoti(email, 1)
        users = tjSql.sqlGetAllReceiveNotiUser()
        assert any(u['email'] == email for u in users)

    def test_login_log(self):
        email = f'log{_uid()}@tongji.edu.cn'
        tjSql.sqlInsertUser(f'log{_uid()}', email, 'hash', '2025-01-01 00:00:00')
        tjSql.sqlUpdateLoginLog(email, '192.168.1.1', '2025-01-02 00:00:00')
        logs = tjSql.sqlGetLoginLog(email)
        assert logs is not None
        assert any(log['ip_address'] == '192.168.1.1' for log in logs)


class TestNoticesPagination:
    """置顶排序与分页集成测试。

    验证修复：置顶项通过 ORDER BY 统一排序，不再单独拼装，
    确保每页返回条数严格等于 page_size。
    """

    def test_pinned_come_first(self):
        """置顶通知应排在非置顶前面，同组内按 publish_time DESC 排序。"""
        ids = []
        with DB() as db:
            ids.append(_next_test_id())
            ids.append(_next_test_id())
            ids.append(_next_test_id())
            # 非置顶(最新) → 置顶 → 非置顶(最旧)
            _insert_notice(db, ids[0], 'test_pagi_normal1', _past(), '2025-06-01 10:00:00')
            _insert_notice(db, ids[1], 'test_pagi_pinned1', _future(), '2025-06-01 09:00:00')
            _insert_notice(db, ids[2], 'test_pagi_normal2', _past(), '2025-06-01 08:00:00')

        try:
            items, _ = tjSql.sqlFindNotices(page=1, page_size=20)
            test_items = [item for item in items if item['id'] in ids]

            assert len(test_items) == 3, f"应查到 3 条测试数据，实际 {len(test_items)}"
            # 置顶排第一
            assert test_items[0]['id'] == ids[1], (
                f"第一条应为置顶通知 (id={ids[1]})，实际 id={test_items[0]['id']}"
            )
            assert test_items[0]['status'] == '置顶'
            # 非置顶按 publish_time DESC
            assert test_items[1]['id'] == ids[0], "非置顶中 publish_time 更新的应排前面"
            assert test_items[2]['id'] == ids[2], "非置顶中 publish_time 更旧的应排后面"
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_page_size_respected(self):
        """每页返回的测试数据条数应等于 page_size（除最后一页外）。"""
        ids = []
        with DB() as db:
            for i in range(5):
                ids.append(_next_test_id())
                _insert_notice(db, ids[-1], f'test_pagi_pin_{i}', _future(),
                               f'2025-06-{(i+1):02d} 10:00:00')
            for i in range(10):
                ids.append(_next_test_id())
                _insert_notice(db, ids[-1], f'test_pagi_norm_{i}', _past(),
                               f'2025-05-{(i+1):02d} 10:00:00')

        try:
            page1, total = tjSql.sqlFindNotices(page=1, page_size=7)
            page2, _ = tjSql.sqlFindNotices(page=2, page_size=7)
            page3, _ = tjSql.sqlFindNotices(page=3, page_size=7)

            p1_test = [i for i in page1 if i['id'] in ids]
            p2_test = [i for i in page2 if i['id'] in ids]
            p3_test = [i for i in page3 if i['id'] in ids]

            assert len(p1_test) == 7, f"第 1 页应有 7 条，实际 {len(p1_test)}"
            assert len(p2_test) == 7, f"第 2 页应有 7 条，实际 {len(p2_test)}"
            assert len(p3_test) == 1, f"第 3 页应有 1 条（15 % 7 = 1），实际 {len(p3_test)}"

            # 验证无重叠
            p1_id_set = {i['id'] for i in p1_test}
            p2_id_set = {i['id'] for i in p2_test}
            p3_id_set = {i['id'] for i in p3_test}
            assert p1_id_set.isdisjoint(p2_id_set), "第 1 页和第 2 页不应有重叠数据"
            assert p1_id_set.isdisjoint(p3_id_set), "第 1 页和第 3 页不应有重叠数据"
            assert p2_id_set.isdisjoint(p3_id_set), "第 2 页和第 3 页不应有重叠数据"
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_more_pinned_than_page_size(self):
        """置顶数超过 page_size 时，首页仍严格返回 page_size 条，后续页补全剩余置顶。"""
        ids = []
        with DB() as db:
            for i in range(8):
                ids.append(_next_test_id())
                _insert_notice(db, ids[-1], f'test_pagi_many_pin_{i}', _future(),
                               f'2025-06-{(i+1):02d} 10:00:00')
            for i in range(2):
                ids.append(_next_test_id())
                _insert_notice(db, ids[-1], f'test_pagi_many_norm_{i}', _past(),
                               f'2025-05-{(i+1):02d} 10:00:00')

        try:
            page1, total = tjSql.sqlFindNotices(page=1, page_size=5)
            page2, _ = tjSql.sqlFindNotices(page=2, page_size=5)

            p1_test = [i for i in page1 if i['id'] in ids]
            p2_test = [i for i in page2 if i['id'] in ids]

            # 关键断言：之前 bug 会导致 page1 返回 8+5=13 条
            assert len(p1_test) == 5, (
                f"置顶 8 条 + page_size=5：首页应严格返回 5 条，实际 {len(p1_test)}"
                f"（修复前 bug 会返回 13 条）"
            )
            assert len(p2_test) == 5, f"第 2 页应有 5 条，实际 {len(p2_test)}"

            # 第 1 页全为置顶
            assert all(item['status'] == '置顶' for item in p1_test), "第 1 页应全为置顶"

            # 第 2 页：前 3 条置顶 + 后 2 条非置顶
            pin_p2 = [item for item in p2_test if item['status'] == '置顶']
            norm_p2 = [item for item in p2_test if item['status'] != '置顶']
            assert len(pin_p2) == 3, f"第 2 页应有 3 条置顶，实际 {len(pin_p2)}"
            assert len(norm_p2) == 2, f"第 2 页应有 2 条非置顶，实际 {len(norm_p2)}"
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_different_page_sizes(self):
        """不同 page_size（3/5/10/20）下每页条数正确，且置顶始终优先。"""
        ids = []
        with DB() as db:
            for i in range(6):
                ids.append(_next_test_id())
                _insert_notice(db, ids[-1], f'test_pagi_size_pin_{i}', _future(),
                               f'2025-06-{(i+1):02d} 10:00:00')
            for i in range(8):
                ids.append(_next_test_id())
                _insert_notice(db, ids[-1], f'test_pagi_size_norm_{i}', _past(),
                               f'2025-05-{(i+1):02d} 10:00:00')

        try:
            for ps in [3, 5, 10, 20]:
                page1, _ = tjSql.sqlFindNotices(page=1, page_size=ps)
                p1_test = [i for i in page1 if i['id'] in ids]

                expected = min(ps, len(ids))
                assert len(p1_test) == expected, (
                    f"page_size={ps}：首页应有 {expected} 条测试数据，实际 {len(p1_test)}"
                )

                # 验证置顶始终在非置顶之前
                seen_normal = False
                for item in p1_test:
                    if item['status'] != '置顶':
                        seen_normal = True
                    elif seen_normal:
                        pytest.fail(f"page_size={ps}：置顶项不应出现在非置顶项之后")
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_null_invalid_top_time_sorts_correctly(self):
        """两层排序：置顶层先（按 publish_time DESC），非置顶层后（按 publish_time DESC）。

        非置顶层包含三种 invalid_top_time：NULL、1970-01-01（默认）、已过期。
        修复前 NULL 因 MySQL 排序异常被排到非置顶层末尾。
        """
        ids = []
        with DB() as db:
            # ===== 置顶层（未来 invalid_top_time）=====
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'real_pinned_1', _future(),
                           '2026-07-06 09:09:43')
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'real_pinned_2', _future(),
                           '2026-06-25 09:31:18')

            # ===== 非置顶层 =====
            # NULL（从未置顶，publish 最新）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'real_null_top_1', None,
                           '2026-07-14 13:51:48')
            # 默认 1970-01-01（从未置顶，publish 介于两个 NULL 之间）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'real_normal_1', _past(),
                           '2026-07-13 20:00:00')
            # NULL（publish 稍旧）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'real_null_top_2', None,
                           '2026-07-13 19:25:41')
            # 过期置顶（过去 invalid_top_time，归入非置顶层，publish 最旧）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'real_expired_pin_1', '2026-07-01 00:00:00',
                           '2026-06-10 08:33:20')

        try:
            items, _ = tjSql.sqlFindNotices(page=1, page_size=20)
            test_items = [item for item in items if item['id'] in ids]
            assert len(test_items) == 6, f"应查到 6 条测试数据，实际 {len(test_items)}"

            # 完整顺序：
            # #1 置顶 (pub=07-06)
            # #2 置顶 (pub=06-25)
            # #3 NULL (pub=07-14)      ← 非置顶中 publish 最新
            # #4 默认 (pub=07-13 20:00) ← 介于两个 NULL 之间
            # #5 NULL (pub=07-13 19:25)
            # #6 过期置顶 (pub=06-10)   ← 非置顶中 publish 最旧
            order = [
                (item['status'] == '置顶',
                 item['invalid_top_time'],
                 item['publish_time'])
                for item in test_items
            ]

            assert order[0] == (True,  _future(), '2026-07-06 09:09:43'), f"#1 {order[0]}"
            assert order[1] == (True,  _future(), '2026-06-25 09:31:18'), f"#2 {order[1]}"
            assert order[2] == (False, None,      '2026-07-14 13:51:48'), f"#3 {order[2]}"
            assert order[3] == (False, _past(),   '2026-07-13 20:00:00'), f"#4 {order[3]}"
            assert order[4] == (False, None,      '2026-07-13 19:25:41'), f"#5 {order[4]}"
            assert order[5] == (False, '2026-07-01 00:00:00',
                                '2026-06-10 08:33:20'), f"#6 {order[5]}"
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_posting_filter_includes_pinned(self):
        """筛选 '发布中' 时应包含置顶项（其 end_time 也在未来），置顶排最前。"""
        ids = []
        with DB() as db:
            # 置顶 + 发布中（end_time 在未来）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'pin_post', _future(),
                           '2026-07-06 09:00:00', end_time='2026-12-31 00:00:00')
            # 普通发布中（非置顶）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'norm_post', _past(),
                           '2026-07-10 10:00:00', end_time='2026-12-31 00:00:00')
            # 已过期（不应出现在发布中筛选结果里）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'expired', _past(),
                           '2026-06-01 08:00:00', end_time='2026-01-01 00:00:00')

        try:
            items, total = tjSql.sqlFindNotices(page=1, page_size=20, statuses=['发布中'])
            test_items = [item for item in items if item['id'] in ids]

            # 应返回 2 条：置顶+发布中 和 普通发布中，不包含已过期
            assert len(test_items) == 2, (
                f"筛选'发布中'应返回 2 条测试数据，实际 {len(test_items)}"
                f"（修复前会排除置顶项只返回 1 条）"
            )
            # 置顶排第一
            assert test_items[0]['status'] == '置顶', f"置顶+发布中应排第一，实际 {test_items[0]['status']}"
            # 第二是普通发布中
            assert test_items[1]['status'] == '发布中', f"普通发布中应排第二，实际 {test_items[1]['status']}"
            # 确保 total 正确
            assert total >= 2
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_multi_status_filter(self):
        """多选状态（置顶 + 发布中）用 OR 拼接"""
        ids = []
        with DB() as db:
            # 置顶
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'pin_only', _future(),
                           '2026-07-06 09:00:00', end_time='2026-12-31 00:00:00')
            # 发布中（非置顶）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'post_only', _past(),
                           '2026-07-10 10:00:00', end_time='2026-12-31 00:00:00')
            # 已过期（不应出现）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'exp_only', _past(),
                           '2026-06-01 08:00:00', end_time='2026-01-01 00:00:00')

        try:
            # 多选：置顶 + 发布中
            items, _ = tjSql.sqlFindNotices(page=1, page_size=20,
                                            statuses=['置顶', '发布中'])
            test_items = [item for item in items if item['id'] in ids]
            assert len(test_items) == 2, f"多选(置顶+发布中)应返回 2 条，实际 {len(test_items)}"
            assert test_items[0]['status'] == '置顶'
            assert test_items[1]['status'] == '发布中'

            # 空列表 = 无筛选
            items3, _ = tjSql.sqlFindNotices(page=1, page_size=20, statuses=[])
            test_items3 = [item for item in items3 if item['id'] in ids]
            assert len(test_items3) == 3, f"空列表应返回 3 条，实际 {len(test_items3)}"
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_pinned_and_outdated_filter(self):
        """多选 置顶 + 已过期：应返回置顶项和已过期项，不含发布中。"""
        ids = []
        with DB() as db:
            # 置顶
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'pin_out_1', _future(),
                           '2026-07-06 09:00:00', end_time='2026-12-31 00:00:00')
            # 发布中（不应出现）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'post_out_1', _past(),
                           '2026-07-10 10:00:00', end_time='2026-12-31 00:00:00')
            # 已过期
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'exp_out_1', _past(),
                           '2026-06-01 08:00:00', end_time='2026-01-01 00:00:00')

        try:
            items, _ = tjSql.sqlFindNotices(page=1, page_size=20,
                                            statuses=['置顶', '已过期'])
            test_items = [item for item in items if item['id'] in ids]
            assert len(test_items) == 2, f"多选(置顶+已过期)应返回 2 条，实际 {len(test_items)}"
            assert test_items[0]['status'] == '置顶', f"置顶应排第一，实际 {test_items[0]['status']}"
            assert test_items[1]['status'] == '已过期', f"已过期应排第二，实际 {test_items[1]['status']}"
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_outdated_and_posting_filter(self):
        """多选 已过期 + 发布中：置顶项总是发布中（end_time 在未来），
        因此也会匹配发布中条件，最终返回全部三种 status。"""
        ids = []
        with DB() as db:
            # 已过期
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'exp_post_1', _past(),
                           '2026-06-01 08:00:00', end_time='2026-01-01 00:00:00')
            # 发布中（非置顶）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'post_exp_1', _past(),
                           '2026-07-10 10:00:00', end_time='2026-12-31 00:00:00')
            # 置顶（总是发布中，匹配发布中条件）
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'pin_exp_1', _future(),
                           '2026-07-06 09:00:00', end_time='2026-12-31 00:00:00')

        try:
            items, _ = tjSql.sqlFindNotices(page=1, page_size=20,
                                            statuses=['已过期', '发布中'])
            test_items = [item for item in items if item['id'] in ids]
            # 已过期 1 条 + 发布中(含置顶) 2 条 = 3 条
            assert len(test_items) == 3, f"多选(已过期+发布中)应返回 3 条，实际 {len(test_items)}"
            # 置顶排第一
            assert test_items[0]['status'] == '置顶'
            assert {item['status'] for item in test_items[1:]} == {'已过期', '发布中'}
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)

    def test_all_three_statuses_equals_no_filter(self):
        """全选三个状态 = 与空列表等效，返回所有项。"""
        ids = []
        with DB() as db:
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'all_pin', _future(),
                           '2026-07-06 09:00:00', end_time='2026-12-31 00:00:00')
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'all_post', _past(),
                           '2026-07-10 10:00:00', end_time='2026-12-31 00:00:00')
            ids.append(_next_test_id())
            _insert_notice(db, ids[-1], 'all_exp', _past(),
                           '2026-06-01 08:00:00', end_time='2026-01-01 00:00:00')

        try:
            items_all, _ = tjSql.sqlFindNotices(page=1, page_size=20,
                                                statuses=['置顶', '发布中', '已过期'])
            items_none, _ = tjSql.sqlFindNotices(page=1, page_size=20, statuses=[])

            test_all = [item for item in items_all if item['id'] in ids]
            test_none = [item for item in items_none if item['id'] in ids]

            assert len(test_all) == 3, f"全选三状态应返回 3 条，实际 {len(test_all)}"
            assert len(test_none) == 3, f"无筛选应返回 3 条，实际 {len(test_none)}"
            # 两者顺序一致
            assert [item['id'] for item in test_all] == [item['id'] for item in test_none]
        finally:
            with DB() as db:
                _cleanup_notices(db, ids)
