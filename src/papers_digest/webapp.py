from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any

from flask import Flask, jsonify, render_template_string, request

from papers_digest.settings import (
    ChannelConfig,
    add_channel,
    get_channel_config,
    load_settings,
    remove_channel,
    save_settings,
)

logger = logging.getLogger(__name__)

app = Flask(__name__)


def _verify_telegram_webapp(init_data: str) -> bool:
    """Verify Telegram WebApp init data."""
    bot_token = os.getenv("PAPERS_DIGEST_BOT_TOKEN", "")
    if not bot_token:
        return False
    
    try:
        # Parse init_data
        pairs = init_data.split("&")
        data = {}
        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                data[key] = value
        
        # Extract hash
        received_hash = data.pop("hash", "")
        if not received_hash:
            return False
        
        # Create data check string
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        
        # Calculate secret key
        secret_key = hmac.new(
            "WebAppData".encode(), bot_token.encode(), hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == received_hash
    except Exception as e:
        logger.error(f"Error verifying Telegram WebApp: {e}")
        return False


@app.route("/")
def index():
    """Main Mini-App page."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Papers Digest - Управление каналами</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
            padding: 16px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 24px;
            color: var(--tg-theme-text-color, #000000);
        }
        .channel-card {
            background: var(--tg-theme-secondary-bg-color, #f0f0f0);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .channel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .channel-id {
            font-weight: 600;
            font-size: 16px;
        }
        .channel-info {
            font-size: 14px;
            color: var(--tg-theme-hint-color, #999999);
            margin: 4px 0;
        }
        .btn {
            background: var(--tg-theme-button-color, #3390ec);
            color: var(--tg-theme-button-text-color, #ffffff);
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 14px;
            cursor: pointer;
            margin: 4px;
        }
        .btn-danger {
            background: #ff3b30;
        }
        .btn-secondary {
            background: var(--tg-theme-secondary-bg-color, #f0f0f0);
            color: var(--tg-theme-text-color, #000000);
        }
        .form-group {
            margin-bottom: 16px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--tg-theme-hint-color, #e0e0e0);
            border-radius: 8px;
            font-size: 14px;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
        }
        .add-channel-form {
            background: var(--tg-theme-secondary-bg-color, #f0f0f0);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 24px;
        }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--tg-theme-hint-color, #999999);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Управление каналами</h1>
        
        <div class="add-channel-form">
            <h2 style="font-size: 18px; margin-bottom: 16px;">Добавить канал</h2>
            <div class="form-group">
                <label>ID канала или @username</label>
                <input type="text" id="channelId" placeholder="@channel или -1001234567890">
            </div>
            <div class="form-group">
                <label>Область науки</label>
                <input type="text" id="scienceArea" placeholder="например: artificial intelligence">
            </div>
            <button class="btn" onclick="addChannel()">Добавить канал</button>
        </div>
        
        <div id="channelsList"></div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        async function loadChannels() {
            try {
                const initData = tg.initData;
                const response = await fetch('/api/channels', {
                    headers: {
                        'X-Telegram-Init-Data': initData
                    }
                });
                const data = await response.json();
                displayChannels(data.channels || []);
            } catch (error) {
                console.error('Error loading channels:', error);
                tg.showAlert('Ошибка загрузки каналов');
            }
        }

        function displayChannels(channels) {
            const container = document.getElementById('channelsList');
            if (channels.length === 0) {
                container.innerHTML = '<div class="empty-state">Каналы не настроены</div>';
                return;
            }
            
            container.innerHTML = channels.map(channel => `
                <div class="channel-card">
                    <div class="channel-header">
                        <div class="channel-id">${escapeHtml(channel.channel_id)}</div>
                        <button class="btn btn-danger" onclick="removeChannel('${escapeHtml(channel.channel_id)}')">Удалить</button>
                    </div>
                    <div class="channel-info">Область: ${escapeHtml(channel.science_area || 'не установлена')}</div>
                    <div class="channel-info">Время публикации: ${escapeHtml(channel.post_time || 'не установлено')}</div>
                    <div class="channel-info">LLM: ${channel.use_llm ? 'включен' : 'выключен'}</div>
                    <button class="btn btn-secondary" onclick="editChannel('${escapeHtml(channel.channel_id)}')">Редактировать</button>
                </div>
            `).join('');
        }

        async function addChannel() {
            const channelId = document.getElementById('channelId').value.trim();
            const scienceArea = document.getElementById('scienceArea').value.trim();
            
            if (!channelId) {
                tg.showAlert('Введите ID канала');
                return;
            }
            
            try {
                const initData = tg.initData;
                const response = await fetch('/api/channels', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Telegram-Init-Data': initData
                    },
                    body: JSON.stringify({
                        channel_id: channelId,
                        science_area: scienceArea
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    tg.showAlert('Канал добавлен');
                    document.getElementById('channelId').value = '';
                    document.getElementById('scienceArea').value = '';
                    loadChannels();
                } else {
                    tg.showAlert(data.error || 'Ошибка добавления канала');
                }
            } catch (error) {
                console.error('Error adding channel:', error);
                tg.showAlert('Ошибка добавления канала');
            }
        }

        async function removeChannel(channelId) {
            if (!confirm('Удалить канал ' + channelId + '?')) {
                return;
            }
            
            try {
                const initData = tg.initData;
                const response = await fetch(`/api/channels/${encodeURIComponent(channelId)}`, {
                    method: 'DELETE',
                    headers: {
                        'X-Telegram-Init-Data': initData
                    }
                });
                
                const data = await response.json();
                if (data.success) {
                    tg.showAlert('Канал удален');
                    loadChannels();
                } else {
                    tg.showAlert(data.error || 'Ошибка удаления канала');
                }
            } catch (error) {
                console.error('Error removing channel:', error);
                tg.showAlert('Ошибка удаления канала');
            }
        }

        function editChannel(channelId) {
            tg.showAlert('Редактирование будет доступно в следующей версии');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Load channels on page load
        loadChannels();
    </script>
</body>
</html>
    """
    return render_template_string(html)


@app.route("/api/channels", methods=["GET"])
def get_channels():
    """Get all channels."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not _verify_telegram_webapp(init_data):
        return jsonify({"error": "Unauthorized"}), 401
    
    settings = load_settings()
    channels = [
        {
            "channel_id": config.channel_id,
            "science_area": config.science_area,
            "post_time": config.post_time,
            "use_llm": config.use_llm,
            "summarizer_provider": config.summarizer_provider,
            "enabled": config.enabled,
        }
        for config in settings.channels.values()
    ]
    return jsonify({"channels": channels})


@app.route("/api/channels", methods=["POST"])
def create_channel():
    """Create a new channel."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not _verify_telegram_webapp(init_data):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    channel_id = data.get("channel_id", "").strip()
    science_area = data.get("science_area", "").strip()
    
    if not channel_id:
        return jsonify({"success": False, "error": "Channel ID is required"}), 400
    
    settings = load_settings()
    add_channel(settings, channel_id, science_area)
    save_settings(settings)
    
    return jsonify({"success": True})


@app.route("/api/channels/<channel_id>", methods=["DELETE"])
def delete_channel(channel_id: str):
    """Delete a channel."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not _verify_telegram_webapp(init_data):
        return jsonify({"error": "Unauthorized"}), 401
    
    settings = load_settings()
    if remove_channel(settings, channel_id):
        save_settings(settings)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Channel not found"}), 404


@app.route("/api/channels/<channel_id>", methods=["PUT"])
def update_channel(channel_id: str):
    """Update channel configuration."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not _verify_telegram_webapp(init_data):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    settings = load_settings()
    config = get_channel_config(settings, channel_id)
    
    if not config:
        return jsonify({"success": False, "error": "Channel not found"}), 404
    
    if "science_area" in data:
        config.science_area = data["science_area"].strip()
    if "post_time" in data:
        config.post_time = data["post_time"].strip()
    if "use_llm" in data:
        config.use_llm = bool(data["use_llm"])
    if "summarizer_provider" in data:
        config.summarizer_provider = data["summarizer_provider"]
    if "enabled" in data:
        config.enabled = bool(data["enabled"])
    
    save_settings(settings)
    return jsonify({"success": True})


def main() -> None:
    """Run the web server."""
    port = int(os.getenv("PAPERS_DIGEST_WEB_PORT", "5000"))
    host = os.getenv("PAPERS_DIGEST_WEB_HOST", "127.0.0.1")
    app.run(host=host, port=port, debug=False)

