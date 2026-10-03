"""課題1の本体（ここを実装する）。仕様は CHALLENGE.md を見てください。"""

from __future__ import annotations

import html
import json
import re

TITLE_MAX = 40          # サイトの記事タイトル
BODY_MAX = 800          # サイトの記事本文
ALT_MAX = 100           # 写真の代替テキスト
TAGS_MAX = 5            # タグの数
GBP_MAX = 1500          # Googleビジネスプロフィールの投稿
INSTAGRAM_MAX = 2200    # Instagramのキャプション
HASHTAG_MAX = 30        # Instagramのハッシュタグの数

PHONE_MASK = "［電話番号］"
EMAIL_MASK = "［メール］"


def mask_personal_info(text: str) -> str:
    """半角数字の電話番号を PHONE_MASK に、メールアドレスを EMAIL_MASK に置き換える。"""
    raise NotImplementedError


def build_posts(message: dict, shop: dict, llm) -> dict:
    """メッセージと店の情報から、3つの投稿先の下書きをつくって返す。"""
    raise NotImplementedError


def to_cms_payload(result: dict, message: dict) -> dict:
    """build_posts の結果を、サイトのCMSに渡す形に変える。"""
    raise NotImplementedError
