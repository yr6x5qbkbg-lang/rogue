from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item



class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.
       
        `self.entity` is the object performing the action.
       
        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()
    

class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in list(self.engine.game_map.items):
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")
                

                # もし拾ったものがゴールドだったら、即座に使う
                if item.name == "Gold":
                    item.consumable.activate(self)
                    self.engine.game_map.entities.remove(item)
                    return # ゴールドを拾ったら処理終了
                else:
                    # 通常のアイテム拾得ロジック
                    self.engine.game_map.entities.remove(item)
                    item.parent = self.entity.inventory
                    inventory.items.append(item)

                    self.engine.message_log.add_message(f"You picked up the {item.name}!")
                    return

        raise exceptions.Impossible("There is nothing here to pick up.")


class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self)
    

class DropItem(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)
        
        self.entity.inventory.drop(self.item)


class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)


class WaitAction(Action):
    def perform(self) -> None:
        pass


class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message(
                "You descend the staircase.", color.descend
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")


class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()
    

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")
        
        # === 最低ダメージ実装 ===
        # 単純な引き算で「素のダメージ（差分）」を出す
        damage_diff = self.entity.fighter.power - target.fighter.defense

        if damage_diff > 0:
            # 攻撃力が高い場合はそのままのダメージ
            damage = damage_diff
        elif damage_diff >= -4:
            # 差分が 0, -1, -2, -3, -4 の時は最低 1 ダメージ保証
            damage = 1
        else:
            # 差分が -5 以下の時（防御が5以上高い時）は 0 ダメージ
            damage = 0
        # === ここまで追加 最低ダメージ実装 ===

        # --- ここから追加 デバッグ記録用---
        # 攻撃されたのがプレイヤーだった場合
        if target is self.engine.player:
            self.engine.times_attacked += 1 # 攻撃を受けた回数
        # --- ここまで追加 デバッグ記録用---

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            if target is self.engine.player:
                self.engine.message_log.add_message(
                    f" {attack_desc} for {damage} hit points.", attack_color
                )
            else:
                self.engine.message_log.add_message(
                    f"{attack_desc} for {damage} hit points.", attack_color
                )
            
            # --- ここから追加 デバッグ記録用---
            if target is self.engine.player:
                self.engine.total_damage_taken += damage # 被ダメージ合計
            # --- ここまで追加 デバッグ記録用---
            
            # --- ここから追加 デバッグ記録用追加分---
            # 攻撃したのがプレイヤーだった場合、合計ダメージに加算
            if self.entity is self.engine.player:
                self.engine.total_damage_dealt += damage
            # --- ここまで追加 デバッグ記録用追加分---
            
            target.fighter.hp -= damage
                            
            # === ボーナスアタックの実装 ===
            # プレイヤーが 8 以上のダメージを与えた場合
            if self.entity is self.engine.player and damage >= 8 and target.fighter.hp > 0:
                # 追撃ダメージの計算 (将来のために念の為変数を作っておく)
                bonus_damage = damage
                # メッセージで追撃が発生したことを伝える
                self.engine.message_log.add_message(
                    f"Follow-up attack! {target.name} for {bonus_damage} damage!",
                    (255, 255, 0) # 黄色で強調
                )
                # 追撃の実行
                target.fighter.hp -= bonus_damage
                # 合計ダメージ記録にも加算
                self.engine.total_damage_dealt += bonus_damage
            # === ここまで追加 ボーナスアタックの実装 ===

        else:
            if self.entity is self.engine.player:
                self.engine.message_log.add_message(
                    f"{attack_desc} but does no damage.", attack_color
                )
            else:
                self.engine.message_log.add_message(
                    f" {attack_desc} but does no damage.", attack_color
            
                )

        # --- クリア判定 ---
        ### print(f"OK1.{target.name} ") # デバッグ確認用      
        if target.name == "remains of Ancient Dragon" : #and target.fighter.hp <=0 :
            ### print(f"OK2.{target.name} ")  # デバッグ確認用
            self.engine.message_log.add_message(
                "The Ancient Dragon falls! You have saved the realm!",
                (255, 215, 0) # ゴールド色
                )
            
            # --- ここで換金処理を追加 ---
            # インベントリの価値を計算
            bonus_gold = self.entity.inventory.get_total_inventory_value()
            # Engineにボーナス額を覚えさせておく
            self.engine.item_bonus_gold = bonus_gold
            # プレイヤーが持っている gold プロパティに加算
            if hasattr(self.entity, "gold"):
                self.entity.gold += bonus_gold
            else:
                # 万が一 Actor に gold が定義されていなかった場合の安全策
                setattr(self.entity, "gold", bonus_gold)
            
            self.engine.message_log.add_message(
                f"Items sold for {bonus_gold}G bonus!",
                (255, 215, 0)
            )
            # --- ここまで クリア時換金ボーナス
        
            # クリアフラグを立てる、または専用の画面へ
            self.engine.game_cleared = True
        # --- ここまで追加 クリア判定 ---


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an entity.
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)


class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
    
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()
            