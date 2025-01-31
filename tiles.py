from pyglet import resource, sprite, graphics
from xml.etree.ElementTree import parse


class Tileset:
    def __init__(self, filename) -> None:
        self.filename = filename

        self.tiles = []

    def get_tiles(self) -> list:
        return self.tiles
    
    def parse_tileset(self) -> None:
        with open(self.filename) as tset:
            root = parse(tset).getroot()
        
        for tile in root:
            if tile.tag == "grid":
                continue

            path_to_tsx = self.filename
            while path_to_tsx[-1] != '/':
                path_to_tsx = path_to_tsx[:-1]

            path = path_to_tsx + tile[1].attrib['source']

            image = resource.image(path)

            tile_id = int(tile.attrib['id'])
            while tile_id > len(self.tiles):
                self.tiles.append(None)
            self.tiles.append(image)


class Tilemap:
    def __init__(self, filename, screen_size) -> None:
        self.filename = filename
        self.screen_width, self.screen_height = screen_size

        self.tileset = None
        self.map = None
        self.position = [self.screen_width // 2, self.screen_height // 2]

        self.batch = graphics.Batch()
        self.tilemap_size = [0, 0]

        self.sprite_list = []

        self.tile_list = None

        self.parse_map()

    def set_screen_size(self, zoom) -> None:
        self.screen_width = self.screen_width/zoom
        self.screen_height = self.screen_height/zoom

    def parse_map(self) -> None:
        with open(self.filename) as tmap:
            root = parse(tmap).getroot()

        self.tilemap_size = [
            int(root.attrib['width']), 
            int(root.attrib['height'])
        ]

        self.tileset = Tileset(root[0].attrib['source'].replace('..', 'assets'))

        self.tileset.parse_tileset()

        tile_list = self.tileset.get_tiles()

        for layer in root:
            if layer.tag == 'tileset':
                continue

            data = layer[0].text

            offset = 0

            for y, row in enumerate(data.split('\n')[1:-1]):
                tiles = row.split(',')[:-1]

                for x, tile in enumerate(tiles):
                    if tile == "0":
                        continue

                    tile_id = int(tile) - 1 + offset

                    condition = True
                    while condition:
                        try:
                            tile_sprite = sprite.Sprite(
                                tile_list[tile_id],
                                x * 16 + self.position[0], 
                                y * 16 + self.position[1],
                                batch=self.batch)
                            self.sprite_list.append(tile_sprite)
                            condition = False
                        except KeyError:
                            offset += 1

    def adjust_position(self, player_pos) -> None:
        x, y = player_pos
        self.position = [
            self.screen_width // 2 - x * 16,
            self.screen_height // 2 - y * 16
        ]

        for i, tile in enumerate(self.sprite_list):
            tile.x = i % self.tilemap_size[0] * 16 + self.position[0]
            tile.y = (self.tilemap_size[1] - i // self.tilemap_size[0] - 1) * 16 + self.position[1]

