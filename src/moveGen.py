from typing import List, Callable
from cards import Cards
from cardMove import CardMove, MoveType

def gen_1234(hand: Cards, num: int) -> List[Cards]:
    """生成指定数量的同点数牌组（单张/对子/三张/炸弹）"""
    result = []
    for i in range(Cards.N):
        if hand.cardCount[i] >= num:
            c = Cards()
            c.cardCount[i] = num
            result.append(c)
    return result

def make_new_serial(from_val: int, to: int, num: int) -> Cards:
    """构造从from_val到to的连续牌组，每种num张"""
    if from_val < 0 or to >= Cards.N or from_val > to or num < 1 or num > 4:
        raise ValueError("Invalid range or num")
    res = Cards()
    for i in range(from_val, to + 1):
        res.cardCount[i] = num
    return res

def gen_serial(hand: Cards, num: int, minlen: int) -> List[Cards]:
    """生成连续牌组（顺子/连对/飞机），num为每种牌的数量，minlen为最短连续长度"""
    result = []
    if num < 1 or num > 4:
        raise ValueError("num must be between 1 and 4")
    last_pos = -1
    for i in range(Cards.N):
        if hand.cardCount[i] < num:
            last_pos = -1
            continue
        elif last_pos < 0:
            last_pos = i
        if i - last_pos + 1 >= minlen:
            for j in range(last_pos, i - minlen + 2):
                result.append(make_new_serial(j, i, num))
    return result

def gen_single(hand: Cards) -> List[Cards]:
    """生成所有单张出法"""
    return gen_1234(hand, 1)

def gen_pair(hand: Cards) -> List[Cards]:
    """生成所有对子出法"""
    return gen_1234(hand, 2)

def gen_triple(hand: Cards) -> List[Cards]:
    """生成所有三张出法"""
    return gen_1234(hand, 3)

def gen_bomb(hand: Cards) -> List[Cards]:
    """生成所有炸弹出法"""
    return gen_1234(hand, 4)

def gen_king_bomb(hand: Cards) -> List[Cards]:
    """生成王炸出法（需要同时持有大小王）"""
    result = []
    small_king_val = Cards.c2v['x']
    big_king_val = Cards.c2v['d']
    if hand.cardCount[small_king_val] > 0 and hand.cardCount[big_king_val] > 0:
        c = Cards()
        c.cardCount[small_king_val] = 1
        c.cardCount[big_king_val] = 1
        result.append(c)
    return result

def gen_serial_single(hand: Cards) -> List[Cards]:
    """生成所有顺子出法（至少5张连续单牌）"""
    return gen_serial(hand, 1, 5)

def gen_serial_pair(hand: Cards) -> List[Cards]:
    """生成所有连对出法（至少3对连续对子）"""
    return gen_serial(hand, 2, 3)

def gen_serial_triple(hand: Cards) -> List[Cards]:
    """生成所有飞机出法（至少2个连续三张）"""
    return gen_serial(hand, 3, 2)

def gen_a_with_b(hand: Cards, type_val: MoveType) -> List[CardMove]:
    """生成带牌出法（三带一/三带二/四带二/四带两对）

    A为主牌（三张或四张），B为附牌（带的牌）
    """
    a_num = 3 if type_val in (MoveType.THREE_ONE, MoveType.THREE_TWO) else 4
    b_num = 1 if type_val in (MoveType.THREE_ONE, MoveType.FOUR_TWO) else 2
    g_num = 2 if type_val in (MoveType.FOUR_TWO, MoveType.FOUR_TWO_TWO) else 1

    moves = []
    a_cards = gen_1234(hand, a_num)
    for a in a_cards:
        remaining_card = hand - a
        b_cards = gen_1234(remaining_card, b_num)
        if g_num == 1:
            for b in b_cards:
                moves.append(CardMove(a, b, type_val))
        elif g_num == 2:
            for b1 in b_cards:
                for b2 in b_cards:
                    if b1 != b2:
                        moves.append(CardMove(a, b1 + b2, type_val))
            bcards_same = gen_1234(remaining_card, b_num * g_num)
            for b in bcards_same:
                moves.append(CardMove(a, b, type_val))
        else:
            raise ValueError("Invalid group number for AwithB move generation")
    return moves

def gen_three_one(hand: Cards) -> List[CardMove]:
    """生成所有三带一出法"""
    return gen_a_with_b(hand, MoveType.THREE_ONE)

def gen_three_two(hand: Cards) -> List[CardMove]:
    """生成所有三带二出法"""
    return gen_a_with_b(hand, MoveType.THREE_TWO)

def gen_four_two(hand: Cards) -> List[CardMove]:
    """生成所有四带二出法"""
    return gen_a_with_b(hand, MoveType.FOUR_TWO)

def gen_four_two_two(hand: Cards) -> List[CardMove]:
    """生成所有四带两对出法"""
    return gen_a_with_b(hand, MoveType.FOUR_TWO_TWO)

def select_n_from_remaining(remaining: Cards, n: int) -> List[Cards]:
    """从剩余牌中选择n种不同点数的牌，返回所有可能组合"""
    result = []
    if n < 1:
        raise ValueError("Invalid number of cards to select")
    if n == 0:
        result.append(Cards())
        return result
    if n > remaining.card_num():
        return result

    def func(current: Cards, rem: Cards, start: int, count: int):
        if count == n:
            result.append(current)
            return
        for i in range(start, Cards.N):
            if rem.cardCount[i] > 0:
                next_card = Cards()
                next_card.cardCount = current.cardCount[:]
                next_card.cardCount[i] += 1
                new_remain = Cards()
                new_remain.cardCount = rem.cardCount[:]
                new_remain.cardCount[i] -= 1
                func(next_card, new_remain, i, count + 1)

    func(Cards(), remaining, 0, 0)
    return result

def gen_serial_three_x(hand: Cards, b_num: int) -> List[CardMove]:
    """生成飞机带牌出法（飞机带单/飞机带对）"""
    res = []
    serial_triple = gen_serial_triple(hand)
    for triple in serial_triple:
        remaining_card = hand - triple
        g_num = triple.card_num() // 3
        if remaining_card.card_num() < g_num * b_num:
            continue

        temp_remaining = Cards()
        for i in range(Cards.N):
            temp_remaining.cardCount[i] = remaining_card.cardCount[i] // b_num

        attach_cards_list = select_n_from_remaining(temp_remaining, g_num)
        for attach_cards in attach_cards_list:
            for i in range(Cards.N):
                attach_cards.cardCount[i] *= b_num
            move_type = MoveType.SERIAL_THREE_ONE if b_num == 1 else MoveType.SERIAL_THREE_TWO
            res.append(CardMove(triple, attach_cards, move_type))
    return res

def gen_serial_three_one(hand: Cards) -> List[CardMove]:
    """生成所有飞机带单出法"""
    return gen_serial_three_x(hand, 1)

def gen_serial_three_two(hand: Cards) -> List[CardMove]:
    """生成所有飞机带对出法"""
    return gen_serial_three_x(hand, 2)

def make_card_move_from_cards(v_cards: List[Cards], type_val: MoveType) -> List[CardMove]:
    """将Cards列表转换为指定类型的CardMove列表"""
    moves = []
    for hand in v_cards:
        moves.append(CardMove(hand, Cards(), type_val))
    return moves

def gen_all_moves(hand: Cards, last_move: CardMove) -> List[CardMove]:
    """根据当前手牌和上一手牌，生成所有合法出牌

    若上一手为INVALID或PASS，则可以出任意类型；
    否则只能出同类型且更大的牌，或炸弹/王炸压过
    """
    result = []

    def add_moves(moves):
        result.extend(moves)

    def add_cards(cards_list, type_val):
        moves = make_card_move_from_cards(cards_list, type_val)
        result.extend(moves)

    add_cards(gen_king_bomb(hand), MoveType.KING_BOMB)
    if last_move.get_type() != MoveType.KING_BOMB:
        add_cards(gen_bomb(hand), MoveType.BOMB)

    last_type = last_move.get_type()
    if last_type == MoveType.INVALID or last_type == MoveType.PASS:
        add_cards(gen_single(hand), MoveType.SINGLE)
        add_cards(gen_pair(hand), MoveType.PAIR)
        add_cards(gen_triple(hand), MoveType.TRIPLE)
        add_cards(gen_serial_single(hand), MoveType.SERIAL_SINGLE)
        add_cards(gen_serial_pair(hand), MoveType.SERIAL_PAIR)
        add_cards(gen_serial_triple(hand), MoveType.SERIAL_TRIPLE)
        add_moves(gen_three_one(hand))
        add_moves(gen_three_two(hand))
        add_moves(gen_four_two(hand))
        add_moves(gen_four_two_two(hand))
        add_moves(gen_serial_three_one(hand))
        add_moves(gen_serial_three_two(hand))
    elif last_type == MoveType.SINGLE:
        add_cards(gen_single(hand), MoveType.SINGLE)
    elif last_type == MoveType.PAIR:
        add_cards(gen_pair(hand), MoveType.PAIR)
    elif last_type == MoveType.TRIPLE:
        add_cards(gen_triple(hand), MoveType.TRIPLE)
    elif last_type == MoveType.SERIAL_SINGLE:
        add_cards(gen_serial_single(hand), MoveType.SERIAL_SINGLE)
    elif last_type == MoveType.SERIAL_PAIR:
        add_cards(gen_serial_pair(hand), MoveType.SERIAL_PAIR)
    elif last_type == MoveType.SERIAL_TRIPLE:
        add_cards(gen_serial_triple(hand), MoveType.SERIAL_TRIPLE)
    elif last_type == MoveType.THREE_ONE:
        add_moves(gen_three_one(hand))
    elif last_type == MoveType.THREE_TWO:
        add_moves(gen_three_two(hand))
    elif last_type == MoveType.FOUR_TWO:
        add_moves(gen_four_two(hand))
    elif last_type == MoveType.FOUR_TWO_TWO:
        add_moves(gen_four_two_two(hand))
    elif last_type == MoveType.SERIAL_THREE_ONE:
        add_moves(gen_serial_three_one(hand))
    elif last_type == MoveType.SERIAL_THREE_TWO:
        add_moves(gen_serial_three_two(hand))

    if last_move.get_type() not in (MoveType.PASS, MoveType.INVALID):
        result.append(CardMove(MoveType.PASS))

    from cardMove import moveCompareResult
    result = [m for m in result if m.compare(last_move) == moveCompareResult.GREATER or m.get_type() == MoveType.PASS]
    return result
