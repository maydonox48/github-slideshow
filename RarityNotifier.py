"""RarityNotifier
A phBot plugin that PMs a target character when Magic / Rare / Legend items appear.
"""
from phBot import *
import phBotChat

PLUGIN_NAME = 'RarityNotifier'
VERSION = '1.1'

# Mesaj gönderilecek karakterin adı
TARGET_CHAR = 'LiderKarakterAdin'  # <-- BURAYI DEĞİŞTİR

# Aynı item için tekrar tekrar mesaj atmamak için
seen_items = set()

# Rarity tespitinde kullanılacak suffix eşleştirmesi
RARITY_SUFFIXES = {
    '_A_RARE': 'Magic',
    '_B_RARE': 'Rare',
    '_C_RARE': 'Legend',
}


def plugin_load():
    log('[%s] v%s yüklendi. Hedef karakter: %s' % (PLUGIN_NAME, VERSION, TARGET_CHAR))


def get_rarity(item):
    """
    Item servername üzerinden rarity tespiti.
    Örnek servername: ITEM_CH_BOW_11_A_RARE
    - _A_RARE -> Magic
    - _B_RARE -> Rare
    - _C_RARE -> Legend
    İstersen buradaki mapping'i kendi serverına göre değiştir.
    """
    servername = item.get('servername', '')
    for suffix, rarity in RARITY_SUFFIXES.items():
        if suffix in servername:
            return rarity
    return None


def build_item_key(item, slot):
    """Benzersiz item key'i üret."""
    return (
        item.get('model'),
        item.get('servername'),
        slot,
        item.get('plus', 0),
    )


def notify_target(item, rarity, slot):
    """
    Seçilen karaktere PM atan fonksiyon.
    """
    name_ = item.get('name', 'Unknown')
    plus = item.get('plus', 0)
    servername = item.get('servername', '')

    msg = '[%s] %s (slot %d, +%d) [%s]' % (
        rarity,
        name_,
        slot,
        plus,
        servername,
    )

    # Private mesaj gönder
    if len(TARGET_CHAR) > 0:
        sent = phBotChat.Private(TARGET_CHAR, msg)
        if sent:
            log('[%s] %s karakterine mesaj gönderildi: %s' % (PLUGIN_NAME, TARGET_CHAR, msg))
        else:
            log('[%s] Mesaj gönderilemedi! Hedef: %s' % (PLUGIN_NAME, TARGET_CHAR))
    else:
        log('[%s] TARGET_CHAR boş, mesaj gönderilmiyor: %s' % (PLUGIN_NAME, msg))


def cleanup_seen_items(items):
    """Sadece çantada duran item'lerin key'lerini tut."""
    global seen_items
    current_keys = set()
    for slot, item in enumerate(items):
        if item is None:
            continue
        rarity = get_rarity(item)
        if not rarity:
            continue
        current_keys.add(build_item_key(item, slot))
    # Çıkartılan/satılan item'leri hafızadan temizle ki aynı modeli tekrar görünce bildirebilelim
    seen_items &= current_keys


def event_loop():
    """
    phBot tarafından her 500 ms'de bir çağrılır.
    Burada inventory’yi kontrol edip Magic/Rare/Legend item bulunca mesaj atıyoruz.
    """
    global seen_items

    inv = get_inventory()
    if not inv:
        return

    items = inv.get('items', [])
    if not items:
        return

    cleanup_seen_items(items)

    # Slot numarasına göre item’leri dolaş
    for slot, item in enumerate(items):
        if item is None:
            continue

        rarity = get_rarity(item)
        if not rarity:
            continue

        # Item için benzersiz bir key üret (model + servername + slot + plus)
        key = build_item_key(item, slot)

        # Daha önce bu item için mesaj attıysak tekrar atma
        if key in seen_items:
            continue

        # Yeni bir Magic / Rare / Legend item, haber ver
        seen_items.add(key)
        notify_target(item, rarity, slot)
