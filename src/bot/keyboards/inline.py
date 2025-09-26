"""Inline keyboards"""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ...models.child import Child


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard with buttons"""
    buttons = [
        [InlineKeyboardButton(
            text="📖 Создать сказку",
            callback_data="menu_create_story"
        )],
        [InlineKeyboardButton(
            text="👨‍👩‍👧‍👦 Управление профилями",
            callback_data="menu_manage_profiles"
        )],
        [InlineKeyboardButton(
            text="📚 История сказок",
            callback_data="menu_story_history"
        )],
        [InlineKeyboardButton(
            text="❓ Помощь",
            callback_data="menu_help"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_children_keyboard(children: List[Child], callback_prefix: str = "child") -> InlineKeyboardMarkup:
    """Create keyboard for child selection"""
    buttons = []
    
    for child in children:
        buttons.append([
            InlineKeyboardButton(
                text=f"👶 {child.name} ({child.age} лет)",
                callback_data=f"{callback_prefix}_{child.id}"
            )
        ])
    
    # Add button to create new child
    buttons.append([
        InlineKeyboardButton(
            text="➕ Добавить ребенка",
            callback_data="add_new_child"
        )
    ])
    
    # Add main menu button
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_story_type_keyboard(child_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for story type selection"""
    buttons = [
        [InlineKeyboardButton(
            text="🎭 Новая сказка",
            callback_data=f"new_story_{child_id}"
        )],
        [InlineKeyboardButton(
            text="⚙️ Настройки профиля",
            callback_data=f"edit_profile_{child_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_children"
        )],
        [InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_theme_keyboard(child_id: int, interests: List[str]) -> InlineKeyboardMarkup:
    """Create keyboard for theme selection based on child interests and popular themes"""
    buttons = []
    
    # Add buttons for child's interests (max 4)
    for interest in interests[:4]:
        buttons.append([
            InlineKeyboardButton(
                text=f"🎯 {interest.title()}",
                callback_data=f"theme_{child_id}_{interest}"
            )
        ])
    
    # Add popular themes
    popular_themes = [
        ("🦄 Волшебство", "волшебство"),
        ("🐾 Животные", "животные"),
        ("🌟 Приключения", "приключения"),
        ("🏰 Принцессы", "принцессы"),
        ("🚗 Машинки", "машинки"),
        ("🌈 Дружба", "дружба"),
        ("🎪 Цирк", "цирк"),
        ("🌊 Морские", "море"),
        ("🌌 Космос", "космос"),
        ("🎨 Творчество", "творчество")
    ]
    
    # Add popular themes (in pairs for compact layout)
    for i in range(0, len(popular_themes), 2):
        row = []
        for j in range(2):
            if i + j < len(popular_themes):
                emoji_text, theme = popular_themes[i + j]
                row.append(InlineKeyboardButton(
                    text=emoji_text,
                    callback_data=f"theme_{child_id}_{theme}"
                ))
        buttons.append(row)
    
    # Add special options
    buttons.extend([
        [InlineKeyboardButton(
            text="🎲 Сюрприз (случайная тема)",
            callback_data=f"theme_{child_id}_random"
        )],
        [InlineKeyboardButton(
            text="✏️ Своя тема",
            callback_data=f"custom_theme_{child_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"back_to_child_{child_id}"
        )]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_feedback_keyboard(story_id: int, child_id: int) -> InlineKeyboardMarkup:
    """Create feedback keyboard for story rating"""
    buttons = [
        [
            InlineKeyboardButton(text="❤️", callback_data=f"feedback_{story_id}_loved"),
            InlineKeyboardButton(text="👍", callback_data=f"feedback_{story_id}_liked"),
            InlineKeyboardButton(text="😐", callback_data=f"feedback_{story_id}_neutral"),
            InlineKeyboardButton(text="👎", callback_data=f"feedback_{story_id}_disliked")
        ],
        [InlineKeyboardButton(
            text="🔄 Еще сказку!",
            callback_data=f"new_story_{child_id}"
        )],
        [InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirm_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Create confirmation keyboard"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_profile_management_keyboard(children: List[Child]) -> InlineKeyboardMarkup:
    """Create keyboard for profile management"""
    buttons = []
    
    for child in children:
        story_count = len(child.stories) if hasattr(child, 'stories') and child.stories else 0
        buttons.append([
            InlineKeyboardButton(
                text=f"👶 {child.name} ({child.age} лет) - {story_count} сказок",
                callback_data=f"manage_profile_{child.id}"
            )
        ])
    
    # Add button to create new child
    buttons.append([
        InlineKeyboardButton(
            text="➕ Добавить ребенка",
            callback_data="add_new_child"
        )
    ])
    
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_profile_actions_keyboard(child_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for individual profile actions"""
    buttons = [
        [InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=f"profile_stats_{child_id}"
        )],
        [InlineKeyboardButton(
            text="✏️ Редактировать профиль", 
            callback_data=f"edit_profile_{child_id}"
        )],
        [InlineKeyboardButton(
            text="🎭 Создать сказку",
            callback_data=f"new_story_{child_id}"
        )],
        [InlineKeyboardButton(
            text="📚 История сказок",
            callback_data=f"story_history_{child_id}"
        )],
        [InlineKeyboardButton(
            text="⚠️ Деактивировать профиль",
            callback_data=f"deactivate_profile_{child_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад к профилям",
            callback_data="back_to_profiles"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_edit_profile_keyboard(child_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for profile editing options"""
    buttons = [
        [InlineKeyboardButton(
            text="📝 Изменить имя",
            callback_data=f"edit_name_{child_id}"
        )],
        [InlineKeyboardButton(
            text="🎂 Изменить возраст",
            callback_data=f"edit_age_{child_id}"
        )],
        [InlineKeyboardButton(
            text="🎭 Изменить персонажей",
            callback_data=f"edit_characters_{child_id}"
        )],
        [InlineKeyboardButton(
            text="💫 Изменить интересы",
            callback_data=f"edit_interests_{child_id}"
        )],
        [InlineKeyboardButton(
            text="⏱️ Изменить длину сказок",
            callback_data=f"edit_length_{child_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"manage_profile_{child_id}"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_history_keyboard(has_multiple_children: bool = False) -> InlineKeyboardMarkup:
    """Create keyboard for story history navigation"""
    buttons = [
        [InlineKeyboardButton(
            text="📖 Все сказки",
            callback_data="view_all_stories"
        )]
    ]
    
    if has_multiple_children:
        buttons.append([InlineKeyboardButton(
            text="👶 Фильтр по детям",
            callback_data="filter_by_child"
        )])
    
    buttons.extend([
        [InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="story_statistics"
        )],
        [InlineKeyboardButton(
            text="🔙 Главное меню",
            callback_data="main_menu"
        )]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_children_filter_keyboard(children: List) -> InlineKeyboardMarkup:
    """Create keyboard for filtering stories by children"""
    buttons = []
    
    for child in children:
        buttons.append([InlineKeyboardButton(
            text=f"👶 {child.name} ({child.age} лет)",
            callback_data=f"child_stories_{child.id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад к истории",
        callback_data="back_to_history"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_story_actions_keyboard(story_id: int, child_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for story actions (export, create similar, etc.)"""
    buttons = [
        [InlineKeyboardButton(
            text="📥 Экспорт в файл",
            callback_data=f"export_story_{story_id}"
        )],
        [InlineKeyboardButton(
            text="🔄 Похожая сказка",
            callback_data=f"similar_story_{child_id}_{story_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 К истории",
            callback_data="back_to_history"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_series_keyboard(child_series: List, child_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for series management"""
    buttons = []
    
    # Add existing series
    for series in child_series:
        status_emoji = "📖" if series.is_active else "✅" if series.is_completed else "⏸️"
        episodes_text = f"({series.total_episodes} эп.)" if series.total_episodes > 0 else "(новая)"
        
        buttons.append([InlineKeyboardButton(
            text=f"{status_emoji} {series.series_name} {episodes_text}",
            callback_data=f"series_{series.id}"
        )])
    
    # Add create new series button
    buttons.append([InlineKeyboardButton(
        text="✨ Создать новую серию",
        callback_data=f"create_series_{child_id}"
    )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад к выбору детей",
        callback_data="back_to_children"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_series_actions_keyboard(series_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for series actions"""
    buttons = [
        [InlineKeyboardButton(
            text="▶️ Новый эпизод",
            callback_data=f"new_episode_{series_id}"
        )],
        [InlineKeyboardButton(
            text="📚 Все эпизоды",
            callback_data=f"series_episodes_{series_id}"
        )],
        [InlineKeyboardButton(
            text="✏️ Эпизод с темой",
            callback_data=f"custom_episode_{series_id}"
        )],
        [InlineKeyboardButton(
            text="✅ Завершить серию",
            callback_data=f"complete_series_{series_id}"
        ), InlineKeyboardButton(
            text="⏸️ Приостановить",
            callback_data=f"pause_series_{series_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 К сериям",
            callback_data="back_to_series"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_series_episodes_keyboard(episodes: List, series_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for series episodes"""
    buttons = []
    
    for episode in episodes:
        feedback_emoji = "💖" if episode.child_feedback == "loved" else "👍" if episode.child_feedback == "liked" else "📖"
        
        buttons.append([InlineKeyboardButton(
            text=f"{feedback_emoji} Эпизод {episode.episode_number}: {episode.theme}",
            callback_data=f"read_story_{episode.id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 К серии",
        callback_data=f"series_{series_id}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
