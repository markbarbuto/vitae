import re

_GREETING = r"(hi|hello|hey|hiya|howdy|greetings|good (morning|afternoon|evening|day))"
_THANKS = r"(thanks|thank you|thx|ty|cheers|much appreciated)"
_BYE = r"(bye|goodbye|bye bye|see you|see ya|later|take care|have a (good|great|nice) (day|one|night))"
_SOCIAL = rf"({_GREETING}|{_THANKS}|{_BYE})( there| mark| so much| again)*"
_ABOUT = r"(who are you|what are you|what can you do|what can i ask( you)?|what do you know|how does this work|help)"
SMALL_TALK = re.compile(rf"({_SOCIAL} ?)+|({_SOCIAL} )*{_ABOUT}")


def is_small_talk(question: str) -> bool:
    words = re.sub(r"[^a-z' ]+", " ", question.lower())
    return SMALL_TALK.fullmatch(" ".join(words.split())) is not None
