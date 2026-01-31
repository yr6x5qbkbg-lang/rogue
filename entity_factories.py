from components.ai import HostileEnemy
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=8, base_power=3), #{30, 6, 2}
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=130),
)

# ENEMY LIST
orc = Actor(
    char="o",
    color=(63, 127, 63), #(63, 127, 63)
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=5),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=35),
)
troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=5, base_power=11),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=100),
)
dragon = Actor(
    char="D",
    color=(255, 0, 0), # 赤色
    name="Ancient Dragon",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=35, base_defense=15, base_power=23, magic_resistance=0.5), # 圧倒的な強さ
    inventory=Inventory(capacity=0),
    level=Level(xp_given=0),
)
emu = Actor(
    char="E",
    color=(63, 127, 63),
    name="Emu",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=12, base_defense=1, base_power=6),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=50),
)
hobgoblin = Actor(
    char="H",
    color=(63, 127, 63),
    name="Hobgoblin",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=14, base_defense=2, base_power=7),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=70),
)
bat = Actor(
    char="B",
    color=(63, 127, 63),
    name="Bat",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=14, base_defense=5, base_power=13),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=60),
)
kestral = Actor(
    char="K",
    color=(63, 127, 63),
    name="Kestral",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=5, base_defense=14, base_power=15),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=250),
)
wraith = Actor(
    char="W",
    color=(63, 127, 63),
    name="Wraith",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=20, base_defense=10, base_power=17),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=350),
)
rattlesnake = Actor(
    char="R",
    color=(63, 127, 63),
    name="Rattlesnake",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=15, base_defense=10, base_power=15),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=300),
)
griffith = Actor(
    char="G",
    color=(0, 0, 255),
    name="Griffith",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=28, base_defense=13, base_power=17),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=750),
)
quagga = Actor(
    char="Q",
    color=(63, 127, 63),
    name="Quagga",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=12, base_defense=2, base_power=9),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=80),
)
centaur = Actor(
    char="C",
    color=(63, 127, 63),
    name="Centaur",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=20, base_defense=5, base_power=12),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=135),
)
jabberwock = Actor(
    char="J",
    color=(63, 127, 63),
    name="Jabberwock",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=14, base_defense=8, base_power=16),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=350),
)
nymph = Actor(
    char="N",
    color=(63, 127, 63),
    name="Nymph",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=10, base_power=15),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=160),
)
aquator = Actor(
    char="A",
    color=(63, 127, 63),
    name="Aquator",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=20, base_defense=8, base_power=14),
   inventory=Inventory(capacity=0),
    level=Level(xp_given=120),
)
fancyrat = Actor(
    char="f",
    color=(63, 127, 63),
    name="fancy rat",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=1, base_defense=0, base_power=33),
   inventory=Inventory(capacity=0),
    level=Level(xp_given=500),
)

# ITEM LIST
confusion_scroll = Item(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=30),  # 元の値は10
    value=10,
)
fireball_scroll = Item(
    char="~",
    color=(255, 0, 0),
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=14, radius=3),
    value=10,
)
health_potion = Item(
    char="!",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=10),
    value=20,
)
lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
    value=10,
)

# ITEM LIST(装備)
dagger = Item(
    char="/", color=(0, 191, 255), name="Dagger", equippable=equippable.Dagger(),
    value=0,
)
sword = Item(
    char="/", color=(0, 191, 255), name="Sword", equippable=equippable.Sword(),
    value=10,
)
super_sword = Item(
    char="/", color=(255, 255, 255), name="Super Sword", equippable=equippable.SuperSword(),
    value=10,
)
master_sword = Item(
    char="/", color=(0, 0, 0), name="Master Sword", equippable=equippable.MasterSword(),
    value=10,
)
leather_armor = Item(
    char="[",
    color=(139, 69, 19),
    name="Leather Armor",
    equippable=equippable.LeatherArmor(),
    value=0,
)

chain_mail = Item(
    char="[", color=(139, 69, 19), name="Chain Mail", equippable=equippable.ChainMail(),
    value=30,
)

# ITEM LIST(ゴールド)
gold = Item(
    char="*", 
    color=(255, 215, 0), # 金色 (Gold)
    name="Gold",
    consumable=consumable.GoldConsumable(amount=20), # 金額を指定
)