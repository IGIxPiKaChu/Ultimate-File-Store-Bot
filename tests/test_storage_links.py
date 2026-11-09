import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.update({
    "TG_BOT_TOKEN": "123456:example-token",
    "APP_ID": "12345",
    "API_HASH": "0123456789abcdef0123456789abcdef",
    "CHANNEL_ID": "-1001111111111",
    "OWNER_ID": "1",
    "DB_URL": "mongodb://127.0.0.1:27017",
    "FORCE_SUB_CHANNEL": "-1003333333333",
    "FORCE_SUB_REQUEST_CHANNELS": "-1003333333333",
})

from core import delivery, fsub
from core.pipeline import parse_request
from helper_func import decode, encode, encode_storage_link, get_message_id
from pyrogram.enums import ChatMemberStatus


class StorageLinkTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        primary = SimpleNamespace(id=-1001111111111, username="primary")
        additional = SimpleNamespace(id=-1002222222222, username="secondary")

        class FakeClient:
            db_channel = primary
            db_channels = {
                primary.id: primary,
                additional.id: additional,
            }

        self.client = FakeClient()

    async def test_batch_link_routes_to_configured_channel(self):
        payload = await encode_storage_link(-1002222222222, 20, 22)
        request = await parse_request(self.client, payload)

        self.assertLessEqual(len(payload), 64)
        self.assertEqual(request.kind, "file")
        self.assertEqual(request.ids, [20, 21, 22])
        self.assertEqual(request.source_channel, -1002222222222)

    async def test_legacy_link_still_uses_primary_channel(self):
        payload = await encode(f"get-{17 * abs(self.client.db_channel.id)}")
        request = await parse_request(self.client, payload)

        self.assertEqual(request.kind, "file")
        self.assertEqual(request.ids, [17])
        self.assertEqual(request.source_channel, self.client.db_channel.id)

    async def test_batch_range_is_capped_before_allocation(self):
        payload = await encode("get2-1002222222222-1-999999999999999999")
        request = await parse_request(self.client, payload)

        self.assertEqual(len(request.ids), 1000)
        self.assertEqual(request.ids[0], 1)
        self.assertEqual(request.ids[-1], 1000)

    async def test_unknown_storage_channel_is_rejected(self):
        payload = await encode_storage_link(-1003333333333, 10)
        request = await parse_request(self.client, payload)

        self.assertEqual(request.kind, "invalid")

    async def test_forwarded_post_and_private_post_link_are_resolved(self):
        forwarded = SimpleNamespace(
            forward_origin=SimpleNamespace(
                chat=self.client.db_channels[-1002222222222],
                message_id=31,
            ),
            text=None,
        )
        post_link = SimpleNamespace(
            forward_origin=None,
            text="https://t.me/c/2222222222/31",
        )

        self.assertEqual(
            await get_message_id(self.client, forwarded),
            (-1002222222222, 31),
        )
        self.assertEqual(
            await get_message_id(self.client, post_link),
            (-1002222222222, 31),
        )

    async def test_new_payload_identifies_channel_and_range(self):
        payload = await encode_storage_link(-1002222222222, 20, 22)

        self.assertEqual(await decode(payload), "get2-1002222222222-20-22")

    async def test_request_force_sub_uses_join_request_invite(self):
        class FakeFsubClient:
            async def get_chat(self, chat_id):
                return SimpleNamespace(
                    id=-1003333333333,
                    title="Requests",
                    username=None,
                    invite_link=None,
                )

            async def create_chat_invite_link(self, chat_id, **kwargs):
                self.request_options = kwargs
                return SimpleNamespace(invite_link="https://t.me/+request-link")

            async def get_chat_member(self, chat_id, user_id):
                return SimpleNamespace(status=ChatMemberStatus.ADMINISTRATOR)

        client = FakeFsubClient()
        chats = await fsub.setup(client)

        self.assertEqual(len(chats), 1)
        self.assertTrue(chats[0].request_join)
        self.assertEqual(client.request_options, {"creates_join_request": True})
        self.assertEqual(chats[0].link, "https://t.me/+request-link")

    async def test_delivery_controls_hide_caption_and_add_button(self):
        class FakeMessage:
            caption = SimpleNamespace(html="original caption")
            document = None
            video = None
            audio = None
            animation = None

            async def copy(self, **kwargs):
                self.copy_options = kwargs
                return self

        message = FakeMessage()
        with (
            patch.object(delivery, "HIDE_CAPTION", True),
            patch.object(delivery, "DELIVERY_BUTTON_TEXT", "Visit"),
            patch.object(delivery, "DELIVERY_BUTTON_URL", "https://example.org"),
        ):
            self.assertEqual(delivery._caption(message), "")
            await delivery._copy(message, 123)

        self.assertEqual(message.copy_options["caption"], "")
        button = message.copy_options["reply_markup"].inline_keyboard[0][0]
        self.assertEqual(button.text, "Visit")
        self.assertEqual(button.url, "https://example.org")


if __name__ == "__main__":
    unittest.main()
