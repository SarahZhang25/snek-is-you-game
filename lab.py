"""6.009 Lab 10: Snek Is You Video Game"""

import doctest
# import pprint as pp

# NO ADDITIONAL IMPORTS!

# All words mentioned in lab. You can add words to these sets,
# but only these are guaranteed to have graphics.
NOUNS = {"SNEK", "FLAG", "ROCK", "WALL", "COMPUTER", "BUG"} # these all have a corresponding text and graphical object
PROPERTIES = {"YOU", "WIN", "STOP", "PUSH", "DEFEAT", "PULL"} # represent behaviors that can be assigned to nouns
WORDS = NOUNS | PROPERTIES | {"AND", "IS"}

# Maps a keyboard direction to a (delta_row, delta_column) vector.
direction_vector = {
    "up": (-1, 0),
    "down": (+1, 0),
    "left": (0, -1),
    "right": (0, +1),
}


#default behaviors
text_obj_behavior = "PUSH"
graphical_obj_behavior = {"snek": None, "flag": None, "rock": None, "wall": None, "computer": None, "bug": None}
property_assoc = {"YOU": [], "STOP": [], "PUSH": [], "PULL": [], "DEFEAT": [], "WIN": []}
snek_objs = set() # locations


class Board:
    """
    Representation of the 'snek is you' game board. Board objects will consist of the following attributes:

    board: 2d array; board[i][j] is an array [] containing all pieces in the cell at row i and column j of the board
    victory_state: boolean; True if board is in a state considered as winning, False elsewise
    num_rows, num_cols: dimensions of the board
    objects_directory: dictionary keyed by object type name (as described in the lab writeup), values are list of the
        objects of that type in play on the board
    behavior_assignments: dictionary keyed by graphical object type, values are a set of the behaviors that the graphical
        object has in the current board. i.e. contains all rules on the board
    property_assocs: dictionary keyed by property, values are a list of objects that have that property in the board 

    """
    def __init__(self, level_description):
        """
        Arguments: 
            level_description: canonical description
        """
        self.board = level_description
        self.victory_state = False
        self.num_rows = len(level_description)
        self.num_cols = len(level_description[0])
        
        self.objects_directory = {**{key.lower():[] for key in NOUNS}, **{key:[] for key in WORDS}}
        self.behavior_assignments = {"snek": set(), "flag": set(), "rock": set(), "wall": set(), "computer": set(), "bug": set()}
        
        self.property_assocs = {"YOU": [], "STOP": [], "PUSH": [], "PULL": [], "DEFEAT": [], "WIN": []}


        for i in range(self.num_rows): 
            for j in range(self.num_cols):
                for ind, obj in enumerate(self.board[i][j]):
                    if obj in NOUNS:
                        new_obj = Noun((i, j), obj)
                    elif obj in PROPERTIES:
                        new_obj = Property((i, j), obj)
                    elif obj in ("snek", "flag", "rock", "wall", "computer", "bug"):
                        new_obj = GraphicalObj((i, j), obj, self)
                    elif obj in ("IS", "AND"):
                        new_obj = TextObj((i, j), obj)

                    self.board[i][j][ind] = new_obj  # replace the string with the newly made associated object
                    self.objects_directory[obj].append(new_obj) # add it to the directory
                    
        self.evaluate_rules(update_replacements = False)
                    

    def evaluate_rules(self, update_replacements = True):
        """
        Update the behaviors assigned to objects according to all rules in the board

        Arguments:
            update_replacements: boolean; whether to or not run the DEFEAT rule

        Returns:
            None
        """
        self.property_assocs = {"YOU": [], "STOP": [], "PUSH": [], "PULL": [], "DEFEAT": [], "WIN": []}

        IS_objs = self.objects_directory["IS"]
        for is_obj in IS_objs:
            i, j = is_obj.position
            lefts, rights, aboves, belows = [], [], [], []
            # consider left/right (horizontal) rules
            if not (j == 0 or j == self.num_cols-1): # consider left/right
                # collect all subjects to the left of IS
                lefts = []
                if self.board[i][j-1] != [] and isinstance(self.board[i][j-1][0], Noun):
                    lefts.append(self.board[i][j-1][0].type) # piece immediately to the left of IS
                    # process ANDs if they exist
                    skip = 2
                    while self.is_in_bounds(i, j-1-skip) and len(self.board[i][j-skip]) > 0 and self.board[i][j-skip][0].type == "AND":
                        # print("CHECKING", self.board[i][j-1-skip:j-1-skip+2])
                      
                        if len(self.board[i][j-1-skip]) > 0 and isinstance(self.board[i][j-1-skip][0], Noun):
                            lefts.append(self.board[i][j-1-skip][0].type)
                            skip += 2
                        else:
                            break
                
                # collect all predicates to the right of IS
                rights = []
                if self.board[i][j+1] != [] and (isinstance(self.board[i][j+1][0], Noun) or isinstance(self.board[i][j+1][0], Property)):
                    rights.append(self.board[i][j+1][0].type) # piece immediately to the left of IS
                    # process ANDs if they exist
                    skip = 2
                    while self.is_in_bounds(i, j+1+skip) and len(self.board[i][j+skip]) > 0 and self.board[i][j+skip][0].type == "AND":
                        if len(self.board[i][j+1+skip]) > 0  and (isinstance(self.board[i][j+1+skip][0], Noun) or isinstance(self.board[i][j+1+skip][0], Property)):
                            rights.append(self.board[i][j+1+skip][0].type)
                            skip += 2
                        else:
                            break

            # consider above/below (vertical) rules
            if not (i == 0 or i == self.num_rows-1):
                # collect all subjects above IS
                aboves = []
                if self.board[i-1][j] != [] and isinstance(self.board[i-1][j][0], Noun):
                    aboves.append(self.board[i-1][j][0].type) # piece immediately above IS
                    # process ANDs if they exist
                    skip = 2
                    while self.is_in_bounds(i-1-skip, j) and len(self.board[i-skip][j]) > 0 and self.board[i-skip][j][0].type == "AND": # look for AND
                        print("CHECKING", self.board[i-1-skip:i-1-skip+2][j])
                        if len(self.board[i-1-skip][j]) > 0 and isinstance(self.board[i-1-skip][j][0], Noun): # look for NOUN
                            aboves.append(self.board[i-1-skip][j][0].type)
                            skip += 2
                        else: # if not found, end loop
                            break

                # collect all predicates below IS
                belows = []
                if self.board[i+1][j] != [] and (isinstance(self.board[i+1][j][0], Noun) or isinstance(self.board[i+1][j][0], Property)):
                    belows.append(self.board[i+1][j][0].type) # piece immediately below IS
                    # process ANDs if they exist
                    skip = 2
                    while self.is_in_bounds(i+1+skip, j) and len(self.board[i+skip][j]) > 0 and self.board[i+skip][j][0].type == "AND": # look for AND
                        if len(self.board[i+1+skip][j]) > 0 and (isinstance(self.board[i+1+skip][j][0], Noun) or isinstance(self.board[i+1+skip][j][0], Property)): # look for NOUN
                            belows.append(self.board[i+1+skip][j][0].type)
                            skip += 2
                        else: # if not found, end loop
                            break

            # list of all rules in (subject, predicate) format
            rules = []
            if len(lefts) != 0 and len(rights) != 0:
                for i in lefts:
                    for j in rights:
                        rules.append((i, j))
            if len(aboves) !=0 and len(belows) != 0:
                for i in aboves:
                    for j in belows:
                        rules.append((i, j))

            print("RULES:", rules)

            # update assignment dictionaries to reflect rules
            replace_nouns_rules = [] # rules to follow for fixing nouns
            replace_nouns_objs = [] # obj to fix
            for subj, pred in rules:
                # self.behavior_assignments[subj.lower()] = set()
                if pred in PROPERTIES: # set rule
                    if "PUSH" in self.behavior_assignments[subj.lower()] and pred == "STOP":
                        pass
                    self.behavior_assignments[subj.lower()].add(pred) # update behavior assignments dict
                    self.property_assocs[pred].extend(self.objects_directory[subj.lower()]) # update property associations dict
                elif pred in NOUNS: # collect rules and objects to convert all instances of subj to type of pred
                    replace_nouns_rules.append((subj, pred))
                    replace_nouns_objs.append(self.objects_directory[subj.lower()]) 

            if update_replacements: # make noun is noun replacements
                print("MAKING REPLACEMENTS")
                self.make_noun_is_noun_replacements(replace_nouns_rules, replace_nouns_objs)
                    

            print("BEHAVIOR ASSIGNMENTS:", self.behavior_assignments)
            # print("OBJECTS DIRECTORY:", self.objects_directory)


        # PUSH takes precedence over STOP            
        for piece_type in self.behavior_assignments:
            if ("PUSH" in self.behavior_assignments[piece_type]) and ("STOP" in self.behavior_assignments[piece_type]):
                self.behavior_assignments[piece_type].remove("STOP")


    def make_noun_is_noun_replacements(self, rules, objects):
        """
        Executes the "NOUN is NOUN" rule by updating the position and behavior attribtues of all objects affected

    
        Arguments:
            rules: list of (n1, n2) rules
            objects: list of list of objects impacted by each rule in rules argument
        
        Returns:
            None
        """

        rules_processed = [0 for _ in range(len(rules))]
        n1s = [i[0] for i in rules]
        def replace_subj_with_pred(n1, n2, n1_insts):
            """
            Processes 1 'NOUN is NOUN' (n1 is n2) rule

            Arguments:
                n1: noun type to be replaced
                n2: noun type to convert to
                n1_insts: objects that are currently type n1

            Returns:
                None
            """
            for inst in n1_insts:
                inst.type = n2.lower()
                
                # print(inst.type)
                self.objects_directory[n2.lower()].append(inst) # add inst to correct type in directory

                
                for behavior in inst.behavior: # remove inst from the old behavior they were bound to in property_assocs 
                    if inst in self.property_assocs[behavior]:
                        self.property_assocs[behavior].remove(inst)

                inst.behavior = self.behavior_assignments[n2.lower()]

                for behavior in inst.behavior: # add inst to the new behavior they are bound to in property_assocs 
                    self.property_assocs[behavior].append(inst)

            self.objects_directory[n1.lower()] = [] # clear out prior n1 instances

            rules_processed[n1s.index(n1)] = 1 # update tracker
            
        # process the rules given
        while not all(rules_processed):
            process_next = rules_processed.index(0)
            n1, n2 = rules[process_next]
            replace_subj_with_pred(n1, n2, objects[process_next])

        return # replacements complete


    def move_possible(self, direction, r, c):
        """
        Checks if a move in a given direction from a given cell is valid or not

        Arguments:
            direction: string representing direction to move in
            r, c: row, col to move from

        Returns:
            True if can move to given new position, False if not
        """
        dr, dc = direction_vector[direction]
        next_r, next_c = r+dr, c+dc
        print("CHECKING IF MOVE POSSIBLE to", next_r, next_c)

        if not self.is_in_bounds(next_r, next_c):
            print("MOVE NOT POSSIBLE: out of bounds")
            return False

        # consider existing non-YOU objs in desired cell to move to
        print(self.board[next_r][next_c])
        pushable_objs = [i for i in self.board[next_r][next_c] if ("PUSH" in i.behavior)]        
        print("pushable objects:", pushable_objs)  

        # check for STOP behavior
        push_blocked = any([("STOP" in obj.behavior) for obj in self.board[next_r][next_c]]) # True if any of the obj in leading objs have STOP behavior
        if push_blocked:
            print("MOVE NOT POSSIBLE: encountered object with STOP behavior")
            return False

        # check for PUSH
        for obj in pushable_objs:
            if "PUSH" in obj.behavior: # attempt to push the object and pull any applicable
                return self.move_single_piece(obj, direction)
            
        return True

    def move_single_piece(self, object, direction):
        """
        Moves a single given piece in a given direction
        
        Arguments:
            object: graphical object to move
            direction: string representing direction to move

        Returns:
            1 if object was successfully moved, 0 if not
        """
        print("MOVING", object.type, "at", object.position, direction)
        r, c = object.position
        dr, dc = direction_vector[direction]

        if self.move_possible(direction, r, c):
            # move object
            self.board[r][c].remove(object) # remove prev pos
            self.board[r+dr][c+dc].append(object) # add obj to new pos
            object.position = (r+dr, c+dc)

            # check if pull is blocked
            pull_blocked = any([("STOP" in obj.behavior) for obj in self.board[r][c]]) # True if any of the obj in current cell have STOP behavior
            if not pull_blocked:

                # collect all pullable objects trailing the current position
                pullable_objs = []#[i for i in self.board[r][c] if ("PULL" in i.behavior)]
                prev_r, prev_c = r-dr, c-dc
                print("collecting pullables")
                while self.is_in_bounds(prev_r, prev_c): 
                    new_pullable_objs = [i for i in self.board[prev_r][prev_c] if ("PULL" in i.behavior)]
                    # print(r, c, prev_r, prev_c, self.board[prev_r][prev_c])
                    any_STOPs = any([i for i in self.board[prev_r+dr][prev_c+dc] if ("STOP" in i.behavior)])
                    if new_pullable_objs == [] or any_STOPs: # if no pullable objects in this cell or STOP object encountered, then exit loop
                        break
                    else:
                        # print("this",r,c, self.board[r][c])
                        new_pullable_objs += [i for i in self.board[prev_r+dr][prev_c+dc] if ("PUSH" in i.behavior)]# or "PULL" in i.behavior)]
                        # new_pullable_objs += []
                        pullable_objs.extend(new_pullable_objs)
                        print("here", new_pullable_objs)
                        prev_r -= dr
                        prev_c -= dc
                print("PULLABLE OBJS:", pullable_objs)

                # pull any applicable objects   
                for pull_obj in pullable_objs:
                    print("moving", pull_obj.type, "at", pull_obj.position)
                    # self.move_single_piece(pull_obj, direction)
                    r_pull, c_pull = pull_obj.position
                    # if self.move_possible(direction, r_pull, c_pull):
                    self.board[r_pull][c_pull].remove(pull_obj) # remove prev pos
                    self.board[r_pull+dr][c_pull+dc].append(pull_obj) # add obj to new pos
                    pull_obj.position = (r_pull+dr, c_pull+dc) # update object's position attribute 

            return 1 # move successful
        return 0 # move unsuccessful


    def make_move(self, direction):
        """
        Apply a move to all player-controlled graphical objects on the board

        Arguments:
            direction: string representing direction to move

        Returns:
            self.victory_state: boolean of whether or not the board is in a win state
        """
        print("MAKING MOVE", direction)
        
        YOU_objs = self.property_assocs["YOU"]
        # print("you are:", YOU_objs)
        
        num_successful_moves = 0
        for obj in YOU_objs:
            num_successful_moves += self.move_single_piece(obj, direction)

            
        # pp.pprint(self.board)
        # if num_successful_moves > 0: # only reevaluate rules if something was moved
        self.evaluate_rules()

        print(num_successful_moves, "moves successful out of", len(YOU_objs), "possible")
        # return num_successful_moves == len(YOU_objs)

        # handle defeat
        self.process_defeat()
        print("PROCESSING DEFEATS")
        print(self.property_assocs["YOU"])

        # check if move results in victory
        self.victory_check()
        print("CHECKING VICTORY:", self.victory_state)
        return self.victory_state


    def process_defeat(self):
        """
        Process the DEFEAT rule in the game board by removing relevant objects. Returns None
        """
        # "YOU" property stands on the same cell as a "rock" graphical object, then the "YOU" object disappears 
        # (though the player will still be able to control any other remaining graphical objects that have the "YOU" property).
        if self.property_assocs["DEFEAT"] == []:
            return
        else:
            defeat_positions = {obj.position for obj in self.property_assocs["DEFEAT"]}
            print(defeat_positions)
            print(self.property_assocs["YOU"])
            to_remove = []
            for obj in self.property_assocs["YOU"]:
                if obj.position in defeat_positions:
                    to_remove.append(obj)
            for obj in to_remove:
                print("deleting", obj)
                # remove the object
                self.property_assocs["YOU"].remove(obj)
                self.objects_directory[obj.type].remove(obj)
                self.board[obj.position[0]][obj.position[1]].remove(obj)
            return

    def victory_check(self):
        """
        Returns True if the current board is in a state of victory or False if not
        """
        if self.property_assocs["WIN"] == []:
            self.victory_state = False # can never win if no object with WIN behavior appears on the board
            return self.victory_state
        
        else:
            winning_positions = {obj.position for obj in self.property_assocs["WIN"]}
            for obj in self.property_assocs["YOU"]:
        
                if obj.position in winning_positions:
                    self.victory_state = True # WIN state satisfied
                    return self.victory_state
                    
            self.victory_state = False # no object with YOU behavior is in the same cell as an object with WIN behavior
            return self.victory_state
        


    def is_in_bounds(self, r, c):
        """
        Checks if a coordinate (r, c) is in bounds of the board

        Arguments:
            r, c: row, col of cell to check
        
        Returns:
            True if in bounds, False elsewise
        """
        if r >= 0 and r < self.num_rows and c >= 0 and c < self.num_cols:
        # if r < 0 or r >= self.num_rows or c < 0 or c >= self.num_cols:
            return True
        else:
            return False

    def get_cell(self, r, c):
        """
        Returns the objects in the cell at row r, col c of the board. Raises exception if out of bounds
        """
        if self.is_in_bounds(r, c):
            return self.board[r][c]
        else:
            raise Exception

    def dump_board(self):
        """
        Returns a canonical representation of the board
        """
        board = [[[] for j in range(self.num_cols)] for i in range(self.num_rows)]
        for obj_type in self.objects_directory:
            for obj in self.objects_directory[obj_type]:
                r, c = obj.position
                board[r][c] = [obj_type] + board[r][c]

        return board


class Object:
    """
    Class representing a general object on the board
    """
    behavior = None
    def __init__(self, coord, label):
        """
        Arguments:
            coord: (row, col) tuple
            label: type of the object
        """
        self.position = coord
        self.type = label

    def __repr__(self):
        out = "Class: " + str(type(self))
        out += "\n\tPosition: " + str(self.position)
        out += "\n\tType: " + self.type
        out += "\n\tBehavior(s): " + str(self.behavior)
        return out


class GraphicalObj(Object):
    """"
    Subclass of Object representing a graphical object on the board
    """
    # behavior = set() # default is no behavior assigned but this can change
    
    def __init__(self, coord, label, associated_board):
        """
        Arguments:
            coord: (row, col) tuple
            label: type of the object
            associated_board: Board object 
        """
        Object.__init__(self, coord, label)
        self.behavior = associated_board.behavior_assignments[self.type] # behavior depends on type

class TextObj(Object):
    """
    Subclass of Object representing a text object on the board
    """
    behavior = {"PUSH"} # cannot change

class Noun(TextObj):
    """
    Subclass of TextObj representing a noun object on the board
    """
    pass

class Property(TextObj):
    """
    Subclass of TextObj representing a property object on the board
    """
    pass


def new_game(level_description):
    """
    Given a description of a game state, create and return a game
    representation of your choice.

    The given description is a list of lists of lists of strs, where UPPERCASE
    strings represent word objects and lowercase strings represent regular
    objects (as described in the lab writeup).

    For example, a valid level_description is:

    [
        [[], ['snek'], []],
        [['SNEK'], ['IS'], ['YOU']],
    ]

    The exact choice of representation is up to you; but note that what you
    return will be used as input to the other functions.
    """
    new_board = Board(level_description)
    return new_board


def step_game(game, direction):
    """
    Given a game representation (as returned from new_game), modify that game
    representation in-place according to one step of the game.  The user's
    input is given by direction, which is one of the following:
    {'up', 'down', 'left', 'right'}.

    step_game should return a Boolean: True if the game has been won after
    updating the state, and False otherwise.
    """
    return game.make_move(direction)


def dump_game(game):
    """
    Given a game representation (as returned from new_game), convert it back
    into a level description that would be a suitable input to new_game.

    This function is used by the GUI and tests to see what your game
    implementation has done, and it can also serve as a rudimentary way to
    print out the current state of your game for testing and debugging on your
    own.
    """
    return game.dump_board()

if __name__ == "__main__":
    # game = Board([[[], [], ["rock"], [], []],
    #               [[], [], ["rock", "wall"], [], []],
    #               [[], [], ["snek"], [], []],
    #               [[], [], [], [], []],
    #               [[], [], [], [], []],
    #               [[], [], [], [], []],
    #               [["SNEK"], ["IS"], ["YOU"], [], []],
    #               [["WALL"], ["IS"], ["PUSH"], [], []],
    #               [["ROCK"], ["IS"], ["PULL"], [], []]
    #               ])

    # pp.pprint(game.dump_board())
    # pp.pprint(game.behavior_assignments)
    # pp.pprint(game.property_assocs)


    # game.make_move("right")

    # pp.pprint(game.dump_board())
    # pp.pprint(game.behavior_assignments)
    # pp.pprint(game.property_assocs)

    # print(game.victory_state)
    
    # game.make_move("down")

    # pp.pprint(game.dump_board())
    
    
    # game.make_move("down")

    # pp.pprint(game.dump_board())

    # game.make_move("up")

    # pp.pprint(game.dump_board())
    
    # game.make_move("up")

    # pp.pprint(game.dump_board())
    # pp.pprint(game.behavior_assignments)
    # pp.pprint(game.property_assocs["YOU"][0].position)
    pass
