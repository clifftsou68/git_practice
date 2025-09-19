"""Notification channels for alerts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Alert:
    title: str
    message: str
    level: str = "info"


class BaseChannel:
    def send(self, alert: Alert) -> None:  # pragma: no cover - to be overridden
        raise NotImplementedError


class ConsoleChannel(BaseChannel):
    def send(self, alert: Alert) -> None:
        print(f"[{alert.level.upper()}] {alert.title}: {alert.message}")


class NotificationManager:
    def __init__(self) -> None:
        self.channels: List[BaseChannel] = []

    def register(self, channel: BaseChannel) -> None:
        self.channels.append(channel)

    def dispatch(self, alert: Alert) -> None:
        for channel in self.channels:
            channel.send(alert)


__all__ = ["Alert", "ConsoleChannel", "NotificationManager"]
