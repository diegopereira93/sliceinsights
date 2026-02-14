"""
Price Alerts Service.

Serviço para detectar quedas de preço e enviar notificações.
"""

import os
import httpx
from datetime import datetime
from dataclasses import dataclass


@dataclass
class PriceAlert:
    """Representa um alerta de queda de preço."""
    product_id: str
    brand_name: str
    model_name: str
    previous_price: float
    current_price: float
    drop_pct: float
    product_url: str


class PriceAlertService:
    """Serviço para gerenciar alertas de preço."""
    
    def __init__(self):
        self.webhook_url = os.getenv("PRICE_ALERT_WEBHOOK_URL", "")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    
    def send_webhook(self, alerts: list[PriceAlert]) -> bool:
        """Envia alertas via webhook genérico (Discord, Slack, etc)."""
        if not self.webhook_url:
            return False
        
        message = self._format_message(alerts)
        
        try:
            response = httpx.post(
                self.webhook_url,
                json={"content": message},
                timeout=10.0
            )
            return response.is_success
        except Exception as e:
            print(f"❌ Erro ao enviar webhook: {e}")
            return False
    
    def send_telegram(self, alerts: list[PriceAlert]) -> bool:
        """Envia alertas via Telegram."""
        if not self.telegram_token or not self.telegram_chat_id:
            return False
        
        message = self._format_message(alerts, markdown=True)
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            response = httpx.post(
                url,
                json={
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                },
                timeout=10.0
            )
            return response.is_success
        except Exception as e:
            print(f"❌ Erro ao enviar Telegram: {e}")
            return False
    
    def _format_message(self, alerts: list[PriceAlert], markdown: bool = False) -> str:
        """Formata mensagem de alerta."""
        if not alerts:
            return "Nenhum alerta de preço hoje."
        
        lines = ["🔥 **ALERTAS DE PREÇO** 🔥\n" if markdown else "🔥 ALERTAS DE PREÇO 🔥\n"]
        
        for alert in alerts:
            if markdown:
                lines.append(
                    f"🏓 *{alert.brand_name} {alert.model_name}*\n"
                    f"   💰 ~~R$ {alert.previous_price:.2f}~~ → R$ {alert.current_price:.2f}\n"
                    f"   📉 Queda de {alert.drop_pct:.1f}%\n"
                    f"   🛒 [Comprar]({alert.product_url})\n"
                )
            else:
                lines.append(
                    f"🏓 {alert.brand_name} {alert.model_name}\n"
                    f"   💰 R$ {alert.previous_price:.2f} → R$ {alert.current_price:.2f}\n"
                    f"   📉 Queda de {alert.drop_pct:.1f}%\n"
                    f"   🛒 {alert.product_url}\n"
                )
        
        lines.append(f"\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        return "\n".join(lines)
    
    def notify(self, alerts: list[PriceAlert]) -> dict:
        """Envia notificações por todos os canais configurados."""
        results = {
            "webhook": False,
            "telegram": False,
            "alerts_count": len(alerts)
        }
        
        if not alerts:
            return results
        
        if self.webhook_url:
            results["webhook"] = self.send_webhook(alerts)
        
        if self.telegram_token:
            results["telegram"] = self.send_telegram(alerts)
        
        return results


def get_price_alert_service() -> PriceAlertService:
    """Factory para o serviço de alertas."""
    return PriceAlertService()
