"""Content Safety Service - защита от нежелательного контента"""
import re
import logging
from typing import List, Dict, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Уровни безопасности"""
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


class ContentSafetyService:
    """Сервис для проверки безопасности контента"""
    
    def __init__(self):
        self._init_blocked_patterns()
        self._init_warning_patterns()
        self._init_age_inappropriate_content()
    
    def _init_blocked_patterns(self):
        """Инициализация заблокированных паттернов"""
        self.blocked_patterns = {
            # Сексуальный контент
            'sexual': [
                r'\b(секс|интим|голый|обнаженн|эротик|порно|проститут|изнасилован|изнасилован)\w*\b',
                r'\b(соблазн|соблазнён|соблазнённ|соблазнённн)\w*\b',
                r'\b(любовн|романс|поцелуй|целовать|обнимать)\w*\b',  # Для детей младше 8 лет
            ],
            
            # Насилие и жестокость
            'violence': [
                r'\b(убийств|убийц|убить|умертв|зарезать|застрелить|отравить)\w*\b',
                r'\b(кровь|кровав|кровавь|кровавьи)\w*\b',
                r'\b(пытк|мучен|избиен|избивать|избить)\w*\b',
                r'\b(войн|сражен|битв|драк|драться|драть)\w*\b',
                r'\b(оружие|пистолет|ружьё|нож|меч|топор)\w*\b',
                r'\b(смерть|умирать|умер|погиб|погибать)\w*\b',
            ],
            
            # Наркотики и алкоголь
            'substances': [
                r'\b(наркотик|наркоман|алкоголь|пьян|пьяница|курить|сигарет)\w*\b',
                r'\b(табак|табачн|спиртн|водк|пиво|вино)\w*\b',
                r'\b(инъекц|укол|шприц|иголка)\w*\b',
            ],
            
            # Нецензурная лексика и сексуальный контент
            'profanity': [
                r'\b(блядь|сука|хуй|пизда|ебать|ебаный|ебан|говно|дерьмо)\w*\b',
                r'\b(чёрт|черт|бля|блин|проклят|проклятый)\w*\b',
                r'\b(чпокать|трахать|совокупляться|заниматься сексом)\w*\b',
                r'\b(изнасиловать|насиловать|принуждать к сексу)\w*\b',
                r'\b(секс|порно|эротик|голый|обнажен|интим|любовник|любовница)\w*\b',
            ],
            
            # Опасные действия
            'dangerous_actions': [
                r'\b(прыгать с крыши|выпрыгивать из окна|повеситься|убить себя)\w*\b',
                r'\b(отравляться|травить|травиться|отравить себя)\w*\b',
                r'\b(резать себя|порезать|кровь из вен|вены)\w*\b',
                r'\b(потрошить|убивать|мучить|истязать|пытать)\w*\b',
                r'\b(животных|животное|кошек|собак|птиц|рыб)\w*\b',
                r'\b(старушек|старушку|старух|бабушек|дедушек)\w*\b',
            ],
            
            # Проблемные персонажи
            'problematic_characters': [
                r'\b(насильник|маньяк|террорист|убийца|преступник)\w*\b',
                r'\b(садист|психопат|наркоман|алкоголик)\w*\b',
                r'\b(злодей|злодейка|дьявол|демон|сатана)\w*\b',
                r'\b(убийц|убийц|душегуб|палач)\w*\b',
            ],
            
            # Политические/религиозные конфликты
            'controversial': [
                r'\b(терроризм|террорист|бомба|взрыв|взрывать)\w*\b',
                r'\b(фашист|нацист|расист|националист)\w*\b',
                r'\b(секта|культ|религиозн конфликт)\w*\b',
            ]
        }
    
    def _init_warning_patterns(self):
        """Инициализация паттернов для предупреждений"""
        self.warning_patterns = {
            # Слегка проблематичный контент (для старших детей)
            'mild_violence': [
                r'\b(схватка|борьба|соперничество)\w*\b',
                r'\b(страшн|пугающ|ужасн|кошмар)\w*\b',
            ],
            
            # Взрослые темы (для старших детей)
            'mature_themes': [
                r'\b(развод|разводиться|расставание|бросить|брошенный)\w*\b',
                r'\b(болезнь|больной|заболевание|лечение)\w*\b',
                r'\b(деньги|богатство|бедность|бедный|богатый)\w*\b',
            ],
            
            # Социальные проблемы
            'social_issues': [
                r'\b(одиночество|грустн|депрессия|плохое настроение)\w*\b',
                r'\b(обман|лгать|ложь|враньё|нечестный)\w*\b',
            ]
        }
    
    def _init_age_inappropriate_content(self):
        """Контент, не подходящий для определенных возрастов"""
        self.age_restrictions = {
            # Для детей 2-4 года - очень строгие ограничения
            4: ['sexual', 'violence', 'dangerous_actions', 'controversial', 'substances', 'profanity'],
            # Для детей 5-6 лет - разрешаем легкие конфликты
            6: ['sexual', 'dangerous_actions', 'controversial', 'substances', 'profanity'],
            # Для детей 7-8 лет - разрешаем больше, но с осторожностью
            8: ['sexual', 'dangerous_actions', 'controversial', 'substances', 'profanity']
        }
    
    def validate_input(self, text: str, child_age: int) -> Tuple[SafetyLevel, List[str]]:
        """
        Валидация пользовательского ввода
        
        Args:
            text: Текст для проверки
            child_age: Возраст ребенка
            
        Returns:
            Tuple[SafetyLevel, List[str]]: Уровень безопасности и список нарушений
        """
        if not text or not text.strip():
            return SafetyLevel.SAFE, []
        
        text_lower = text.lower().strip()
        violations = []
        
        # Проверяем заблокированные паттерны
        for category, patterns in self.blocked_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    violations.append(f"blocked_{category}")
        
        # Проверяем возрастные ограничения
        age_key = min([age for age in self.age_restrictions.keys() if child_age <= age], default=8)
        restricted_categories = self.age_restrictions.get(age_key, [])
        
        for category, patterns in self.warning_patterns.items():
            if category in restricted_categories:
                for pattern in patterns:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        violations.append(f"age_restricted_{category}")
        
        # Определяем уровень безопасности
        if any('blocked_' in v for v in violations):
            return SafetyLevel.BLOCKED, violations
        elif any('age_restricted_' in v for v in violations):
            return SafetyLevel.WARNING, violations
        else:
            return SafetyLevel.SAFE, violations
    
    def validate_theme(self, theme: str, child_age: int) -> Tuple[SafetyLevel, str]:
        """
        Валидация темы сказки
        
        Args:
            theme: Тема сказки
            child_age: Возраст ребенка
            
        Returns:
            Tuple[SafetyLevel, str]: Уровень безопасности и сообщение
        """
        safety_level, violations = self.validate_input(theme, child_age)
        
        if safety_level == SafetyLevel.BLOCKED:
            return safety_level, "❌ Эта тема содержит неподходящий для детей контент"
        elif safety_level == SafetyLevel.WARNING:
            return safety_level, "⚠️ Эта тема может быть слишком сложной для данного возраста"
        else:
            return safety_level, "✅ Тема подходит для детей"
    
    def validate_characters(self, characters: List[str], child_age: int) -> Tuple[SafetyLevel, List[str]]:
        """
        Валидация персонажей
        
        Args:
            characters: Список персонажей
            child_age: Возраст ребенка
            
        Returns:
            Tuple[SafetyLevel, List[str]]: Уровень безопасности и список проблемных персонажей
        """
        problematic_chars = []
        
        # Список разрешенных персонажей (исключения)
        allowed_characters = {
            'дракон', 'дракоша', 'драконы', 'добрый дракон', 'волшебный дракон',
            'монстр', 'монстрик', 'дружелюбный монстр', 'добрый монстр',
            'злодей', 'злой', 'плохой', 'злая ведьма', 'злая волшебница'
        }
        
        # Список запрещенных персонажей (строго)
        forbidden_characters = {
            'насильник', 'насильница', 'маньяк', 'маньячка', 'террорист', 'террористка',
            'убийца', 'убийца', 'преступник', 'преступница', 'садист', 'садистка',
            'психопат', 'психопатка', 'наркоман', 'наркоманка', 'алкоголик', 'алкоголичка',
            'дьявол', 'демон', 'сатана', 'душегуб', 'палач',
            # Добавляем обходные варианты
            'алкаш', 'алкашка', 'наркоша', 'наркошка', 'саддюга', 'саддюжка',
            'пьяница', 'пьяничка', 'торчок', 'торчиха', 'доза', 'дозер',
            'зверь', 'зверюга', 'монстр', 'монстриха', 'чудовище', 'чудовище'
        }
        
        for character in characters:
            character_lower = character.lower().strip()
            
            # Сначала проверяем запрещенные персонажи (строго)
            if character_lower in forbidden_characters:
                problematic_chars.append(character)
                continue
            
            # Затем проверяем разрешенные персонажи (исключения)
            if character_lower in allowed_characters:
                continue
            
            # Проверяем через общую валидацию
            safety_level, _ = self.validate_input(character, child_age)
            if safety_level != SafetyLevel.SAFE:
                problematic_chars.append(character)
        
        if problematic_chars:
            return SafetyLevel.BLOCKED, problematic_chars
        else:
            return SafetyLevel.SAFE, []
    
    def validate_interests(self, interests: List[str], child_age: int) -> Tuple[SafetyLevel, List[str]]:
        """
        Валидация интересов
        
        Args:
            interests: Список интересов
            child_age: Возраст ребенка
            
        Returns:
            Tuple[SafetyLevel, List[str]]: Уровень безопасности и список проблемных интересов
        """
        problematic_interests = []
        
        for interest in interests:
            safety_level, _ = self.validate_input(interest, child_age)
            if safety_level != SafetyLevel.SAFE:
                problematic_interests.append(interest)
        
        if problematic_interests:
            return SafetyLevel.BLOCKED, problematic_interests
        else:
            return SafetyLevel.SAFE, []
    
    def sanitize_text(self, text: str) -> str:
        """
        Очистка текста от потенциально проблемных элементов
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        if not text:
            return text
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Удаляем потенциально опасные символы
        text = re.sub(r'[<>{}[\]\\|`~]', '', text)
        
        # Ограничиваем длину
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        return text.strip()
    
    def get_safe_alternatives(self, blocked_content: str, child_age: int) -> List[str]:
        """
        Предложение безопасных альтернатив
        
        Args:
            blocked_content: Заблокированный контент
            child_age: Возраст ребенка
            
        Returns:
            List[str]: Список безопасных альтернатив
        """
        alternatives = {
            # Альтернативы для персонажей
            'characters': {
                'warrior': ['рыцарь', 'герой', 'защитник', 'храбрец'],
                'monster': ['дружелюбное существо', 'волшебное животное', 'добрый дракон'],
                'witch': ['волшебница', 'фея', 'магический помощник'],
                'dragon': ['добрый дракон', 'волшебный дракон', 'дракон-защитник'],
                'rapist': ['принц', 'рыцарь', 'герой', 'защитник'],
                'maniac': ['волшебник', 'маг', 'колдун', 'мудрец'],
                'terrorist': ['путешественник', 'исследователь', 'авантюрист'],
                'killer': ['охотник', 'воин', 'защитник', 'рыцарь'],
                'sadist': ['волшебник', 'мудрец', 'учитель', 'наставник'],
                'alcoholic': ['повар', 'кондитер', 'художник', 'музыкант'],
                'drug_addict': ['исследователь', 'ученый', 'изобретатель', 'творец'],
            },
            
            # Альтернативы для имен
            'names': {
                'sadist': ['Александр', 'Максим', 'Дмитрий', 'Артем'],
                'rapist': ['Андрей', 'Николай', 'Сергей', 'Владимир'],
                'maniac': ['Антон', 'Роман', 'Игорь', 'Олег'],
                'killer': ['Алексей', 'Павел', 'Михаил', 'Евгений'],
                'default': ['Анна', 'Мария', 'Елена', 'Ольга', 'Татьяна'],
            },
            
            # Альтернативы для тем
            'themes': {
                'adventure': ['приключение', 'путешествие', 'исследование'],
                'friendship': ['дружба', 'помощь', 'взаимопомощь'],
                'magic': ['волшебство', 'чудеса', 'магия добра'],
            }
        }
        
        # Простой поиск альтернатив
        content_lower = blocked_content.lower()
        suggestions = []
        
        for category, items in alternatives.items():
            for key, values in items.items():
                if key in content_lower:
                    suggestions.extend(values[:2])  # Берем 2 альтернативы
        
        return suggestions[:3]  # Максимум 3 предложения


# Глобальный экземпляр сервиса
content_safety = ContentSafetyService()
