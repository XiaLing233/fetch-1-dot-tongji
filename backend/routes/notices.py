"""通知接口：列表、详情、附件下载。"""

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required

from db import tjSql
from utils import crypto as myDecrypt
from utils.response import ok, ok_paginated
from services.cos import CosUpload

notices_bp = Blueprint('notices', __name__)

MYCOS = CosUpload()


@notices_bp.route('/api/findMyCommonMsgPublish', methods=['GET'])
def findMyCommonMsgPublish():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)

    items, total = tjSql.sqlFindNotices(page, page_size, search, status)
    return ok_paginated(items, page, page_size, total, '成功')


@notices_bp.route('/api/findMyCommonMsgPublishById', methods=['POST'])
@jwt_required()
def findMyCommonMsgPublishById():
    id = request.json.get('id')
    data = tjSql.sqlFindMyCommonMsgPublishById(id)
    return ok(data, '成功')


@notices_bp.route('/api/downloadAttachmentByFileName', methods=['POST'])
@jwt_required()
def downloadAttachmentByFileName():
    fileLocation = request.json.get('fileLocation')
    print("文件位置：", fileLocation)

    filePath = myDecrypt.decryptFilePath(fileLocation)
    print("文件路径：", filePath)

    ATTACHMENT_PATH = current_app.config.get('ATTACHMENT_PATH', './1dot')
    return ok({
        "location": MYCOS.generate_temporary_url(f"{ATTACHMENT_PATH}/{filePath}")
    })
