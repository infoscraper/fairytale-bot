"""OpenAI service for story generation"""
import asyncio
import time
from typing import Optional, List, Dict
from openai import AsyncOpenAI

from ..core.config import settings
from ..models.child import Child


class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_story(
        self,
        child: Child,
        theme: Optional[str] = None,
        custom_theme: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate personalized story for child"""
        
        # Build context about the child
        context = self._build_child_context(child)
        
        # Determine the theme
        story_theme = custom_theme or theme or self._suggest_theme_from_interests(child.interests)
        
        # Build the prompt
        prompt = self._build_story_prompt(child, context, story_theme)
        
        try:
            # Start timing
            start_time = time.time()
            
            # Use Chat Completions API with proper parameters for GPT-5
            request_params = {
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": self._get_storyteller_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            }
            
            # Use correct parameters based on model
            if settings.OPENAI_MODEL.startswith('gpt-5'):
                request_params["max_completion_tokens"] = 800  # Для коротких детских сказок
                # GPT-5 uses default temperature=1.0 only
            else:
                request_params["max_tokens"] = 800  # Оптимально для 10-минутных сказок
                request_params["temperature"] = 0.8
            
            response = await self.client.chat.completions.create(**request_params)
            
            story_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Debug logging for GPT-5
            print(f"🔍 DEBUG - Model: {settings.OPENAI_MODEL}")
            print(f"🔍 DEBUG - Raw response content: {story_text[:200]}...")
            print(f"🔍 DEBUG - Content length: {len(story_text) if story_text else 0}")
            print(f"🔍 DEBUG - Tokens used: {tokens_used}")
            
            if not story_text or not story_text.strip():
                print("❌ WARNING: Empty story text received from GPT!")
                print(f"❌ Full response: {response}")
                raise Exception("GPT вернул пустой ответ")
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            return {
                "story_text": story_text,
                "theme": story_theme,
                "characters": child.favorite_characters,
                "moral": self._extract_moral_from_story(story_text),
                "tokens_used": tokens_used,
                "generation_time": round(generation_time, 2)
            }
            
        except Exception as e:
            # More detailed error handling
            if "rate_limit" in str(e).lower():
                raise Exception("⏳ Слишком много запросов. Попробуйте через минуту.")
            elif "invalid_api_key" in str(e).lower():
                raise Exception("🔑 Проблема с API ключом. Обратитесь к администратору.")
            elif "insufficient_quota" in str(e).lower():
                raise Exception("💰 Превышен лимит API. Попробуйте позже.")
            elif "timeout" in str(e).lower():
                raise Exception("⏱️ Превышено время ожидания. Попробуйте еще раз.")
            elif "connection" in str(e).lower():
                raise Exception("🌐 Проблемы с подключением к серверу. Попробуйте позже.")
            else:
                raise Exception(f"😔 Не удалось создать сказку: {str(e)[:100]}...")
    
    def _build_child_context(self, child: Child) -> str:
        """Build context about the child for personalization"""
        
        characters_text = ", ".join(child.favorite_characters) if child.favorite_characters else "любые добрые персонажи"
        interests_text = ", ".join(child.interests) if child.interests else "общие детские темы"
        
        context = f"""
        ИНФОРМАЦИЯ О РЕБЕНКЕ:
        Имя: {child.name}
        Возраст: {child.age} лет
        Любимые персонажи: {characters_text}
        Интересы: {interests_text}
        Предпочитаемая длина сказки: {child.preferred_story_length} минут чтения
        """
        
        return context.strip()
    
    def _build_story_prompt(self, child: Child, context: str, theme: str) -> str:
        """Build the story generation prompt"""
        
        age_guidance = self._get_age_appropriate_guidance(child.age)
        
        prompt = f"""
        {context}
        
        ЗАДАЧА: Создай персонализированную сказку для {child.name}
        
        ТЕМА СКАЗКИ: {theme}
        
        ТРЕБОВАНИЯ:
        1. {child.name} должен быть главным героем и активным участником событий
        2. Включи любимых персонажей ребенка органично в сюжет
        3. {age_guidance}
        4. История должна быть добрая, поучительная и позитивная. За основу можно взять популярные сказки, мультфильмы и истории адаптировав их под возраст ребенка.
        5. Длина: примерно {child.preferred_story_length} минут чтения
        6. Используй яркие, образные описания для воображения
        7. Добавь интерактивные моменты где ребенок может представить себя
        
        СТРУКТУРА:
        - Увлекательное начало
        - Интересное приключение или проблема
        - Активное участие {child.name} в решении
        - Позитивный финал с моралью
        
        Создай захватывающую историю на русском языке:
        """
        
        return prompt.strip()
    
    def _get_storyteller_system_prompt(self) -> str:
        """System prompt for the storyteller"""
        return """
        Ты - волшебный рассказчик сказок для детей. Твоя задача создавать:
        
        ✨ Захватывающие истории где ребенок - главный герой
        ✨ Добрые сказки с позитивными персонажами
        ✨ Возрастно-подходящий контент без страшных элементов
        ✨ Истории с позитивной моралью и важными жизненными уроками
        ✨ Яркие, образные описания для развития воображения
        
        СТРОГИЕ ОГРАНИЧЕНИЯ БЕЗОПАСНОСТИ:
        🚫 ЗАПРЕЩЕНО ВКЛЮЧАТЬ:
        - Любые упоминания насилия, жестокости, смерти, крови
        - Сексуальный контент или романтические отношения
        - Наркотики, алкоголь, курение
        - Нецензурную лексику или грубость
        - Страшных монстров, ужасы, кошмары
        - Оружие, драки, войны, конфликты
        - Политические или религиозные споры
        - Опасные действия (прыжки с высоты, отравления и т.д.)
        - Одиночество, депрессию, негативные эмоции
        - Обман, ложь, нечестность (кроме поучительных примеров)
        
        ✅ ОБЯЗАТЕЛЬНО ВКЛЮЧАТЬ:
        - Только добрых, дружелюбных персонажей
        - Позитивные сюжеты с решением проблем
        - Счастливые концовки
        - Поучительные морали о дружбе, доброте, честности
        - Взаимопомощь и поддержку
        - Волшебство и чудеса добра
        - Приключения без опасности
        
        ВАЖНО: Ребенок должен быть активным участником, а не наблюдателем!
        При нарушении ограничений - немедленно остановись и создай безопасную альтернативу.
        Всегда пиши на русском языке.
        """
    
    def _get_age_appropriate_guidance(self, age: int) -> str:
        """Get age-appropriate story guidance with length adaptation"""
        age_adaptations = self._get_age_adaptations(age)
        
        base_guidance = ""
        if age <= 3:
            base_guidance = "Простой сюжет, короткие предложения, основные цвета и формы, знакомые предметы"
        elif age <= 5:
            base_guidance = "Простая структура, понятные эмоции, дружба и семья, магические элементы"
        elif age <= 7:
            base_guidance = "Более сложный сюжет, проблемы и их решения, храбрость и доброта"
        else:  # 8 лет
            base_guidance = "Развернутые приключения, моральные выборы, дружба и ответственность"
        
        return f"{base_guidance}. ДЛИНА: {age_adaptations['word_count']} слов. ЯЗЫК: {age_adaptations['complexity']}"
    
    def _get_age_adaptations(self, age: int) -> Dict[str, str]:
        """Get age-appropriate adaptations for story length and complexity"""
        if age <= 3:
            return {
                'word_count': '150-200',
                'complexity': 'простые слова, короткие предложения',
                'structure': 'простая линейная история с повторами',
                'moral_style': 'очень простая и прямая мораль'
            }
        elif age <= 5:
            return {
                'word_count': '250-350',
                'complexity': 'доступные слова, средние предложения',
                'structure': 'ясная структура с завязкой, развитием и концовкой',
                'moral_style': 'понятная мораль с примерами'
            }
        elif age <= 7:
            return {
                'word_count': '400-550',
                'complexity': 'разнообразная лексика, развернутые предложения',
                'structure': 'полная структура с несколькими событиями',
                'moral_style': 'глубокая мораль с объяснением'
            }
        else:  # 8 лет
            return {
                'word_count': '600-800',
                'complexity': 'богатая лексика, сложные предложения',
                'structure': 'развитая структура с подсюжетами',
                'moral_style': 'многослойная мораль для размышления'
            }
    
    def _suggest_theme_from_interests(self, interests: List[str]) -> str:
        """Suggest theme based on child's interests"""
        if not interests:
            return "волшебное приключение"
        
        # Pick random interest as theme
        import random
        return random.choice(interests)
    
    def _extract_moral_from_story(self, story_text: str) -> str:
        """Extract moral from the story (enhanced with 40 diverse morals)"""
        import random
        
        # Расширенная коллекция моралей на основе ключевых слов в тексте
        morals = {
            "дружба": "Дружба — это одно из самых важных сокровищ в жизни",
            "друг": "Настоящий друг всегда рядом, когда трудно",
            "вместе": "Лучше вместе, чем поодиночке",
            
            "доброта": "Даже маленькие поступки доброты делают мир лучше",
            "добрый": "Добро всегда возвращается",
            "добро": "Самое ценное богатство — это добрые дела",
            "помощь": "Тот, кто помогает другим, помогает и себе",
            "помогать": "Кто заботится о других, тот никогда не останется один",
            
            "храбрость": "Настоящая смелость — не в силе, а в сердце",
            "смелость": "Смелость — это не отсутствие страха, а умение его преодолеть",
            "смелый": "Маленькие герои тоже совершают большие дела",
            "страх": "Не стоит бояться просить помощи",
            
            "честность": "Честность всегда важнее обмана",
            "правда": "Доверие строится поступками",
            "обман": "Честность всегда важнее обмана",
            
            "труд": "Труд и терпение помогают достичь мечты",
            "работа": "Мечты сбываются, если верить и стараться",
            "лень": "Лень не приводит к успеху",
            "терпение": "Терпение помогает преодолеть трудности",
            
            "дели": "Делись с другими, и счастья станет больше",
            "щедрость": "Щедрость делает тебя счастливым",
            "жадность": "Секрет счастья — в умении делиться",
            
            "природа": "Уважай природу и заботься о животных",
            "животные": "Уважай природу и заботься о животных",
            
            "особенный": "Каждый особенный по-своему, и это ценно",
            "красота": "Настоящая красота — внутри человека",
            "внешность": "Не суди других по внешности",
            
            "зависть": "Зависть разрушает дружбу",
            "злость": "Нельзя быть счастливым, обижая других",
            
            "улыбка": "Улыбка и доброе слово могут изменить день",
            "смех": "Смех и радость делают жизнь ярче",
            "радость": "Смех и радость делают жизнь ярче",
            
            "учение": "Учиться новому — это всегда полезно",
            "ошибка": "Ошибки помогают становиться умнее",
            "умный": "Ум важнее силы",
            
            "справедливость": "Справедливость важнее выгоды",
            "вежливость": "Вежливость открывает сердца людей",
            "уступать": "Иногда нужно уметь уступить",
            
            "семья": "Любовь и забота делают семью крепкой",
            "мудрость": "Важно слушать старших и мудрых",
            "беречь": "Нужно беречь то, что имеешь"
        }
        
        story_lower = story_text.lower()
        
        # Ищем совпадения с ключевыми словами
        found_morals = []
        for keyword, moral in morals.items():
            if keyword in story_lower:
                found_morals.append(moral)
        
        if found_morals:
            return random.choice(found_morals)
        
        # Fallback - случайная мораль из базового набора
        default_morals = [
            "Важно быть добрым, смелым и помогать другим",
            "Дружба — это одно из самых важных сокровищ в жизни", 
            "Даже маленькие поступки доброты делают мир лучше",
            "Настоящая смелость — не в силе, а в сердце",
            "Делись с другими, и счастья станет больше"
        ]
        
        return random.choice(default_morals)
    
    async def close(self):
        """Close the OpenAI client"""
        if self.client:
            await self.client.close()
