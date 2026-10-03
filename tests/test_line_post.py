"""課題1の公開テスト（12本）。応募時は、これとは別の非公開テストでも確認します。"""

import json

import pytest

from fakes import FakeLLM
from line_post import core

SHOP = {"name": "パティスリー森", "tone": "やわらかい", "hashtags": ["#京都カフェ", "#パティスリー森"]}
MESSAGE = {
    "text": "今日から秋限定のモンブランを始めました！",
    "photo_url": "https://example.com/montblanc.jpg",
    "sent_at": "2026-11-02T10:00:00+09:00",
}


def good_json(**overrides):
    data = {
        "title": "秋限定のモンブランが始まりました",
        "body": "今日から秋限定のモンブランを始めました。",
        "alt": "栗のモンブラン",
        "tags": ["新メニュー", "秋限定"],
        "gbp": "秋限定のモンブランが始まりました。",
        "instagram": "秋限定のモンブランが始まりました🌰 #モンブラン",
    }
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


def test_mask_phone_with_hyphen():
    assert core.mask_personal_info("予約は075-123-4567まで") == "予約は［電話番号］まで"


def test_mask_mobile_and_email():
    masked = core.mask_personal_info("09012345678 か shop@example.com へ")
    assert "09012345678" not in masked and "shop@example.com" not in masked
    assert "［電話番号］" in masked and "［メール］" in masked


def test_mask_keeps_dates_and_prices():
    text = "2026-11-02から1,500円で販売"
    assert core.mask_personal_info(text) == text


def test_build_posts_with_valid_json():
    llm = FakeLLM(good_json())
    result = core.build_posts(MESSAGE, SHOP, llm)
    assert result["site"]["title"] == "秋限定のモンブランが始まりました"
    assert result["site"]["alt"] == "栗のモンブラン"
    assert result["needs_review"] is False
    assert len(llm.calls) == 1


def test_prompt_contains_masked_message_in_tags():
    llm = FakeLLM(good_json())
    message = dict(MESSAGE, text="新作です。予約は075-123-4567へ")
    core.build_posts(message, SHOP, llm)
    user = llm.calls[0]["user"]
    assert "<message>" in user and "</message>" in user
    assert "075-123-4567" not in user
    assert "［電話番号］" in user


def test_retry_once_when_json_is_invalid():
    llm = FakeLLM("JSONではない返事です", good_json())
    result = core.build_posts(MESSAGE, SHOP, llm)
    assert len(llm.calls) == 2
    assert result["site"]["title"] == "秋限定のモンブランが始まりました"


def test_fallback_after_two_invalid_outputs():
    llm = FakeLLM("だめ", "やっぱりだめ")
    result = core.build_posts(MESSAGE, SHOP, llm)
    assert len(llm.calls) == 2
    assert result["needs_review"] is True
    assert "モンブラン" in result["site"]["title"]


def test_json_in_code_fence_is_accepted():
    llm = FakeLLM("```json\n" + good_json() + "\n```")
    result = core.build_posts(MESSAGE, SHOP, llm)
    assert result["site"]["title"] == "秋限定のモンブランが始まりました"
    assert len(llm.calls) == 1


def test_long_title_is_clipped_and_flagged():
    llm = FakeLLM(good_json(title="あ" * 60))
    result = core.build_posts(MESSAGE, SHOP, llm)
    assert len(result["site"]["title"]) <= core.TITLE_MAX
    assert result["needs_review"] is True


def test_instagram_has_shop_hashtags_within_limit():
    many = " ".join(f"#tag{i}" for i in range(40))
    llm = FakeLLM(good_json(instagram="秋のモンブラン " + many))
    result = core.build_posts(MESSAGE, SHOP, llm)
    caption = result["instagram"]
    assert "#京都カフェ" in caption and "#パティスリー森" in caption
    assert caption.count("#") <= core.HASHTAG_MAX
    assert len(caption) <= core.INSTAGRAM_MAX


def test_empty_message_without_photo_raises():
    with pytest.raises(ValueError):
        core.build_posts({"text": "   ", "photo_url": None}, SHOP, FakeLLM())


def test_cms_payload_escapes_html_and_drafts_when_review_needed():
    llm = FakeLLM(good_json(body="<script>alert(1)</script>", title="あ" * 60))
    result = core.build_posts(MESSAGE, SHOP, llm)
    payload = core.to_cms_payload(result, MESSAGE)
    assert "<script>" not in payload["body_html"]
    assert "&lt;script&gt;" in payload["body_html"]
    assert payload["status"] == "draft"
    assert payload["image_url"] == MESSAGE["photo_url"]
