"""Async message bus used for all inter-agent communication.

Every agent subscribes with its id; messages are delivered through
per-recipient asyncio queues so that a slow consumer never blocks the
