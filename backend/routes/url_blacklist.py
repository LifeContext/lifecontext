"""
URL 黑名单管理路由
仅供前端配置界面使用，与其他后端业务解耦
"""

from flask import Blueprint, jsonify, request
from utils.db import (
    get_url_blacklist,
    add_url_to_blacklist,
    delete_url_from_blacklist,
)
from utils.helpers import get_logger

logger = get_logger(__name__)

url_blacklist_bp = Blueprint("url_blacklist", __name__, url_prefix="/api/url-blacklist")


@url_blacklist_bp.route("", methods=["GET"])
def list_blacklist():
    """获取 URL 黑名单列表"""
    try:
        limit = request.args.get("limit", default=1000, type=int)
        offset = request.args.get("offset", default=0, type=int)
        
        if limit <= 0 or offset < 0:
            return jsonify({"error": "limit 必须大于 0，offset 不能为负数"}), 400
        
        entries = get_url_blacklist(limit=limit, offset=offset)
        return jsonify(entries)
    except Exception as exc:
        logger.exception("获取 URL 黑名单失败: %s", exc)
        return jsonify({
            "error": "获取 URL 黑名单失败",
            "message": str(exc)
        }), 500


@url_blacklist_bp.route("", methods=["POST"])
def create_blacklist_entry():
    """新增黑名单 URL"""
    try:
        data = request.get_json() or {}
        url = data.get("url")
        
        if not url or not isinstance(url, str):
            return jsonify({"error": "url 为必填字段，且必须是字符串"}), 400
        
        entry_id = add_url_to_blacklist(url=url)
        return jsonify({
            "id": entry_id,
            "url": url.strip()
        }), 201
    except ValueError as ve:
        return jsonify({
            "error": str(ve)
        }), 400
    except Exception as exc:
        logger.exception("新增 URL 黑名单失败: %s", exc)
        return jsonify({
            "error": "新增 URL 黑名单失败",
            "message": str(exc)
        }), 500


@url_blacklist_bp.route("/<int:entry_id>", methods=["DELETE"])
def delete_blacklist_entry(entry_id: int):
    """删除黑名单记录"""
    try:
        deleted = delete_url_from_blacklist(entry_id)
        if not deleted:
            return jsonify({"error": "未找到对应的黑名单记录"}), 404
        
        return jsonify({"success": True})
    except Exception as exc:
        logger.exception("删除 URL 黑名单失败: %s", exc)
        return jsonify({
            "error": "删除 URL 黑名单失败",
            "message": str(exc)
        }), 500

