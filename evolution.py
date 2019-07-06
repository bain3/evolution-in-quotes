# --------------------------------------- Imports ---------------------------------------
import random
import keyboard
import time
import os
import logging
from itertools import count
# ---------------------------------- Setting constants ----------------------------------
mapSize = (80, 40)
nearest = None
animals = []
Foods = []
# ---------------------------- Setting up  logging for debug ----------------------------
logging.basicConfig(filename='log.log',
                            filemode='w',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
logging.info('Start')
# --------------------------- Defining functions and classes ----------------------------


def Visual(fds, anm, mapSiz):
    # The visual output of the program. It shows the full map and when the user holds 's' it shows details of
    # the animals.
    output = ""
    # Repeat for y dimension
    for y in range(0, mapSiz[1]+1):
        # Create list for x dimension
        xlist = []
        for x in range(0, mapSiz[0] + 1):
            xlist.append(' ')
        for fd in fds:
            if fd.coords[1] == y:
                xlist[fd.coords[0]] = 'F'
        for an in anm:
            if an.coords[1] == y:
                xlist[an.coords[0]] = 'A'
        output += ' '.join(xlist) + '\n' # Joining and creating a string that can be showed in one print.
    os.system('cls')
    print(output)
    print('ID - Hunger - Coords   Animals alive: ' + str(len(animals)) + '       ' + str(time.asctime()) + '\n')
    if keyboard.is_pressed('s'):
        # TODO: Multiple columns of info. Better use of all the horizontal space.
        for an in anm:
            print('{:<3} {:<2} {:<10} {:>2}'.format(str(an.id), str(an.hunger), str(an.coords), str(an.parent)))

    if keyboard.is_pressed('p'):
        time.sleep(0.5)
        while not keyboard.is_pressed('p'):
            time.sleep(0.2)

class Food:
    # Food like herbs and stuff. Each instance places itself on the map. (doesn't check if there is anything
    # in the square it wants to place itself in).
    def __init__(self):
        # Setting up variables.
        self.coords = [random.randint(0, mapSize[0]), random.randint(0, mapSize[1])] # Coordinates of the food
        self.eaten = False # A boolean that determines if the food has been eaten or not.
        self.eatTime = 0 # Simple counter for the Food.regen function.
        self.regenWait = 12 # The value it needs to reach to regenerate.

    def regen(self):
        # Simple regenerating function that should called every round by the main process to work properly.
        if self.eaten:
            self.eatTime += 1
            if self.eatTime == self.regenWait:
                self.eatTime = 0
                self.eaten = False


class Animal:
    _ids = count(0)
    # Animal class. Instance places itself in a square. It can find food (self.findF), calculate distance from an object
    # (self.distanceFrom)

    def __init__(self, stomach, speed, viewd, parent):
        # Setting up variables and spawning the animal in the map. It is randomly chosen by the program.
        self.coords = [random.randint(0, mapSize[0]), random.randint(0, mapSize[1])] # Spawn coordinates of the animal
        self.id = next(self._ids) # ID of the animal. Used for debugging.
        self.hunger = 0 # Counter for the hunger of the animal, should be increased every round.
        self.age = 0 # Counter for the age of the animal, should be increased every round.
        self.stomach = stomach # The hunger value that needs to be reached before the animal looks for food.
        self.viewdist = viewd # View distance of the animal.
        self.speed = speed # Moving speed of the animal.
        self.sFood = [] # The food that it has seen before.
        if parent is None:
            self.parent = self.id
        else:
            self.parent = parent
        logging.debug(str(self.id) + ' has sprung to life')
        if speed < 0 or viewd < 0:
            self.die()


    def findF(self):
        # Searching for food that is in my view distance. It needs to be in my view distance. Return a list of all the
        # found food in the form of its instance.
        foundF = []
        for fd in Foods:
            if fd.coords[0] in range(self.coords[0] - self.viewdist, self.coords[0] + self.viewdist) and \
                    fd.coords[1] in range(self.coords[1] - self.viewdist, self.coords[1] + self.viewdist) and not fd.eaten:
                foundF.append(fd)
        return foundF


    def distanceFrom(self, entity):
        # Calculation of distance from objects. Need to pass an entity like Food class or Animal class.
        return abs(self.coords[0] - entity.coords[0]) + abs(self.coords[1] - entity.coords[1])


    def moveTowards(self, entity):
        if self.speed < 0:
            logging.critical(str(self.id) + ': i have speed of:' + str(self.speed) + '. killed myself.')
            self.die()
            return
        # Moving towards an object like food. Moves in the direction that its the farthest away from the object.
        # Preferred coordinate is x (0)
        coordToChange = 0
        logging.debug('Move towards : ' + str(self.id) + ': ' + str(self.coords) + ' --> ' + str(entity.coords))
        if entity.coords == self.coords:
            return
        elif self.distanceFrom(entity) <= self.speed: # Slow down if close enough.
            self.coords[0] = entity.coords[0]
            self.coords[1] = entity.coords[1]
            return
        if abs(self.coords[1] - entity.coords[1]) > abs(self.coords[0] - entity.coords[0]): # Change move direction if its further away.
            coordToChange = 1
        if entity.coords[coordToChange] < self.coords[coordToChange]:
            if self.coords[coordToChange]-self.speed > 0:
                logging.debug('substracting from my coords ' + str(self.speed))
                self.coords[coordToChange] -= self.speed
            else:
                logging.debug('limit reached, setting to 0')
                self.coords[coordToChange] = 0
        else:
            if self.coords[coordToChange]+self.speed <= mapSize[coordToChange]:
                logging.debug('adding to my coords ' + str(self.speed))
                self.coords[coordToChange] += self.speed
            else:
                logging.debug('limit reached, setting to mapSize')
                self.coords[coordToChange] = mapSize[coordToChange]


    def eat(self, fd):
        # Eating food. Checks if the animal is in the same place as the food.
        if fd.coords == self.coords:
            fd.eaten = True
            if self.hunger <= 10: self.hunger = 0
            else: self.hunger -= 10


    def wander(self):
        # Wandering around when the animal doesn't have anything to do. It chooses a random direction to move in.
        coordToChange = random.randint(0,1)
        moveto = random.choice([-self.speed,self.speed])
        if 0 <= self.coords[coordToChange]+moveto < mapSize[coordToChange]:
            # Check if the animal isn't going outside the map.
            self.coords[coordToChange] += moveto
            logging.info('Wander: ' + str(self.id) + ' --> ' + str(self.coords))


    def reproduce(self):
        # Creates an instance of itself that is a bit modified.
        logging.debug('Reproduce')
        animals.append(Animal(random.randint(self.stomach - 2, self.stomach + 2), random.randint(self.speed - 2, self.speed + 2), random.randint(self.viewdist - 2, self.viewdist + 2), self.parent))


    def die(self):
        logging.debug(str(self.id) + ':i died')
        if self in animals:
            animals.remove(self)
        del self


# ----------------------------------     Main Code     ----------------------------------
# Creating food instances
if __name__=='__main__':
    numOfFood = int(input('Number of food: '))
    numOfAnimals = int(input('Number of animals:'))
    windowSize = [mapSize[0] * 2 + 3, mapSize[1]]
    os.system('title Ecosystem by bain')
    os.system('mode con: cols=' + str(windowSize[0]) + ' lines=' + str(windowSize[1]+5*numOfAnimals))
    for i in range(numOfFood):
        Foods.append(Food())
    # Creating animal instances
    for i in range(numOfAnimals):
        animals.append(Animal(random.randint(2, 30), random.randint(1, 5), random.randint(5, 40), None))
    counter = 0
    while True:
        counter +=1
        for food in Foods: # Looping through all instances of the food class
            food.regen()
        for ani in animals: # Evaluation of the next move from the Animal.
            # TODO: Remember already found food?
            if ani.hunger >= ani.stomach:
                # Finding the nearest food.
                ani.sFood = ani.findF()
                if len(ani.sFood) != 0:
                    nearest = ani.sFood[0]
                    for food in ani.sFood:
                        if ani.distanceFrom(food) < ani.distanceFrom(nearest):
                            nearest = food
            if nearest is not None:
                # Moving to and eating the nearest food.
                if ani.distanceFrom(nearest) != 0:
                    ani.moveTowards(nearest)
                elif ani.coords == nearest.coords:
                    ani.eat(nearest)
                    nearest = None
            else:
                ani.wander()


            # Updating the hunger and age of the Animal.
            if ani.age == 40:
                ani.reproduce()
            if ani.hunger == 60 or ani.age == 180:
                ani.die()
            ani.hunger += 1
            ani.age += 1
        # Visual output and wait.
        Visual(Foods, animals, mapSize)
        time.sleep(0.05)
