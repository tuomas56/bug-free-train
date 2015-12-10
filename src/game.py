import tkinter as tk
from functools import partial
from event import EventManager
import random
from tkinter import *
import time
import noise

class BlockType:
	WATER = 0
	SAND = 1
	GRASS = 2
	STONE = 3
	SNOW = 4

colour_tileset = {
	BlockType.WATER: '#157AC2',
	BlockType.SAND: '#D4CB90',
	BlockType.GRASS: '#15C238',
	BlockType.STONE: '#B3B3B3',
	BlockType.SNOW: '#FFFFFF'
}

class AppEventManager(EventManager):
	def _register_with_method(self, name):
		self._register(name)
		@self.on(name)
		def on_name(data):
			getattr(self, 'on_%s' % name)(data)

class TerrainGenerator:
	def __init__(self, world, seed, water_level=(0.4*255), mountain_level=(0.6*255),
		snow_level=(0.8*255)):
		self.water_level = water_level
		self.mountain_level = mountain_level
		self.snow_level = snow_level
		self.world = world
		self.seed = seed
		self.random = random.Random(seed)

	def get_height(self, x, y):
		pass

class StandardGenerator(TerrainGenerator):
	def get_height(self, x, y):
		if 0 < y < self.world.height or 0 < x < self.world.width:
			height = abs(noise.snoise2(self.seed + x / 64, self.seed + y / 64, 1))
			height = int(height*255)
			return height
		else:
			return 0

	def get_block(self, x, y):
		z = self.get_height(x, y)
		if z < self.water_level:
			return BlockType.WATER
		else:
			up = self.get_height(x, y + 1) < self.water_level
			down = self.get_height(x, y - 1) < self.water_level
			left = self.get_height(x - 1, y) < self.water_level
			right = self.get_height(x + 1, y) < self.water_level
			if any([up, down, left, right]):
				return BlockType.SAND
			elif z > self.snow_level:
				return BlockType.SNOW
			elif z > self.mountain_level:
				return BlockType.STONE
			else:
				return BlockType.GRASS

class ColourUtil:
	def darken(hs, val):
		r, g, b = int(hs[1:3], 16), int(hs[3:5], 16), int(hs[5:7], 16)
		r, g, b = r * (1 + val), g * (1 + val), b * (1 + val)
		r, g, b = int(min(r, 255)), int(min(g, 255)), int(min(b, 255))
		return "#%02x%02x%02x" % (r, g, b)

class Block:
	def __init__(self, x, y, world):
		self.world = world
		self.x, self.y, self.z = x, y, self.world.gen.get_height(x, y)
		self.type = self.world.gen.get_block(self.x, self.y)

	def render(self):
		return ColourUtil.darken(self.world.tileset[self.type], -((self.z - self.world.gen.water_level) / 255)**2)

class World(AppEventManager):
	def __init__(self, height, width, terrain_generator=StandardGenerator, seed=None, block_size=50, tileset=colour_tileset):
		super().__init__()
		self.height, self.width = height, width
		self.pixel_height, self.pixel_width = self.height*block_size, self.width*block_size
		self.block_size = block_size
		self.tileset = tileset

		if seed is None:
			self.gen = terrain_generator(self, 0)
		else:
			self.gen = terrain_generator(self, seed)

		self.blocks = []
		for i in range(width):
			column = []
			for j in range(height):
				column.append(Block(i, j, self))
			self.blocks.append(column)

	def change_block_size(self, size):
		self.block_size += size
		self.pixel_height, self.pixel_width = self.height*size, self.width*size
		print("change")

class Game(AppEventManager):
	def __init__(self, master, world):
		super().__init__()
		self.master = master
		self.world = world
		self.master.maxsize(self.world.pixel_width, self.world.pixel_height)
		self.frame = tk.Frame(master)

		self.frame.grid_rowconfigure(0, weight=1)
		self.frame.grid_columnconfigure(0, weight=1)
		xscrollbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)
		xscrollbar.grid(row=1, column=0, sticky=tk.E+tk.W)
		yscrollbar = tk.Scrollbar(self.frame)
		yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
		self.canvas = Canvas(self.frame, bd=0, xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set,
							 xscrollincrement=self.world.block_size,yscrollincrement=self.world.block_size)

		self.canvas.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

		self.canvas.config(scrollregion=(0, 0, self.world.pixel_width  - self.world.block_size, 
											   self.world.pixel_height - self.world.block_size))
		xscrollbar.config(command=self.canvas.xview)
		yscrollbar.config(command=self.canvas.yview)

		self.frame.pack(expand=True, fill=tk.BOTH)

		self.canvas.bind("<Button 1>",self.grab)
		self.canvas.bind("<B1-Motion>",self.drag)

		self._register_with_method('resize')
		self.master.bind('<Configure>', partial(self.trigger, 'resize'))

		self._register_with_method('key')
		self.master.bind('<Key>', partial(self.trigger, 'key'))

		self.render()

	def grab(self,event):
		self.cy = event.y
		self.cx = event.x

	def drag(self,event):
		if (self.cy-event.y < 0): 
			self.canvas.yview("scroll",1,"units")
		elif (self.cy-event.y > 0): 
			self.canvas.yview("scroll",-1,"units")
		if (self.cx-event.x < 0): 
			self.canvas.xview("scroll",1,"units")
		elif (self.cx-event.x > 0): 
			self.canvas.xview("scroll",-1,"units")
		self.cx = event.x
		self.cy = event.y

	def on_resize(self, event):
		self.render()

	def on_key(self, event):
		pass

	def render(self):
		self.canvas.delete(tk.ALL)
		for y, column in enumerate(self.world.blocks):
			for x, block in enumerate(column):
				self.canvas.create_rectangle((x*self.world.block_size, y*self.world.block_size, 
											 (x+1)*self.world.block_size, (y+1)*self.world.block_size),
											 fill=Block.render(block), outline='')