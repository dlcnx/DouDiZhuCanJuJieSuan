from enum import IntEnum
from typing import List, Tuple
from cards import Cards
from cardMove import CardMove, MoveType

class FACTION(IntEnum):
    """阵营标识"""
    OUR_SIDE = 0
    ENEMY_SIDE = 1

MAX_SCORE = 99
MIN_SCORE = -99

class GameStatus:
    """游戏状态，将双方手牌压缩到一个数组中以便作为缓存键

    cur_hand每个元素：低4位存当前玩家手牌数量，高4位存对手手牌数量
    递归时交换双方位置，始终从"当前玩家"视角计算
    """

    def __init__(self, our_hand: Cards, enemy_hand: Cards, last_move: CardMove):
        self.cur_hand: List[int] = [0] * Cards.N
        for i in range(Cards.N):
            self.cur_hand[i] = (our_hand.cardCount[i] & 0x0F) | ((enemy_hand.cardCount[i] & 0x0F) << 4)
        self.last_move = last_move

    def get_cur_player_hand(self) -> Cards:
        """获取当前玩家的手牌"""
        res = Cards()
        for i in range(Cards.N):
            res.cardCount[i] = self.cur_hand[i] & 0x0F
        return res

    def get_cur_enemy_hand(self) -> Cards:
        """获取对手的手牌"""
        res = Cards()
        for i in range(Cards.N):
            res.cardCount[i] = (self.cur_hand[i] >> 4) & 0x0F
        return res

    def get_cur_player_card_num(self) -> int:
        """获取当前玩家手牌总数"""
        num = 0
        for i in range(Cards.N):
            num += self.cur_hand[i] & 0x0F
        return num

    def get_cur_enemy_card_num(self) -> int:
        """获取对手手牌总数"""
        num = 0
        for i in range(Cards.N):
            num += (self.cur_hand[i] >> 4) & 0x0F
        return num

    def exist_zero_card_player(self) -> bool:
        """判断是否有一方已出完牌"""
        tmp = 0
        for i in range(Cards.N):
            tmp |= self.cur_hand[i]
        return (tmp & 0x0F) == 0 or (tmp & 0xF0) == 0

    def __eq__(self, other) -> bool:
        return self.cur_hand == other.cur_hand and self.last_move == other.last_move

    def __hash__(self) -> int:
        return hash(tuple(self.cur_hand) + (hash(self.last_move),))

class BestAction:
    """最佳出牌结果，包含出牌动作和评分"""

    def __init__(self, move: CardMove, score: int):
        self.move = move
        self.score = score

    def __eq__(self, other) -> bool:
        return self.move == other.move and self.score == other.score

    def __hash__(self) -> int:
        return hash((hash(self.move), self.score))

actionCache: dict = {}

class GameCore:
    """游戏核心逻辑，管理双方手牌和出牌状态"""

    def __init__(self, our: Cards, enemy: Cards, last: CardMove = None):
        self.our_hand = our
        self.enemy_hand = enemy
        self.last_move = last if last else CardMove(MoveType.INVALID)
        self.cur_player = FACTION.OUR_SIDE

    def get_our_hand(self) -> Cards:
        """获取我方手牌"""
        return self.our_hand

    def get_enemy_hand(self) -> Cards:
        """获取敌方手牌"""
        return self.enemy_hand

    def is_game_over(self) -> bool:
        """判断游戏是否结束（任一方出完牌）"""
        return self.our_hand.card_num() == 0 or self.enemy_hand.card_num() == 0

    def get_current_status(self) -> GameStatus:
        """获取当前游戏状态，用于递归计算"""
        cur_player_hand = self.our_hand if self.cur_player == FACTION.OUR_SIDE else self.enemy_hand
        cur_enemy_hand = self.enemy_hand if self.cur_player == FACTION.OUR_SIDE else self.our_hand
        return GameStatus(cur_player_hand, cur_enemy_hand, self.last_move)

    def play_card(self, move: CardMove) -> bool:
        """执行出牌，更新手牌、上一手牌和当前出牌方，若出牌不合法返回False"""
        from moveGen import gen_all_moves
        cur_player_hand = self.our_hand if self.cur_player == FACTION.OUR_SIDE else self.enemy_hand
        all_possible_moves = gen_all_moves(cur_player_hand, self.last_move)

        if move in all_possible_moves:
            self.last_move = move
            cur_player_hand.remove(move.get_all_cards())
            self.cur_player = FACTION.ENEMY_SIDE if self.cur_player == FACTION.OUR_SIDE else FACTION.OUR_SIDE
            return True
        return False

def calculate_best_action(status: GameStatus) -> BestAction:
    """递归搜索当前状态下的最佳出牌

    遍历所有合法出牌，对每种出牌模拟对手的最优应对，
    找到一个对手无法获胜的动作则返回，否则判定敌方必胜
    """

    global actionCache

    if status in actionCache:
        return actionCache[status]

    if status.exist_zero_card_player():
        raise RuntimeError("Game over, one player has no cards left, and should not reach here")

    from moveGen import gen_all_moves
    move_list = gen_all_moves(status.get_cur_player_hand(), status.last_move)
    if not move_list:
        raise RuntimeError("No valid moves available, should not reach here")

    move_list.sort(key=lambda m: m.get_all_card_num(), reverse=True)

    cur_player_card_num = status.get_cur_player_card_num()
    for move in move_list:
        if cur_player_card_num == move.get_all_card_num():
            actionCache[status] = BestAction(move, MAX_SCORE)
            return actionCache[status]

        tmp = status.get_cur_player_hand()
        tmp.remove(move.get_all_cards())
        if tmp.card_num() == 0:
            actionCache[status] = BestAction(move, MAX_SCORE)
            return actionCache[status]

        new_status = GameStatus(status.get_cur_enemy_hand(), tmp, move)

        enemy_best = calculate_best_action(new_status)
        if enemy_best.score == MAX_SCORE:
            continue
        else:
            actionCache[status] = BestAction(move, MAX_SCORE)
            return BestAction(move, MAX_SCORE)

    actionCache[status] = BestAction(CardMove(MoveType.INVALID), MIN_SCORE)
    return actionCache[status]
