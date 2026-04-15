from typing import Dict, List, Tuple

class Cards:
    """手牌表示，用数组统计每种牌的数量"""

    N = 16
    c2v: Dict[str, int] = {
        '3': 0, '4': 1, '5': 2, '6': 3, '7': 4, '8': 5, '9': 6,
        '0': 7,
        'J': 8, 'j': 8, 'Q': 9, 'q': 9, 'K': 10, 'k': 10,
        'A': 11, 'a': 11,
        't': 12,
        '2': 13,
        'X': 14, 'x': 14,
        'D': 15, 'd': 15
    }
    v2s: Dict[int, str] = {
        0: "3", 1: "4", 2: "5", 3: "6", 4: "7", 5: "8", 6: "9", 7: "10",
        8: "J", 9: "Q", 10: "K", 11: "A", 13: "2", 14: "小王", 15: "大王"
    }

    def __init__(self, s: str = ""):
        """从字符串解析手牌，每个字符代表一张牌"""
        self.cardCount: List[int] = [0] * Cards.N
        if s:
            for c in s:
                if c in Cards.c2v:
                    self.cardCount[Cards.c2v[c]] += 1

    def is_include(self, b: 'Cards') -> bool:
        """判断当前手牌是否包含b中的所有牌"""
        for i in range(Cards.N):
            if b.cardCount[i] > self.cardCount[i]:
                return False
        return True

    def remove(self, b: 'Cards') -> bool:
        """从当前手牌中移除b，若b不被包含则不移除并返回False"""
        if not self.is_include(b):
            return False
        for i in range(Cards.N):
            self.cardCount[i] -= b.cardCount[i]
        return True

    def __sub__(self, b: 'Cards') -> 'Cards':
        """返回当前手牌减去b后的新Cards，不修改自身"""
        res = Cards()
        for i in range(Cards.N):
            res.cardCount[i] = self.cardCount[i] - b.cardCount[i]
            if res.cardCount[i] < 0:
                raise ValueError("Cannot remove cards that are not included")
        return res

    def card_num(self) -> int:
        """返回手牌总数"""
        return sum(self.cardCount)

    def __eq__(self, other) -> bool:
        return self.cardCount == other.cardCount

    def __add__(self, b: 'Cards') -> 'Cards':
        """返回两副牌合并后的新Cards"""
        res = Cards()
        for i in range(Cards.N):
            res.cardCount[i] = self.cardCount[i] + b.cardCount[i]
        return res

    def __hash__(self) -> int:
        return hash(tuple(self.cardCount))

    def __str__(self) -> str:
        result = ""
        for i in range(Cards.N):
            if self.cardCount[i] > 0:
                for _ in range(self.cardCount[i]):
                    result += f"{Cards.v2s.get(i, str(i))} "
        return result if result else "空"

    def __repr__(self) -> str:
        return self.__str__()
