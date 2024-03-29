import sys
from enum import Enum, auto
import random



class Field():
    def __init__(self, x, y, shot=False):
        self.shot = shot
        self.x = x
        self.y = y
    
    def __str__(self):
        return f"X: {self.x}  Y: {self.y}  State: {self.shot.name}" 


class ShipType(Enum):
    BATTLESHIP = auto()
    CRUISER = auto()
    DESTROYER = auto()

    def get_available(self):
        match self:
            case ShipType.BATTLESHIP: return 1
            case ShipType.CRUISER: return 2
            case ShipType.DESTROYER: return 3
            case _: return 0
    
    def get_lenght(self):
        match self:
            case ShipType.BATTLESHIP:
                return 4
            case ShipType.CRUISER:
                return 3
            case ShipType.DESTROYER:
                return 2
            case _:
                return 0

    def get_color(self):
        match self:
            case ShipType.BATTLESHIP:
                return "#92109E"
            case ShipType.CRUISER:
                return "#00EBA1"
            case ShipType.DESTROYER:
                return "#EBA400"
            case _:
                return "gray"
                


class Ship():
    def __init__(self, ship_type):
        self.destroyed = False
        self.lenght = -1
        self.ship_type = None
        self.fields = []
        self.ship_type = ship_type
        self.lenght = ship_type.get_lenght()

    def __str__(self):
        return f"Ship Type: {self.ship_type}  Lenght: {self.lenght}  Destroyed: {self.destroyed}  Fields: {[str(field) for field in self.fields]}"
    


class GameBoard():
    ships = []
    fields = []

    def set_random_ship_placement(self, ship):
        is_horizontal = random.choice([True, False])
        safe_pos = random.randint(0, 10 - ship.lenght)
        other_pos = random.randint(0, 9)
        ship.fields.clear()

        if is_horizontal:
            for z in range(ship.lenght):
                field = Field(safe_pos + z, other_pos, False)
                self.fields.append(field)
                ship.fields.append(field)

        else:
            for z in range(ship.lenght):
                field = Field(other_pos, safe_pos + z, False)
                self.fields.append(field)
                ship.fields.append(field)
                
        occupied_fields = []
        for placed_ship in self.ships:
            for fld in placed_ship.fields: occupied_fields.append(fld)
        for field_to_test in ship.fields:
            for occupied_field in occupied_fields:
                if (field_to_test.x, field_to_test.y) == (occupied_field.x, occupied_field.y):
                        print(f"Collided with other ship! {field_to_test.x}, {field_to_test.y}      {occupied_field.x}, {occupied_field.y}")
                        self.set_random_ship_placement(ship)


    def gernerate_board(self):
        for ship_type in ShipType:
            for i in range(ship_type.get_available()):
                ship = Ship(ship_type)
                self.set_random_ship_placement(ship)
                self.ships.append(ship)
        #for ship in self.ships:
        #    print(str(ship))

    def clear_board(self):
        self.ships.clear()
        self.fields.clear()



