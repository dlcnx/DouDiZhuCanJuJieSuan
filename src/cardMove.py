from enum import IntEnum
from typing import List
from cards import Cards

class MoveType(IntEnum):
    """出牌类型枚举"""
    PASS = 0
    SINGLE = 1
    PAIR = 2
    TRIPLE = 3
    BOMB = 4
    KING_BOMB = 5
    THREE_ONE = 6
    THREE_TWO = 7
    SERIAL_SINGLE = 8
    SERIAL_PAIR = 9
    SERIAL_TRIPLE = 10
    SERIAL_THREE_ONE = 11
    SERIAL_THREE_TWO = 12
    FOUR_TWO = 13
    FOUR_TWO_TWO = 14
    INVALID = 15

MOVE_TYPES_STR = {
    MoveType.INVALID: "无效",
    MoveType.PASS: "过",
    MoveType.SINGLE: "单张",
    MoveType.PAIR: "对子",
    MoveType.TRIPLE: "三张",
    MoveType.BOMB: "炸弹",
    MoveType.KING_BOMB: "王炸",
    MoveType.THREE_ONE: "三带一",
    MoveType.THREE_TWO: "三带二",
    MoveType.SERIAL_SINGLE: "顺子",
    MoveType.SERIAL_PAIR: "连对",
    MoveType.SERIAL_TRIPLE: "飞机",
    MoveType.SERIAL_THREE_ONE: "三带一组成的飞机",
    MoveType.SERIAL_THREE_TWO: "三带二组成的飞机",
    MoveType.FOUR_TWO: "四带二",
    MoveType.FOUR_TWO_TWO: "四带两对"
}

class moveCompareResult(IntEnum):
    """出牌比较结果"""
    INVALID = -1
    EQUAL = 0
    LESS = 1
    GREATER = 2

class CardMove:
    """出牌动作，将主牌和附牌压缩存储在同一个数组中

    attach_main数组的每个元素：低4位存主牌数量，高4位存附牌数量
    moveTypeOffset位置存出牌类型
    """

    moveTypeOffset = 12

    def __init__(self, main=None, attach=None, t=None):
        """构造出牌动作

        三种用法：
        1. CardMove(MoveType.PASS/INVALID) - 创建PASS或INVALID动作
        2. CardMove(main_cards, None, MoveType) - 创建仅含主牌的动作（单张、对子、顺子等）
        3. CardMove(main_cards, attach_cards, MoveType) - 创建含主牌和附牌的动作（三带一、四带二等）
        """
        self.attach_main: List[int] = [0] * Cards.N
        if isinstance(main, MoveType):
            t = main
            main = None
        if main is None and attach is None and t is None:
            self.attach_main[CardMove.moveTypeOffset] = MoveType.PASS
        elif t is not None and main is None and attach is None:
            if t != MoveType.PASS and t != MoveType.INVALID:
                raise ValueError("Cannot create a cardMove which is not PASS type without cards")
            self.attach_main[CardMove.moveTypeOffset] = t
        elif attach is None:
            for i in range(Cards.N):
                self.attach_main[i] = main.cardCount[i] & 0x0F
            self.attach_main[CardMove.moveTypeOffset] = t
        else:
            for i in range(Cards.N):
                self.attach_main[i] = (main.cardCount[i] & 0x0F) | ((attach.cardCount[i] & 0x0F) << 4)
            self.attach_main[CardMove.moveTypeOffset] = t

    def get_type(self) -> MoveType:
        """获取出牌类型"""
        return MoveType(self.attach_main[CardMove.moveTypeOffset])

    def get_main_cards(self) -> Cards:
        """获取主牌部分（如三带一中的三张）"""
        main = Cards()
        for i in range(Cards.N):
            main.cardCount[i] = self.attach_main[i] & 0x0F
        main.cardCount[CardMove.moveTypeOffset] = 0
        return main

    def get_attach_cards(self) -> Cards:
        """获取附牌部分（如三带一中的一张）"""
        attach = Cards()
        for i in range(Cards.N):
            attach.cardCount[i] = (self.attach_main[i] >> 4) & 0x0F
        return attach

    def get_main_card_max_val(self) -> int:
        """获取主牌中最大的牌面值"""
        for i in range(Cards.N - 1, -1, -1):
            if (self.attach_main[i] & 0x0F) > 0 and i != CardMove.moveTypeOffset:
                return i
        return -1

    def get_all_cards(self) -> Cards:
        """获取该动作涉及的所有牌（主牌+附牌）"""
        all_cards = Cards()
        for i in range(Cards.N):
            all_cards.cardCount[i] = (self.attach_main[i] & 0x0F) | ((self.attach_main[i] & 0xF0) >> 4)
        all_cards.cardCount[CardMove.moveTypeOffset] = 0
        return all_cards

    def get_all_card_num(self) -> int:
        """获取该动作涉及的总牌数"""
        count = 0
        for i in range(Cards.N):
            count += (self.attach_main[i] & 0x0F) + ((self.attach_main[i] & 0xF0) >> 4)
        return count - self.attach_main[CardMove.moveTypeOffset]

    def compare(self, b: 'CardMove') -> moveCompareResult:
        """比较两个出牌动作的大小，用于判断是否能压过对方

        王炸最大，炸弹次之，同类型按主牌面值比较，不同类型不可比较
        """
        if self.get_type() == MoveType.PASS and b.get_type() == MoveType.PASS:
            return moveCompareResult.EQUAL
        if self.get_type() == MoveType.PASS or self.get_type() == MoveType.INVALID:
            return moveCompareResult.LESS
        if b.get_type() == MoveType.PASS or b.get_type() == MoveType.INVALID:
            return moveCompareResult.GREATER

        if self.get_type() != b.get_type():
            if self.get_type() == MoveType.KING_BOMB:
                return moveCompareResult.GREATER
            if b.get_type() == MoveType.KING_BOMB:
                return moveCompareResult.LESS
            if self.get_type() == MoveType.BOMB:
                return moveCompareResult.GREATER
            if b.get_type() == MoveType.BOMB:
                return moveCompareResult.LESS
            return moveCompareResult.INVALID

        t = self.get_type()
        if t in (MoveType.SINGLE, MoveType.PAIR, MoveType.TRIPLE, MoveType.BOMB,
                 MoveType.THREE_ONE, MoveType.THREE_TWO, MoveType.FOUR_TWO, MoveType.FOUR_TWO_TWO):
            if self.get_main_card_max_val() > b.get_main_card_max_val():
                return moveCompareResult.GREATER
            elif self.get_main_card_max_val() < b.get_main_card_max_val():
                return moveCompareResult.LESS
            else:
                return moveCompareResult.EQUAL

        if t in (MoveType.SERIAL_SINGLE, MoveType.SERIAL_PAIR, MoveType.SERIAL_TRIPLE,
                 MoveType.SERIAL_THREE_ONE, MoveType.SERIAL_THREE_TWO):
            if self.get_all_card_num() != b.get_all_card_num():
                return moveCompareResult.INVALID
            if self.get_main_card_max_val() > b.get_main_card_max_val():
                return moveCompareResult.GREATER
            elif self.get_main_card_max_val() < b.get_main_card_max_val():
                return moveCompareResult.LESS
            else:
                return moveCompareResult.EQUAL

        raise ValueError("Should not reach here, invalid move type")

    def __eq__(self, other) -> bool:
        return self.attach_main == other.attach_main

    def __hash__(self) -> int:
        return hash(tuple(self.attach_main))

    def __str__(self) -> str:
        main = self.get_main_cards()
        attach = self.get_attach_cards()
        main_str = str(main) if main.card_num() > 0 else ""
        attach_str = str(attach) if attach.card_num() > 0 else ""
        result = MOVE_TYPES_STR.get(self.get_type(), '未知')
        if main_str:
            result += " " + main_str
        if attach_str:
            result += " " + attach_str
        return result.strip()

    def __repr__(self) -> str:
        return self.__str__()
