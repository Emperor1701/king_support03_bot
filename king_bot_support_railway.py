# King Bot Support - Telegram Bot
# Python 3.10+
# Install:
#   pip install python-telegram-bot
#
# Run:
#   python king_bot_support.py
#
# Important:
# 1) Put your BotFather token in BOT_TOKEN.
# 2) Start the bot once and send /getid in your admin group to get ADMIN_CHAT_ID.
# 3) Put that number in ADMIN_CHAT_ID so requests are forwarded to your admin group.

import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# Settings
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

BOT_NAME = "كنغ بوت للدعم | King Bot Support"
ADMIN_LINK = "https://t.me/Alking03"

# Put your admin group/chat ID here after you get it with /getid
# Example: ADMIN_CHAT_ID = -1001234567890
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

DB_PATH = Path("king_bot_support.db")

# Anti-spam settings
MIN_SECONDS_BETWEEN_MESSAGES = 15
MAX_MESSAGES_PER_HOUR = 20

# =========================
# Logging
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# Languages / Texts
# =========================

LANGS = {
    "ar": "العربية 🇸🇦",
    "de": "Deutsch 🇩🇪",
    "tr": "Türkçe 🇹🇷",
    "uk": "Українська 🇺🇦",
    "ur": "اردو 🇵🇰",
}

TEXTS = {'ar': {'welcome': 'أهلاً وسهلاً بك في أكاديمية الكنغ التعليمية. يرجى اختيار اللغة للمتابعة:',
        'privacy': 'تنبيه: يتم حفظ بياناتك ورسائلك فقط لأغراض الدعم والمتابعة وتنظيم الطلبات ومنع التكرار.',
        'main': 'مرحباً بك في كنغ بوت للدعم. يرجى اختيار الخدمة المطلوبة من القائمة:',
        'back': 'العودة إلى القائمة الرئيسية',
        'change_lang': 'تغيير اللغة',
        'intensive': 'التدريب المكثف',
        'schedule': 'مواعيد التدريب المكثف',
        'b1': 'B1 (DTZ) الأسئلة والمواد المفيدة',
        'b1_price': 'أسعار B1 (DTZ)',
        'b2': 'B2 (DTB) الأسئلة والمواد المفيدة',
        'b2_price': 'أسعار B2 (DTB)',
        'payment': 'طرق الدفع',
        'contact': 'التواصل مع الإدارة',
        'send_contact': 'يرجى كتابة رسالتك كاملة الآن، مع توضيح الطلب أو الاستفسار. سيتم حفظ الرسالة وتحويلها للإدارة.',
        'request_saved': 'تم استلام طلبك وحفظه بنجاح ✅\nسيتم تحويله إلى الإدارة للمتابعة في أقرب وقت ممكن.',
        'spam_wait': 'يرجى الانتظار قليلاً قبل إرسال رسالة جديدة حتى نتمكن من معالجة طلبك بشكل منظم.',
        'spam_hour': 'تم إرسال عدد كبير من الرسائل خلال وقت قصير. يرجى المحاولة لاحقاً.',
        'unknown': 'يرجى اختيار خدمة من الأزرار الظاهرة، أو إرسال /start للبدء من جديد.',
        'intensive_text': 'تفاصيل الاشتراك في مجموعة التدريب المكثف:\n'
                          '\n'
                          'مدة الاشتراك: شهران\n'
                          'تكلفة الاشتراك: 60 يورو\n'
                          '\n'
                          'يشمل التدريب الأقسام التالية:\n'
                          '• القسم الشفهي\n'
                          '• القسم الكتابي\n'
                          '• نماذج تدريبية لقسم الاستماع\n'
                          '• نماذج تدريبية لقسم القراءة\n'
                          '• نماذج امتحانية مهمة ومتكررة تساعد الطالب على التحضير بشكل أفضل\n'
                          '\n'
                          'كما يتم تنظيم امتحان تجريبي كامل لمستوى B1 كل أسبوع، بهدف تقييم مستوى الطلاب، تحديد نقاط '
                          'الضعف، والعمل على تحسينها بشكل عملي ومنظم.',
        'schedule_text': 'مواعيد التدريب المكثف:\n'
                         '\n'
                         'الاثنين، الثلاثاء، الأربعاء:\n'
                         'من الساعة 9:00 مساءً حتى 11:00 مساءً\n'
                         'المحتوى التدريبي: القسم الشفهي، وصف الصور، البلانات، وطريقة كتابة Brief و E-Mail.\n'
                         '\n'
                         'الخميس:\n'
                         'امتحان تجريبي يبدأ الساعة 9:00 مساءً.\n'
                         '\n'
                         'بالإضافة إلى ذلك، تشرف الآنسة ليلى على تدريبات إضافية من الاثنين إلى الخميس، ويكون الموعد '
                         'غالباً بعد الظهر حوالي الساعة 3:00 أو في الفترة الصباحية.\n'
                         '\n'
                         'أما أيام الجمعة والسبت والأحد، فقد يتم تنظيم تدريبات إضافية حسب توفر الوقت لدى الآنسة ليلى، '
                         'ويتم إبلاغ الطلاب مسبقاً بوقت التدريب وموضوع الدرس.',
        'b1_text': 'للاستفسار عن الأسئلة والمواد المفيدة الخاصة بامتحان B1 (DTZ)، يرجى إرسال المعلومات التالية برسالة '
                   'واحدة:\n'
                   '\n'
                   '1. تاريخ الامتحان\n'
                   '2. وقت بدء الامتحان\n'
                   '3. نوع الامتحان: B1 (DTZ)\n'
                   '4. صورة أو ملف ورقة موعد الامتحان، إن وجدت\n'
                   '\n'
                   'بعد إرسال المعلومات سيتم حفظ طلبك وتحويله إلى الإدارة للمتابعة.',
        'b1_price_text': 'سعر مواد وأسئلة B1 (DTZ):\n200€',
        'b2_text': 'للاستفسار عن الأسئلة والمواد المفيدة الخاصة بامتحان B2 (DTB)، يرجى إرسال المعلومات التالية برسالة '
                   'واحدة:\n'
                   '\n'
                   '1. تاريخ الامتحان\n'
                   '2. وقت بدء الامتحان\n'
                   '3. نوع الامتحان: B2 (DTB)\n'
                   '4. صورة أو ملف ورقة موعد الامتحان، إن وجدت\n'
                   '\n'
                   'ملاحظة: المواد المتوفرة لا تشمل الجزء الشفهي.\n'
                   '\n'
                   'بعد إرسال المعلومات سيتم حفظ طلبك وتحويله إلى الإدارة للمتابعة.',
        'b2_price_text': 'سعر مواد وأسئلة B2 (DTB):\n150€',
        'payment_text': 'طرق الدفع المتاحة:\n'
                        '\n'
                        '1. PayPal\n'
                        '2. تحويل بنكي\n'
                        '3. حوالة إلى سوريا\n'
                        '\n'
                        'للحصول على بيانات الدفع المناسبة، يرجى التواصل مع الإدارة وتحديد الخدمة المطلوبة.',
        'contact_text': 'للتواصل مع الإدارة، يرجى كتابة سبب المراسلة بشكل واضح وكامل.\n'
                        '\n'
                        'يرجى عدم الاكتفاء بإرسال التحية فقط؛ اكتب طلبك أو استفسارك كاملاً حتى تتمكن الإدارة من '
                        'مساعدتك بسرعة ودقة.\n'
                        '\n'
                        'رابط الإدارة:\n'
                        'https://t.me/Alking03'},
 'de': {'welcome': 'Willkommen bei der King Bildungsakademie. Bitte wählen Sie Ihre Sprache aus:',
        'privacy': 'Hinweis: Ihre Daten und Nachrichten werden ausschließlich zur Bearbeitung von Supportanfragen, zur '
                   'Nachverfolgung und zur Vermeidung mehrfacher Anfragen gespeichert.',
        'main': 'Willkommen beim King Bot Support. Bitte wählen Sie den gewünschten Service aus:',
        'back': 'Zurück zum Hauptmenü',
        'change_lang': 'Sprache ändern',
        'intensive': 'Intensivtraining',
        'schedule': 'Termine des Intensivtrainings',
        'b1': 'B1 (DTZ) hilfreiche Fragen und Materialien',
        'b1_price': 'Preise für B1 (DTZ)',
        'b2': 'B2 (DTB) hilfreiche Fragen und Materialien',
        'b2_price': 'Preise für B2 (DTB)',
        'payment': 'Zahlungsmethoden',
        'contact': 'Kontakt zur Verwaltung',
        'send_contact': 'Bitte schreiben Sie jetzt Ihre vollständige Nachricht und beschreiben Sie Ihr Anliegen klar. '
                        'Die Nachricht wird gespeichert und an die Verwaltung weitergeleitet.',
        'request_saved': 'Ihre Anfrage wurde erfolgreich empfangen und gespeichert ✅\n'
                         'Sie wird zur weiteren Bearbeitung an die Verwaltung weitergeleitet.',
        'spam_wait': 'Bitte warten Sie einen Moment, bevor Sie eine weitere Nachricht senden, damit Ihre Anfrage '
                     'geordnet bearbeitet werden kann.',
        'spam_hour': 'Sie haben innerhalb kurzer Zeit zu viele Nachrichten gesendet. Bitte versuchen Sie es später '
                     'erneut.',
        'unknown': 'Bitte wählen Sie einen Service über die angezeigten Buttons aus oder senden Sie /start, um neu zu '
                   'beginnen.',
        'intensive_text': 'Details zur Teilnahme an der Intensivtrainingsgruppe:\n'
                          '\n'
                          'Dauer der Teilnahme: 2 Monate\n'
                          'Teilnahmegebühr: 60 Euro\n'
                          '\n'
                          'Das Training umfasst folgende Bereiche:\n'
                          '• Mündlicher Teil\n'
                          '• Schriftlicher Teil\n'
                          '• Übungsmodelle für den Hörteil\n'
                          '• Übungsmodelle für den Leseteil\n'
                          '• Wichtige und häufig wiederkehrende Prüfungsmodelle zur gezielten Vorbereitung\n'
                          '\n'
                          'Zusätzlich findet jede Woche eine vollständige B1-Probeprüfung statt. Ziel ist es, den '
                          'aktuellen Lernstand der Teilnehmenden zu bewerten, Schwächen zu erkennen und diese '
                          'strukturiert zu verbessern.',
        'schedule_text': 'Termine des Intensivtrainings:\n'
                         '\n'
                         'Montag, Dienstag, Mittwoch:\n'
                         'Von 21:00 bis 23:00 Uhr\n'
                         'Trainingsinhalte: mündlicher Teil, Bildbeschreibung, Pläne sowie das Schreiben von Brief und '
                         'E-Mail.\n'
                         '\n'
                         'Donnerstag:\n'
                         'Probeprüfung ab 21:00 Uhr.\n'
                         '\n'
                         'Zusätzlich betreut Frau Layla von Montag bis Donnerstag weitere Trainingseinheiten. Die '
                         'Termine liegen meistens nachmittags gegen 15:00 Uhr oder am Vormittag.\n'
                         '\n'
                         'Freitag, Samstag und Sonntag können je nach Verfügbarkeit von Frau Layla zusätzliche '
                         'Trainingseinheiten stattfinden. Die Teilnehmenden werden rechtzeitig über Uhrzeit und Thema '
                         'informiert.',
        'b1_text': 'Für Anfragen zu den hilfreichen Fragen und Materialien für B1 (DTZ) senden Sie bitte die folgenden '
                   'Informationen in einer einzigen Nachricht:\n'
                   '\n'
                   '1. Datum Ihrer Prüfung\n'
                   '2. Beginnzeit Ihrer Prüfung\n'
                   '3. Prüfungstyp: B1 (DTZ)\n'
                   '4. Foto oder Datei Ihres Prüfungstermins, falls vorhanden\n'
                   '\n'
                   'Nach dem Senden werden Ihre Angaben gespeichert und zur weiteren Bearbeitung an die Verwaltung '
                   'weitergeleitet.',
        'b1_price_text': 'Preis für B1 (DTZ) Materialien und Fragen:\n200€',
        'b2_text': 'Für Anfragen zu den hilfreichen Fragen und Materialien für B2 (DTB) senden Sie bitte die folgenden '
                   'Informationen in einer einzigen Nachricht:\n'
                   '\n'
                   '1. Datum Ihrer Prüfung\n'
                   '2. Beginnzeit Ihrer Prüfung\n'
                   '3. Prüfungstyp: B2 (DTB)\n'
                   '4. Foto oder Datei Ihres Prüfungstermins, falls vorhanden\n'
                   '\n'
                   'Hinweis: Die verfügbaren Materialien enthalten keinen mündlichen Teil.\n'
                   '\n'
                   'Nach dem Senden werden Ihre Angaben gespeichert und zur weiteren Bearbeitung an die Verwaltung '
                   'weitergeleitet.',
        'b2_price_text': 'Preis für B2 (DTB) Materialien und Fragen:\n150€',
        'payment_text': 'Verfügbare Zahlungsmethoden:\n'
                        '\n'
                        '1. PayPal\n'
                        '2. Banküberweisung\n'
                        '3. Überweisung nach Syrien\n'
                        '\n'
                        'Für die passenden Zahlungsdaten kontaktieren Sie bitte die Verwaltung und nennen Sie den '
                        'gewünschten Service.',
        'contact_text': 'Für den Kontakt mit der Verwaltung schreiben Sie bitte Ihr Anliegen klar und vollständig.\n'
                        '\n'
                        'Bitte senden Sie nicht nur eine Begrüßung, sondern beschreiben Sie Ihre Anfrage oder Ihr '
                        'Problem vollständig, damit die Verwaltung Ihnen schnell und gezielt helfen kann.\n'
                        '\n'
                        'Link zur Verwaltung:\n'
                        'https://t.me/Alking03'},
 'tr': {'welcome': 'King Eğitim Akademisi’ne hoş geldiniz. Devam etmek için lütfen dilinizi seçin:',
        'privacy': 'Bilgilendirme: Bilgileriniz ve mesajlarınız yalnızca destek taleplerinin takibi, düzenlenmesi ve '
                   'tekrar eden başvuruların önlenmesi amacıyla kaydedilir.',
        'main': 'King Bot Support’a hoş geldiniz. Lütfen almak istediğiniz hizmeti seçin:',
        'back': 'Ana menüye dön',
        'change_lang': 'Dili değiştir',
        'intensive': 'Yoğun eğitim',
        'schedule': 'Yoğun eğitim programı',
        'b1': 'B1 (DTZ) faydalı sorular ve materyaller',
        'b1_price': 'B1 (DTZ) ücretleri',
        'b2': 'B2 (DTB) faydalı sorular ve materyaller',
        'b2_price': 'B2 (DTB) ücretleri',
        'payment': 'Ödeme yöntemleri',
        'contact': 'Yönetim ile iletişim',
        'send_contact': 'Lütfen mesajınızı şimdi eksiksiz şekilde yazın ve talebinizi açıkça belirtin. Mesajınız '
                        'kaydedilip yönetime iletilecektir.',
        'request_saved': 'Talebiniz başarıyla alındı ve kaydedildi ✅\nİncelenmesi için yönetime iletilecektir.',
        'spam_wait': 'Talebinizin düzenli şekilde işlenebilmesi için lütfen yeni bir mesaj göndermeden önce kısa bir '
                     'süre bekleyin.',
        'spam_hour': 'Kısa süre içinde çok fazla mesaj gönderdiniz. Lütfen daha sonra tekrar deneyin.',
        'unknown': 'Lütfen ekrandaki butonlardan bir hizmet seçin veya yeniden başlamak için /start yazın.',
        'intensive_text': 'Yoğun eğitim grubuna katılım detayları:\n'
                          '\n'
                          'Katılım süresi: 2 ay\n'
                          'Katılım ücreti: 60 Euro\n'
                          '\n'
                          'Eğitim şu bölümleri kapsar:\n'
                          '• Konuşma bölümü\n'
                          '• Yazma bölümü\n'
                          '• Dinleme bölümü için alıştırma modelleri\n'
                          '• Okuma bölümü için alıştırma modelleri\n'
                          '• Sınava daha iyi hazırlanmayı sağlayan önemli ve sık tekrar eden sınav örnekleri\n'
                          '\n'
                          'Ayrıca öğrencilerin seviyesini değerlendirmek, zayıf noktaları belirlemek ve bu noktalar '
                          'üzerinde düzenli şekilde çalışmak amacıyla her hafta tam bir B1 deneme sınavı yapılır.',
        'schedule_text': 'Yoğun eğitim programı:\n'
                         '\n'
                         'Pazartesi, Salı, Çarşamba:\n'
                         'Saat 21:00 - 23:00\n'
                         'Eğitim içeriği: konuşma bölümü, resim anlatımı, planlar, Brief ve E-Mail yazma yöntemi.\n'
                         '\n'
                         'Perşembe:\n'
                         'Deneme sınavı saat 21:00’de başlar.\n'
                         '\n'
                         'Buna ek olarak, Leyla Hanım pazartesiden perşembeye kadar ek eğitimleri takip eder. Saat '
                         'genellikle öğleden sonra 15:00 civarında veya sabah saatlerinde olur.\n'
                         '\n'
                         'Cuma, cumartesi ve pazar günleri de Leyla Hanım’ın uygunluğuna göre ek eğitimler '
                         'düzenlenebilir. Eğitim saati ve ders konusu öğrencilere önceden bildirilir.',
        'b1_text': 'B1 (DTZ) için faydalı sorular ve materyaller hakkında bilgi almak istiyorsanız, lütfen aşağıdaki '
                   'bilgileri tek mesaj halinde gönderin:\n'
                   '\n'
                   '1. Sınav tarihiniz\n'
                   '2. Sınav başlangıç saatiniz\n'
                   '3. Sınav türü: B1 (DTZ)\n'
                   '4. Varsa sınav randevu belgenizin fotoğrafı veya dosyası\n'
                   '\n'
                   'Bilgileriniz gönderildikten sonra talebiniz kaydedilecek ve yönetime iletilecektir.',
        'b1_price_text': 'B1 (DTZ) materyal ve soru ücreti:\n200€',
        'b2_text': 'B2 (DTB) için faydalı sorular ve materyaller hakkında bilgi almak istiyorsanız, lütfen aşağıdaki '
                   'bilgileri tek mesaj halinde gönderin:\n'
                   '\n'
                   '1. Sınav tarihiniz\n'
                   '2. Sınav başlangıç saatiniz\n'
                   '3. Sınav türü: B2 (DTB)\n'
                   '4. Varsa sınav randevu belgenizin fotoğrafı veya dosyası\n'
                   '\n'
                   'Not: Mevcut materyaller konuşma bölümünü içermez.\n'
                   '\n'
                   'Bilgileriniz gönderildikten sonra talebiniz kaydedilecek ve yönetime iletilecektir.',
        'b2_price_text': 'B2 (DTB) materyal ve soru ücreti:\n150€',
        'payment_text': 'Mevcut ödeme yöntemleri:\n'
                        '\n'
                        '1. PayPal\n'
                        '2. Banka havalesi\n'
                        '3. Suriye’ye havale\n'
                        '\n'
                        'Uygun ödeme bilgilerini almak için lütfen yönetimle iletişime geçin ve almak istediğiniz '
                        'hizmeti belirtin.',
        'contact_text': 'Yönetimle iletişime geçmek için lütfen mesaj nedeninizi açık ve eksiksiz şekilde yazın.\n'
                        '\n'
                        'Sadece selam göndermek yerine, talebinizi veya sorunuzu tam olarak belirtmeniz, yönetimin '
                        'size daha hızlı ve doğru şekilde yardımcı olmasını sağlar.\n'
                        '\n'
                        'Yönetim bağlantısı:\n'
                        'https://t.me/Alking03'},
 'uk': {'welcome': 'Вітаємо в освітній академії King. Будь ласка, оберіть мову для продовження:',
        'privacy': 'Повідомлення: ваші дані та повідомлення зберігаються лише для обробки запитів підтримки, '
                   'подальшого зв’язку та уникнення повторних звернень.',
        'main': 'Вітаємо в King Bot Support. Будь ласка, оберіть потрібну послугу:',
        'back': 'Повернутися до головного меню',
        'change_lang': 'Змінити мову',
        'intensive': 'Інтенсивне навчання',
        'schedule': 'Розклад інтенсивного навчання',
        'b1': 'B1 (DTZ) корисні питання та матеріали',
        'b1_price': 'Ціни B1 (DTZ)',
        'b2': 'B2 (DTB) корисні питання та матеріали',
        'b2_price': 'Ціни B2 (DTB)',
        'payment': 'Способи оплати',
        'contact': 'Зв’язок з адміністрацією',
        'send_contact': 'Будь ласка، напишіть повне повідомлення та чітко опишіть свій запит. Повідомлення буде '
                        'збережено й передано адміністрації.',
        'request_saved': 'Ваш запит успішно отримано та збережено ✅\n'
                         'Його буде передано адміністрації для подальшої обробки.',
        'spam_wait': 'Будь ласка, зачекайте трохи перед надсиланням нового повідомлення, щоб ваш запит було оброблено '
                     'належним чином.',
        'spam_hour': 'Ви надіслали занадто багато повідомлень за короткий час. Будь ласка, спробуйте пізніше.',
        'unknown': 'Будь ласка, оберіть послугу за допомогою кнопок або надішліть /start, щоб почати знову.',
        'intensive_text': 'Деталі участі в групі інтенсивного навчання:\n'
                          '\n'
                          'Тривалість участі: 2 місяці\n'
                          'Вартість участі: 60 євро\n'
                          '\n'
                          'Навчання охоплює такі розділи:\n'
                          '• Усна частина\n'
                          '• Письмова частина\n'
                          '• Тренувальні моделі для аудіювання\n'
                          '• Тренувальні моделі для читання\n'
                          '• Важливі та часто повторювані екзаменаційні приклади для кращої підготовки\n'
                          '\n'
                          'Також щотижня проводиться повний пробний іспит рівня B1, щоб оцінити рівень студентів, '
                          'визначити слабкі місця та системно працювати над їх покращенням.',
        'schedule_text': 'Розклад інтенсивного навчання:\n'
                         '\n'
                         'Понеділок, вівторок, середа:\n'
                         'З 21:00 до 23:00\n'
                         'Зміст занять: усна частина, опис зображень, плани, а також написання Brief та E-Mail.\n'
                         '\n'
                         'Четвер:\n'
                         'Пробний іспит починається о 21:00.\n'
                         '\n'
                         'Крім того, пані Лейла проводить додаткові тренування з понеділка по четвер. Час зазвичай '
                         'припадає на післяобідній період близько 15:00 або на ранок.\n'
                         '\n'
                         'У п’ятницю, суботу та неділю додаткові заняття можуть проводитися залежно від наявності часу '
                         'у пані Лейли. Про час і тему заняття студентів повідомляють заздалегідь.',
        'b1_text': 'Для запиту щодо корисних питань і матеріалів для B1 (DTZ) надішліть, будь ласка, такі дані одним '
                   'повідомленням:\n'
                   '\n'
                   '1. Дату вашого іспиту\n'
                   '2. Час початку іспиту\n'
                   '3. Тип іспиту: B1 (DTZ)\n'
                   '4. Фото або файл документа з датою іспиту, якщо він є\n'
                   '\n'
                   'Після надсилання ваш запит буде збережено та передано адміністрації для подальшої обробки.',
        'b1_price_text': 'Вартість матеріалів і питань B1 (DTZ):\n200€',
        'b2_text': 'Для запиту щодо корисних питань і матеріалів для B2 (DTB) надішліть, будь ласка, такі дані одним '
                   'повідомленням:\n'
                   '\n'
                   '1. Дату вашого іспиту\n'
                   '2. Час початку іспиту\n'
                   '3. Тип іспиту: B2 (DTB)\n'
                   '4. Фото або файл документа з датою іспиту, якщо він є\n'
                   '\n'
                   'Примітка: доступні матеріали не включають усну частину.\n'
                   '\n'
                   'Після надсилання ваш запит буде збережено та передано адміністрації для подальшої обробки.',
        'b2_price_text': 'Вартість матеріалів і питань B2 (DTB):\n150€',
        'payment_text': 'Доступні способи оплати:\n'
                        '\n'
                        '1. PayPal\n'
                        '2. Банківський переказ\n'
                        '3. Переказ до Сирії\n'
                        '\n'
                        'Щоб отримати відповідні платіжні реквізити, зв’яжіться з адміністрацією та вкажіть потрібну '
                        'послугу.',
        'contact_text': 'Щоб зв’язатися з адміністрацією, будь ласка, чітко й повністю опишіть причину звернення.\n'
                        '\n'
                        'Не надсилайте лише привітання — повний опис вашого запиту допоможе адміністрації швидше й '
                        'точніше вам відповісти.\n'
                        '\n'
                        'Посилання на адміністрацію:\n'
                        'https://t.me/Alking03'},
 'ur': {'welcome': 'کنگ ایجوکیشنل اکیڈمی میں خوش آمدید۔ جاری رکھنے کے لیے براہ کرم اپنی زبان منتخب کریں:',
        'privacy': 'اطلاع: آپ کی معلومات اور پیغامات صرف سپورٹ درخواستوں کی پیروی، تنظیم اور بار بار آنے والی '
                   'درخواستوں کو روکنے کے مقصد سے محفوظ کیے جاتے ہیں۔',
        'main': 'کنگ بوٹ سپورٹ میں خوش آمدید۔ براہ کرم مطلوبہ سروس منتخب کریں:',
        'back': 'مرکزی مینو پر واپس جائیں',
        'change_lang': 'زبان تبدیل کریں',
        'intensive': 'انتہائی تربیتی کورس',
        'schedule': 'انتہائی تربیت کے اوقات',
        'b1': 'B1 (DTZ) مفید سوالات اور مواد',
        'b1_price': 'B1 (DTZ) قیمتیں',
        'b2': 'B2 (DTB) مفید سوالات اور مواد',
        'b2_price': 'B2 (DTB) قیمتیں',
        'payment': 'ادائیگی کے طریقے',
        'contact': 'انتظامیہ سے رابطہ',
        'send_contact': 'براہ کرم اپنا مکمل پیغام ابھی لکھیں اور اپنی درخواست واضح طور پر بیان کریں۔ پیغام محفوظ کر کے '
                        'انتظامیہ کو بھیجا جائے گا۔',
        'request_saved': 'آپ کی درخواست کامیابی سے موصول اور محفوظ کر لی گئی ہے ✅\n'
                         'اسے مزید کارروائی کے لیے انتظامیہ کو بھیجا جائے گا۔',
        'spam_wait': 'براہ کرم نیا پیغام بھیجنے سے پہلے تھوڑا انتظار کریں تاکہ آپ کی درخواست منظم طریقے سے دیکھی جا '
                     'سکے۔',
        'spam_hour': 'آپ نے مختصر وقت میں بہت زیادہ پیغامات بھیجے ہیں۔ براہ کرم بعد میں دوبارہ کوشش کریں۔',
        'unknown': 'براہ کرم دکھائے گئے بٹنوں میں سے کوئی سروس منتخب کریں یا دوبارہ شروع کرنے کے لیے /start بھیجیں۔',
        'intensive_text': 'انتہائی تربیتی گروپ میں شمولیت کی تفصیلات:\n'
                          '\n'
                          'مدت: 2 ماہ\n'
                          'فیس: 60 یورو\n'
                          '\n'
                          'تربیت میں درج ذیل حصے شامل ہیں:\n'
                          '• زبانی حصہ\n'
                          '• تحریری حصہ\n'
                          '• سننے کے حصے کے لیے مشقی نمونے\n'
                          '• پڑھنے کے حصے کے لیے مشقی نمونے\n'
                          '• اہم اور بار بار آنے والے امتحانی نمونے جو بہتر تیاری میں مدد دیتے ہیں\n'
                          '\n'
                          'اس کے علاوہ ہر ہفتے مکمل B1 آزمائشی امتحان لیا جاتا ہے، تاکہ طلبہ کی سطح کا اندازہ لگایا جا '
                          'سکے، کمزور نکات معلوم کیے جا سکیں، اور ان پر منظم طریقے سے کام کیا جا سکے۔',
        'schedule_text': 'انتہائی تربیت کے اوقات:\n'
                         '\n'
                         'پیر، منگل، بدھ:\n'
                         'رات 9:00 بجے سے 11:00 بجے تک\n'
                         'تربیتی مواد: زبانی حصہ، تصاویر کی وضاحت، پلانز، اور Brief و E-Mail لکھنے کا طریقہ۔\n'
                         '\n'
                         'جمعرات:\n'
                         'آزمائشی امتحان رات 9:00 بجے شروع ہوتا ہے۔\n'
                         '\n'
                         'اس کے علاوہ پیر سے جمعرات تک مس لیلیٰ اضافی تربیت کی نگرانی کرتی ہیں۔ وقت عموماً دوپہر '
                         'تقریباً 3:00 بجے یا صبح ہوتا ہے۔\n'
                         '\n'
                         'جمعہ، ہفتہ اور اتوار کو بھی مس لیلیٰ کی دستیابی کے مطابق اضافی تربیت ہو سکتی ہے۔ وقت اور سبق '
                         'کے موضوع سے طلبہ کو پہلے آگاہ کر دیا جاتا ہے۔',
        'b1_text': 'B1 (DTZ) کے مفید سوالات اور مواد کے بارے میں معلومات کے لیے براہ کرم درج ذیل معلومات ایک ہی پیغام '
                   'میں بھیجیں:\n'
                   '\n'
                   '1. آپ کے امتحان کی تاریخ\n'
                   '2. امتحان شروع ہونے کا وقت\n'
                   '3. امتحان کی قسم: B1 (DTZ)\n'
                   '4. اگر موجود ہو تو امتحان کی اپائنٹمنٹ شیٹ کی تصویر یا فائل\n'
                   '\n'
                   'معلومات بھیجنے کے بعد آپ کی درخواست محفوظ کر کے مزید کارروائی کے لیے انتظامیہ کو بھیج دی جائے گی۔',
        'b1_price_text': 'B1 (DTZ) مواد اور سوالات کی قیمت:\n200€',
        'b2_text': 'B2 (DTB) کے مفید سوالات اور مواد کے بارے میں معلومات کے لیے براہ کرم درج ذیل معلومات ایک ہی پیغام '
                   'میں بھیجیں:\n'
                   '\n'
                   '1. آپ کے امتحان کی تاریخ\n'
                   '2. امتحان شروع ہونے کا وقت\n'
                   '3. امتحان کی قسم: B2 (DTB)\n'
                   '4. اگر موجود ہو تو امتحان کی اپائنٹمنٹ شیٹ کی تصویر یا فائل\n'
                   '\n'
                   'نوٹ: دستیاب مواد میں زبانی حصہ شامل نہیں ہے۔\n'
                   '\n'
                   'معلومات بھیجنے کے بعد آپ کی درخواست محفوظ کر کے مزید کارروائی کے لیے انتظامیہ کو بھیج دی جائے گی۔',
        'b2_price_text': 'B2 (DTB) مواد اور سوالات کی قیمت:\n150€',
        'payment_text': 'دستیاب ادائیگی کے طریقے:\n'
                        '\n'
                        '1. PayPal\n'
                        '2. بینک ٹرانسفر\n'
                        '3. شام کے لیے حوالہ\n'
                        '\n'
                        'مناسب ادائیگی کی تفصیلات حاصل کرنے کے لیے براہ کرم انتظامیہ سے رابطہ کریں اور مطلوبہ سروس '
                        'واضح کریں۔',
        'contact_text': 'انتظامیہ سے رابطہ کرنے کے لیے براہ کرم اپنی درخواست کی وجہ واضح اور مکمل طور پر لکھیں۔\n'
                        '\n'
                        'صرف سلام بھیجنے کے بجائے، اپنی درخواست یا سوال مکمل طور پر لکھیں تاکہ انتظامیہ آپ کی جلد اور '
                        'درست مدد کر سکے۔\n'
                        '\n'
                        'انتظامیہ کا لنک:\n'
                        'https://t.me/Alking03'}}

MENU_KEYS = [
    "intensive",
    "schedule",
    "b1",
    "b1_price",
    "b2",
    "b2_price",
    "payment",
    "contact",
    "change_lang",
]

# =========================
# Database
# =========================

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'ar',
                first_seen TEXT,
                last_seen TEXT,
                total_messages INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                language TEXT,
                request_type TEXT,
                message TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                created_at INTEGER
            )
        """)
        conn.commit()


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def upsert_user(update: Update, language: Optional[str] = None) -> None:
    user = update.effective_user
    if not user:
        return

    with db() as conn:
        existing = conn.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (user.id,),
        ).fetchone()

        if existing:
            if language:
                conn.execute("""
                    UPDATE users
                    SET username = ?, first_name = ?, last_name = ?, language = ?, last_seen = ?, total_messages = total_messages + 1
                    WHERE user_id = ?
                """, (user.username, user.first_name, user.last_name, language, now_iso(), user.id))
            else:
                conn.execute("""
                    UPDATE users
                    SET username = ?, first_name = ?, last_name = ?, last_seen = ?, total_messages = total_messages + 1
                    WHERE user_id = ?
                """, (user.username, user.first_name, user.last_name, now_iso(), user.id))
        else:
            conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, language, first_seen, last_seen, total_messages)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                language or "ar",
                now_iso(),
                now_iso(),
            ))
        conn.commit()


def get_user_lang(user_id: int) -> str:
    with db() as conn:
        row = conn.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row and row["language"] in TEXTS:
        return row["language"]
    return "ar"


def save_request(update: Update, request_type: str, message: str, lang: Optional[str] = None) -> int:
    user = update.effective_user
    if not user:
        return 0
    lang = lang or get_user_lang(user.id)

    with db() as conn:
        cur = conn.execute("""
            INSERT INTO requests (user_id, username, language, request_type, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            lang,
            request_type,
            message,
            now_iso(),
        ))
        conn.commit()
        return int(cur.lastrowid)


def stats() -> Dict[str, int]:
    with db() as conn:
        users_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        requests_count = conn.execute("SELECT COUNT(*) AS c FROM requests").fetchone()["c"]
    return {"users": users_count, "requests": requests_count}

# =========================
# Anti-spam
# =========================

def check_rate_limit(user_id: int) -> str:
    current = int(time.time())
    hour_ago = current - 3600

    with db() as conn:
        last = conn.execute(
            "SELECT created_at FROM user_activity WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()

        if last and current - int(last["created_at"]) < MIN_SECONDS_BETWEEN_MESSAGES:
            return "wait"

        count_hour = conn.execute(
            "SELECT COUNT(*) AS c FROM user_activity WHERE user_id = ? AND created_at >= ?",
            (user_id, hour_ago),
        ).fetchone()["c"]

        if count_hour >= MAX_MESSAGES_PER_HOUR:
            return "hour"

        conn.execute(
            "INSERT INTO user_activity (user_id, created_at) VALUES (?, ?)",
            (user_id, current),
        )

        # Cleanup old activity
        conn.execute("DELETE FROM user_activity WHERE created_at < ?", (hour_ago,))
        conn.commit()

    return "ok"

# =========================
# Keyboards
# =========================

def language_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(LANGS["ar"], callback_data="lang:ar")],
        [InlineKeyboardButton(LANGS["de"], callback_data="lang:de")],
        [InlineKeyboardButton(LANGS["tr"], callback_data="lang:tr")],
        [InlineKeyboardButton(LANGS["uk"], callback_data="lang:uk")],
        [InlineKeyboardButton(LANGS["ur"], callback_data="lang:ur")],
    ]
    return InlineKeyboardMarkup(rows)


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    rows = [
        [InlineKeyboardButton(t["intensive"], callback_data="menu:intensive")],
        [InlineKeyboardButton(t["schedule"], callback_data="menu:schedule")],
        [InlineKeyboardButton(t["b1"], callback_data="menu:b1")],
        [InlineKeyboardButton(t["b1_price"], callback_data="menu:b1_price")],
        [InlineKeyboardButton(t["b2"], callback_data="menu:b2")],
        [InlineKeyboardButton(t["b2_price"], callback_data="menu:b2_price")],
        [InlineKeyboardButton(t["payment"], callback_data="menu:payment")],
        [InlineKeyboardButton(t["contact"], callback_data="menu:contact")],
        [InlineKeyboardButton(t["change_lang"], callback_data="change_lang")],
    ]
    return InlineKeyboardMarkup(rows)


def back_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["back"], callback_data="back:main")],
        [InlineKeyboardButton(t["change_lang"], callback_data="change_lang")],
    ])


def contact_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["contact"], url=ADMIN_LINK)],
        [InlineKeyboardButton(t["back"], callback_data="back:main")],
    ])

# =========================
# Helpers
# =========================

def user_display(update: Update) -> str:
    user = update.effective_user
    if not user:
        return "Unknown user"
    parts = [f"ID: {user.id}"]
    if user.username:
        parts.append(f"@{user.username}")
    if user.first_name or user.last_name:
        parts.append(f"Name: {(user.first_name or '')} {(user.last_name or '')}".strip())
    return " | ".join(parts)


async def notify_admin(context: ContextTypes.DEFAULT_TYPE, update: Update, request_id: int, request_type: str, message: str, lang: str) -> None:
    if not ADMIN_CHAT_ID:
        return

    text = (
        "📩 طلب جديد من البوت\n\n"
        f"رقم الطلب: {request_id}\n"
        f"نوع الطلب: {request_type}\n"
        f"اللغة: {LANGS.get(lang, lang)}\n"
        f"الطالب: {user_display(update)}\n\n"
        f"الرسالة:\n{message}"
    )

    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception as exc:
        logger.exception("Could not notify admin: %s", exc)


async def show_main(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str, edit: bool = False) -> None:
    t = TEXTS[lang]
    text = f"{t['main']}\n\n{t['privacy']}"
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=main_menu_keyboard(lang),
        )
    else:
        await update.effective_message.reply_text(
            text=text,
            reply_markup=main_menu_keyboard(lang),
        )

# =========================
# Handlers
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    upsert_user(update)
    context.user_data.clear()

    welcome = (
        "أهلاً وسهلاً بك في أكاديمية الكنغ التعليمية، اختر اللغة:\n"
        "Willkommen an der King's Educational Academy, wählen Sie Ihre Sprache:\n"
        "King Eğitim Akademisi'ne hoş geldiniz, lütfen dil seçin:\n"
        "Ласкаво просимо, виберіть мову:\n"
        "خوش آمدید، براہ کرم زبان منتخب کریں:"
    )

    await update.message.reply_text(welcome, reply_markup=language_keyboard())


async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    upsert_user(update)
    chat = update.effective_chat
    await update.message.reply_text(
        f"Chat ID:\n{chat.id}\n\nضع هذا الرقم في ADMIN_CHAT_ID داخل الكود."
    )


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    upsert_user(update)
    if ADMIN_CHAT_ID and update.effective_chat.id != ADMIN_CHAT_ID:
        await update.message.reply_text("هذا الأمر مخصص لمجموعة الإدارة.")
        return

    s = stats()
    await update.message.reply_text(
        f"📊 إحصائيات البوت\n\nعدد الطلاب/المستخدمين: {s['users']}\nعدد الطلبات المحفوظة: {s['requests']}"
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    upsert_user(update)
    data = query.data or ""
    user_id = update.effective_user.id

    if data.startswith("lang:"):
        lang = data.split(":", 1)[1]
        if lang not in TEXTS:
            lang = "ar"
        upsert_user(update, language=lang)
        context.user_data.clear()
        await show_main(update, context, lang, edit=True)
        return

    if data == "change_lang":
        context.user_data.clear()
        await query.edit_message_text(TEXTS["ar"]["welcome"], reply_markup=language_keyboard())
        return

    lang = get_user_lang(user_id)
    t = TEXTS[lang]

    if data == "back:main":
        context.user_data.clear()
        await show_main(update, context, lang, edit=True)
        return

    if data.startswith("menu:"):
        item = data.split(":", 1)[1]
        context.user_data.clear()

        if item == "intensive":
            await query.edit_message_text(t["intensive_text"], reply_markup=back_keyboard(lang))
            return

        if item == "schedule":
            await query.edit_message_text(t["schedule_text"], reply_markup=back_keyboard(lang))
            return

        if item == "b1":
            context.user_data["awaiting"] = "B1 (DTZ)"
            await query.edit_message_text(t["b1_text"], reply_markup=back_keyboard(lang))
            return

        if item == "b1_price":
            await query.edit_message_text(t["b1_price_text"], reply_markup=back_keyboard(lang))
            return

        if item == "b2":
            context.user_data["awaiting"] = "B2 (DTB)"
            await query.edit_message_text(t["b2_text"], reply_markup=back_keyboard(lang))
            return

        if item == "b2_price":
            await query.edit_message_text(t["b2_price_text"], reply_markup=back_keyboard(lang))
            return

        if item == "payment":
            await query.edit_message_text(t["payment_text"], reply_markup=back_keyboard(lang))
            return

        if item == "contact":
            context.user_data["awaiting"] = "تواصل مع الإدارة"
            await query.edit_message_text(
                t["contact_text"] + "\n\n" + t["send_contact"],
                reply_markup=contact_keyboard(lang),
            )
            return

    await query.edit_message_text(t["unknown"], reply_markup=main_menu_keyboard(lang))


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    upsert_user(update)

    user = update.effective_user
    if not user or not update.message:
        return

    lang = get_user_lang(user.id)
    t = TEXTS[lang]

    status = check_rate_limit(user.id)
    if status == "wait":
        await update.message.reply_text(t["spam_wait"])
        return
    if status == "hour":
        await update.message.reply_text(t["spam_hour"])
        return

    message = update.message.text.strip()
    awaiting = context.user_data.get("awaiting")

    if awaiting:
        request_id = save_request(update, awaiting, message, lang)
        await notify_admin(context, update, request_id, awaiting, message, lang)
        context.user_data.clear()
        await update.message.reply_text(t["request_saved"], reply_markup=main_menu_keyboard(lang))
        return

    # Save general messages too, but do not always forward them unless you want that behavior.
    request_id = save_request(update, "رسالة عامة", message, lang)
    await notify_admin(context, update, request_id, "رسالة عامة", message, lang)
    await update.message.reply_text(t["unknown"], reply_markup=main_menu_keyboard(lang))


async def on_document_or_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    upsert_user(update)

    user = update.effective_user
    if not user:
        return

    lang = get_user_lang(user.id)
    t = TEXTS[lang]
    awaiting = context.user_data.get("awaiting") or "مرفق من الطالب"

    status = check_rate_limit(user.id)
    if status == "wait":
        await update.effective_message.reply_text(t["spam_wait"])
        return
    if status == "hour":
        await update.effective_message.reply_text(t["spam_hour"])
        return

    caption = update.effective_message.caption or "مرفق بدون شرح"
    request_id = save_request(update, awaiting, f"[مرفق] {caption}", lang)

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    "📎 مرفق جديد من البوت\n\n"
                    f"رقم الطلب: {request_id}\n"
                    f"نوع الطلب: {awaiting}\n"
                    f"اللغة: {LANGS.get(lang, lang)}\n"
                    f"الطالب: {user_display(update)}\n\n"
                    f"الشرح:\n{caption}"
                ),
            )

            # Forward the actual attachment/message
            await update.effective_message.forward(chat_id=ADMIN_CHAT_ID)
        except Exception as exc:
            logger.exception("Could not forward attachment to admin: %s", exc)

    context.user_data.clear()
    await update.effective_message.reply_text(t["request_saved"], reply_markup=main_menu_keyboard(lang))


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("ضع متغير BOT_TOKEN داخل Railway > Variables أولاً.")

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getid", getid))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, on_document_or_photo))

    logger.info("%s is running...", BOT_NAME)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
