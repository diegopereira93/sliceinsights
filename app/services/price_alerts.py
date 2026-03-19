"""
Price Alerts Service.

Dataclass para representar alertas de queda de preço e serviço de notificação
via Telegram e/ou webhook.
"""

import os
from dataclasses import dataclass

import requests


@dataclass
class PriceAlert:
    """Representa um alerta de queda de preço."""
    paddle_id: str
    brand_name: str
    model_name: str
    previous_price: float
    current_price: float
    drop_pct: float
    product_url: str
    store_name: str = ""


class PriceAlertService:
    """Envia alertas de queda de preço via Telegram e/ou webhook."""

    def __init__(self, telegram_token: str, telegram_chat_id: str, webhook_url: str):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.webhook_url = webhook_url

    def _format_telegram_message(self, alerts: list[PriceAlert]) -> str:
        lines = ["🏓 *Alertas de Queda de Preço*\n"]
        for a in alerts:
            lines.append(
                f"• *{a.brand_name} {a.model_name}*\n"
                f"  💰 De R${a.previous_price:.2f} → R${a.current_price:.2f} (-{a.drop_pct:.1f}%)\n"
                f"  🏪 {a.store_name}\n"
                f"  🔗 {a.product_url}"
            )
        return "\n".join(lines)

    def _send_telegram(self, alerts: list[PriceAlert]) -> bool:
        if not self.telegram_token or not self.telegram_chat_id:
            return False
        message = self._format_telegram_message(alerts)
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        resp = requests.post(
            url,
            json={"chat_id": self.telegram_chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=15,
        )
        return resp.ok

    def _send_webhook(self, alerts: list[PriceAlert]) -> bool:
        if not self.webhook_url:
            return False
        payload = [
            {
                "paddle_id": a.paddle_id,
                "brand_name": a.brand_name,
                "model_name": a.model_name,
                "previous_price": a.previous_price,
                "current_price": a.current_price,
                "drop_pct": float(a.drop_pct),
                "product_url": a.product_url,
                "store_name": a.store_name,
            }
            for a in alerts
        ]
        resp = requests.post(self.webhook_url, json=payload, timeout=15)
        return resp.ok

    def notify(self, alerts: list[PriceAlert]) -> dict:
        """Envia notificações e retorna resultado por canal."""
        telegram_ok = self._send_telegram(alerts)
        webhook_ok = self._send_webhook(alerts)
        return {"telegram": telegram_ok, "webhook": webhook_ok}


def get_price_alert_service() -> PriceAlertService:
    """Retorna instância configurada do serviço de alertas via variáveis de ambiente."""
    return PriceAlertService(
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        webhook_url=os.getenv("PRICE_ALERT_WEBHOOK_URL", ""),
    )
