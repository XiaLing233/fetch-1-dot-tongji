"""通知接口：列表、详情、附件下载。"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required

from db import tjSql
from utils import crypto as myDecrypt
from utils.response import ok, ok_paginated
from services.cos import CosUpload

notices_bp = Blueprint('notices', __name__)

MYCOS = CosUpload()


@notices_bp.route('/api/notices', methods=['GET'])
def listNotices():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)

    items, total = tjSql.sqlFindNotices(page, page_size, search, status)
    return ok_paginated(items, page, page_size, total, '成功')


@notices_bp.route('/api/notices/<int:id>', methods=['GET'])
@jwt_required()
def getNotice(id):
    data = tjSql.sqlFindMyCommonMsgPublishById(id)
    if data is None:
        from utils.response import err
        return err(404, '通知不存在')
    return ok(data, '成功')


@notices_bp.route('/api/attachments/<path:filename>/download', methods=['GET'])
@jwt_required()
def downloadAttachment(filename):
    filePath = myDecrypt.decryptFilePath(filename)
    ATTACHMENT_PATH = current_app.config.get('ATTACHMENT_PATH', './1dot')
    return ok({
        "location": MYCOS.generate_temporary_url(f"{ATTACHMENT_PATH}/{filePath}")
    })
