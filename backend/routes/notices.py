"""通知接口：列表、详情、附件下载。"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from db import tjSql
from utils import crypto as myDecrypt
from services.cos import CosUpload

notices_bp = Blueprint('notices', __name__)

MYCOS = CosUpload()


@notices_bp.route('/api/findMyCommonMsgPublish', methods=['GET'])
def findMyCommonMsgPublish():
    data = tjSql.sqlFindMyCommonMsgPublish()
    return jsonify({'code': 200, 'msg': '成功', 'data': data}), 200


@notices_bp.route('/api/findMyCommonMsgPublishById', methods=['POST'])
@jwt_required()
def findMyCommonMsgPublishById():
    id = request.json.get('id')
    data = tjSql.sqlFindMyCommonMsgPublishById(id)
    return jsonify({'code': 200, 'msg': '成功', 'data': data}), 200


@notices_bp.route('/api/downloadAttachmentByFileName', methods=['POST'])
@jwt_required()
def downloadAttachmentByFileName():
    fileLocation = request.json.get('fileLocation')
    print("文件位置：", fileLocation)

    filePath = myDecrypt.decryptFilePath(fileLocation)
    print("文件路径：", filePath)

    ATTACHMENT_PATH = current_app.config.get('ATTACHMENT_PATH', './1dot')
    return jsonify({
        "code": 200,
        "location": MYCOS.generate_temporary_url(f"{ATTACHMENT_PATH}/{filePath}")
    })
