# -*- coding: utf-8 -*-
"""
Persistent per-account Telegram client manager.

Provides:
  AccountWorker  — one persistent TelegramClient per Telegram account.
  WorkerPool     — manages all workers; watchdog + auto-restart.

Every send / forward / join call reuses the *same* connected client,
avoiding the costly create→connect→work→disconnect cycle and keeping
Telethon's dialog cache warm so entity-resolution never hits PeerUser.
"""
import asyncio
import logging
import random
import re
from datetime import datetime

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import (
    Channel, Chat, InputPeerChannel, InputPeerChat, PeerChannel, PeerChat,
)
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.errors import (
    FloodWaitError, UserAlreadyParticipantError,
    InviteHashExpiredError, InviteHashInvalidError,
    ChatWriteForbiddenError,
)

from PyToday import database as db, config
from PyToday.encryption import decrypt_data

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _is_free_tier(user_id: int) -> bool:
    """Return True if user is free/trial (not premium/owner)."""
    role = db.get_user_role(user_id)
    return role in (None, "user", "trial")

FREE_WATERMARK = f"\n\nvia @{config.BOT_USERNAME}"
FREE_BIO = f"Automated message via @{config.BOT_USERNAME}\nChannel: @reyaeron"


async def _resolve_entity(client, chat_id, access_hash=None):
    """Robustly resolve a Telethon entity."""
    chat_str = str(chat_id)

    if access_hash:
        try:
            raw_id = int(chat_str[4:]) if chat_str.startswith("-100") else abs(int(chat_str))
            return InputPeerChannel(channel_id=raw_id, access_hash=int(access_hash))
        except Exception:
            pass

    try:
        return await client.get_entity(chat_id)
    except Exception:
        pass

    try:
        if chat_str.startswith("-100"):
            return await client.get_input_entity(PeerChannel(int(chat_str[4:])))
        elif chat_str.startswith("-"):
            return await client.get_input_entity(PeerChat(abs(int(chat_str))))
        else:
            return await client.get_input_entity(PeerChannel(abs(int(chat_str))))
    except Exception:
        pass

    return int(chat_id)


# ──────────────────────────────────────────────────────────────────────────────
# AccountWorker
# ──────────────────────────────────────────────────────────────────────────────

class AccountWorker:
    """Persistent Telethon client for one Telegram account."""

    MAX_RETRIES = 3
    RECONNECT_DELAY = 5  # seconds

    def __init__(self, account_id: int, user_id: int):
        self.account_id = account_id
        self.user_id = user_id
        self.client: TelegramClient | None = None
        self._connected = False
        self._lock = asyncio.Lock()

    # ── lifecycle ──────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """Connect and cache dialogs.  Safe to call repeatedly."""
        if self._connected and self.client and self.client.is_connected():
            return True

        account = db.get_account(self.account_id)
        if not account or not account.get("is_logged_in"):
            logger.warning(f"Worker {self.account_id}: account not logged in")
            return False

        api_id = decrypt_data(account.get("api_id", ""))
        api_hash = decrypt_data(account.get("api_hash", ""))
        session_string = decrypt_data(account.get("session_string", ""))

        self.client = TelegramClient(StringSession(session_string), int(api_id), api_hash)
        await self.client.connect()

        if not await self.client.is_user_authorized():
            await self.client.disconnect()
            self._connected = False
            logger.warning(f"Worker {self.account_id}: session expired")
            return False

        # Warm the entity cache so PeerUser errors don't happen
        try:
            await self.client.get_dialogs(limit=500)
        except Exception:
            pass

        self._connected = True
        logger.info(f"Worker {self.account_id}: connected ✓")
        return True

    async def disconnect(self):
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        self._connected = False

    async def ensure_connected(self) -> bool:
        """Reconnect if the connection dropped."""
        async with self._lock:
            if self._connected and self.client and self.client.is_connected():
                return True
            logger.info(f"Worker {self.account_id}: reconnecting …")
            self._connected = False
            return await self.connect()

    # ── sending ────────────────────────────────────────────────────────────

    async def send_message(self, chat_id, text: str, access_hash=None) -> dict:
        """Send a text message to a group.  Handles flood-wait + reconnect."""
        for attempt in range(self.MAX_RETRIES):
            if not await self.ensure_connected():
                return {"success": False, "error": "Cannot connect"}
            try:
                entity = await _resolve_entity(self.client, chat_id, access_hash)
                await self.client.send_message(entity, text)

                db.update_account(self.account_id, last_used=datetime.utcnow().isoformat())
                db.increment_stat(self.account_id, "messages_sent")
                return {"success": True}

            except FloodWaitError as e:
                wait = e.seconds + random.randint(3, 10)
                logger.warning(f"Worker {self.account_id}: FloodWait {e.seconds}s → sleeping {wait}s")
                await asyncio.sleep(wait)
            except (ConnectionError, OSError):
                logger.warning(f"Worker {self.account_id}: connection lost, reconnecting …")
                self._connected = False
                await asyncio.sleep(self.RECONNECT_DELAY)
            except ChatWriteForbiddenError:
                db.increment_stat(self.account_id, "messages_failed")
                return {"success": False, "error": "No write permission in this group"}
            except Exception as e:
                db.increment_stat(self.account_id, "messages_failed")
                return {"success": False, "error": str(e)}

        db.increment_stat(self.account_id, "messages_failed")
        return {"success": False, "error": "Max retries exceeded"}

    async def forward_from_saved(self, chat_id, access_hash=None) -> dict:
        """Forward the latest Saved-Messages item to a group."""
        for attempt in range(self.MAX_RETRIES):
            if not await self.ensure_connected():
                return {"success": False, "error": "Cannot connect"}
            try:
                me = await self.client.get_me()
                messages = await self.client.get_messages(me, limit=1)
                if not messages:
                    return {"success": False, "error": "No saved message found"}

                entity = await _resolve_entity(self.client, chat_id, access_hash)

                await self.client.forward_messages(entity, messages[0].id, me)

                db.update_account(self.account_id, last_used=datetime.utcnow().isoformat())
                db.increment_stat(self.account_id, "messages_sent")
                return {"success": True}

            except FloodWaitError as e:
                wait = e.seconds + random.randint(3, 10)
                logger.warning(f"Worker {self.account_id}: FloodWait {e.seconds}s → sleeping {wait}s")
                await asyncio.sleep(wait)
            except (ConnectionError, OSError):
                self._connected = False
                await asyncio.sleep(self.RECONNECT_DELAY)
            except Exception as e:
                db.increment_stat(self.account_id, "messages_failed")
                return {"success": False, "error": str(e)}

        db.increment_stat(self.account_id, "messages_failed")
        return {"success": False, "error": "Max retries exceeded"}

    # ── group joining ──────────────────────────────────────────────────────

    async def join_group(self, invite_link: str) -> dict:
        """Join a group by invite link or @username.  Handles flood + retries."""
        for attempt in range(self.MAX_RETRIES):
            if not await self.ensure_connected():
                return {"success": False, "error": "Cannot connect"}
            try:
                hash_pat = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me)/(?:joinchat/|\+)([a-zA-Z0-9_-]+)")
                user_pat = re.compile(r"(?:https?://)?(?:t\.me|telegram\.me)/([a-zA-Z][\w]{3,})")

                hm = hash_pat.search(invite_link)
                um = user_pat.search(invite_link)

                if hm:
                    result = await self.client(ImportChatInviteRequest(hm.group(1)))
                    chat = result.chats[0] if hasattr(result, "chats") and result.chats else None
                    title = getattr(chat, "title", None) if chat else None
                    gid = chat.id if chat else None
                elif um:
                    entity = await self.client.get_entity(um.group(1))
                    await self.client(JoinChannelRequest(entity))
                    title = getattr(entity, "title", None)
                    gid = entity.id
                else:
                    return {"success": False, "error": "Invalid invite link format"}

                db.log_group_join(self.account_id, gid, title, invite_link)
                db.increment_stat(self.account_id, "groups_joined")
                return {"success": True, "group_title": title, "group_id": gid}

            except UserAlreadyParticipantError:
                return {"success": False, "error": "Already a member of this group"}
            except (InviteHashExpiredError, InviteHashInvalidError):
                return {"success": False, "error": "Invalid or expired invite link"}
            except FloodWaitError as e:
                wait = e.seconds + random.randint(3, 10)
                logger.warning(f"Worker {self.account_id}: FloodWait on join → sleeping {wait}s")
                await asyncio.sleep(wait)
            except (ConnectionError, OSError):
                self._connected = False
                await asyncio.sleep(self.RECONNECT_DELAY)
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "Max retries exceeded"}

    # ── broadcast ──────────────────────────────────────────────────────────

    async def broadcast(self, message: str, delay: int, use_forward: bool,
                        target_groups: list | None, logs_channel_id=None,
                        cancel_flags: dict | None = None, cancel_user_id: int | None = None):
        """
        Broadcast to groups.  If target_groups is provided, send ONLY to those.
        Otherwise fetch all groups from dialogs.
        """
        if target_groups is not None:
            groups = target_groups
        else:
            if not await self.ensure_connected():
                return {"success": False, "error": "Cannot connect"}
            groups = await self._fetch_all_groups()

        account = db.get_account(self.account_id)
        acc_name = account.get("account_first_name", "Unknown") if account else "Unknown"

        sent = 0
        failed = 0

        for group in groups:
            # Check cancel flag
            if cancel_flags and cancel_user_id is not None:
                if not cancel_flags.get(cancel_user_id, False):
                    break

            gid = group.get("group_id") or group.get("id")
            ahash = group.get("access_hash")
            gtitle = group.get("group_title") or group.get("title", "Unknown")

            if use_forward:
                result = await self.forward_from_saved(gid, ahash)
            else:
                result = await self.send_message(gid, message, ahash)

            if result["success"]:
                sent += 1
                if logs_channel_id:
                    await _log_to_channel(logs_channel_id, acc_name, gtitle, gid, True)
            else:
                failed += 1
                if logs_channel_id:
                    await _log_to_channel(logs_channel_id, acc_name, gtitle, gid, False, result.get("error"))

            # Interruptible sleep with random jitter
            jittered_delay = delay + random.randint(1, 5)
            for _ in range(jittered_delay):
                if cancel_flags and cancel_user_id is not None:
                    if not cancel_flags.get(cancel_user_id, False):
                        break
                await asyncio.sleep(1)

        db.create_or_update_stats(self.account_id, last_broadcast=datetime.utcnow().isoformat())
        return {"success": True, "sent": sent, "failed": failed, "total": len(groups)}

    async def _fetch_all_groups(self) -> list:
        """Fetch all non-broadcast groups from dialogs."""
        groups = []
        try:
            dialogs = await self.client.get_dialogs(limit=500)
            for d in dialogs:
                e = d.entity
                if isinstance(e, Channel):
                    if e.broadcast or not e.megagroup:
                        continue
                if getattr(e, "left", False) or getattr(e, "kicked", False):
                    continue
                if isinstance(e, (Channel, Chat)):
                    groups.append({
                        "id": e.id,
                        "title": d.title or "Unknown",
                        "access_hash": getattr(e, "access_hash", None),
                    })
        except Exception as ex:
            logger.error(f"Worker {self.account_id}: error fetching groups: {ex}")
        return groups

    # ── auto-reply listener ────────────────────────────────────────────────

    async def start_auto_reply(self, reply_text: str | None = None):
        """Start listening for DMs and auto-replying.  Runs until disconnected."""
        if not await self.ensure_connected():
            return False

        @self.client.on(events.NewMessage(incoming=True))
        async def _on_dm(event):
            try:
                if not (event.is_private and not event.message.out):
                    return
                sender = await event.get_sender()
                if not sender or sender.bot:
                    return

                from_id = sender.id
                text = event.message.text or ""

                # 1. Keyword reply (advanced)
                kw = db.find_keyword_reply(self.account_id, text) if hasattr(db, "find_keyword_reply") else None
                if kw:
                    if kw.get("media_file_id"):
                        await event.respond(file=kw["media_file_id"], message=kw.get("message_text") or "")
                    else:
                        await event.respond(kw["message_text"])
                    db.increment_stat(self.account_id, "replies_triggered")
                    return

                # 2. Sequential reply
                seq = db.get_next_sequential_reply(self.account_id, from_id) if hasattr(db, "get_next_sequential_reply") else None
                if seq:
                    if seq.get("media_file_id"):
                        await event.respond(file=seq["media_file_id"], message=seq.get("message_text") or "")
                    else:
                        await event.respond(seq.get("message_text") or "")
                    db.increment_stat(self.account_id, "replies_triggered")
                    return

                # 3. Basic auto-reply
                if reply_text:
                    already = db.has_replied_to_user(self.account_id, from_id)
                    if not already:
                        await event.respond(reply_text)
                        db.mark_user_replied(self.account_id, from_id, getattr(sender, "username", None))
                        if hasattr(db, "log_auto_reply"):
                            db.log_auto_reply(self.account_id, from_id, getattr(sender, "username", None))
                        db.increment_stat(self.account_id, "auto_replies_sent")
            except Exception as e:
                logger.error(f"Worker {self.account_id}: auto-reply error: {e}")

        logger.info(f"Worker {self.account_id}: auto-reply listener started ✓")
        return True

    # ── free-tier bio enforcement ──────────────────────────────────────────

    async def enforce_free_bio(self):
        """Set forced last_name and bio for free-tier users (first name untouched)."""
        if not _is_free_tier(self.user_id):
            return
        if not await self.ensure_connected():
            return
        try:
            # Only change last_name and bio — never touch first_name
            forced_last_name = f"@{config.BOT_USERNAME}"

            await self.client(UpdateProfileRequest(
                last_name=forced_last_name,
                about=FREE_BIO
            ))
            logger.info(f"Worker {self.account_id}: free-tier last_name+bio enforced (last_name={forced_last_name})")
        except Exception as e:
            logger.warning(f"Worker {self.account_id}: bio enforcement failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# WorkerPool
# ──────────────────────────────────────────────────────────────────────────────

class WorkerPool:
    """
    Manages all AccountWorkers.  Provides watchdog + auto-restart.
    Singleton — import and use `worker_pool`.
    """

    def __init__(self):
        self._workers: dict[int, AccountWorker] = {}   # account_id → worker

    async def get_worker(self, account_id: int, user_id: int | None = None) -> AccountWorker | None:
        """Get or create an AccountWorker.  Connects if needed."""
        account_id = int(account_id)
        if account_id in self._workers:
            w = self._workers[account_id]
            if await w.ensure_connected():
                return w

        # Need user_id to create a new worker
        if user_id is None:
            acc = db.get_account(account_id)
            user_id = acc.get("user_id") if acc else None
        if user_id is None:
            return None

        w = AccountWorker(account_id, user_id)
        if await w.connect():
            self._workers[account_id] = w
            return w
        return None

    async def remove_worker(self, account_id: int):
        account_id = int(account_id)
        w = self._workers.pop(account_id, None)
        if w:
            await w.disconnect()

    async def shutdown(self):
        for w in list(self._workers.values()):
            await w.disconnect()
        self._workers.clear()

    def get_all_workers(self) -> list[AccountWorker]:
        return list(self._workers.values())


# Module-level singleton
worker_pool = WorkerPool()


# ──────────────────────────────────────────────────────────────────────────────
# Channel logging helper (shared with telethon_handler)
# ──────────────────────────────────────────────────────────────────────────────

async def _log_to_channel(channel_id, acc_name, group_title, group_id, success, error=None):
    try:
        from telegram import Bot
        bot = Bot(token=config.BOT_TOKEN)
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if success:
            txt = (f"<b>✅ MESSAGE SENT</b>\n\n"
                   f"<b>ACCOUNT:</b> <code>{acc_name}</code>\n"
                   f"<b>GROUP:</b> <code>{group_title}</code>\n"
                   f"<b>GROUP ID:</b> <code>{group_id}</code>\n"
                   f"<b>TIME:</b> <code>{ts} UTC</code>")
        else:
            txt = (f"<b>❌ MESSAGE FAILED</b>\n\n"
                   f"<b>ACCOUNT:</b> <code>{acc_name}</code>\n"
                   f"<b>GROUP:</b> <code>{group_title}</code>\n"
                   f"<b>GROUP ID:</b> <code>{group_id}</code>\n"
                   f"<b>ERROR:</b> <code>{error or 'Unknown'}</code>\n"
                   f"<b>TIME:</b> <code>{ts} UTC</code>")
        await bot.send_message(int(channel_id), txt, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Log-to-channel error: {e}")
