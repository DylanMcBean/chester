import chess, itertools, random, os
from PIL import Image
import chess.pgn

piece_mappings = {"P":0,"R":1,"N":2,"B":3,"Q":4,"K":5,"p":6,"r":7,"n":8,"b":9,"q":10,"k":11}
user_cache = {}

def render_board(board, save_name, move=None):
    board_image = Image.new("RGBA",(380,380),color=(0,0,0,0))
    board_background_image = Image.open("assets/background2.png")
    board_pieces_image = Image.open("assets/Pieces2.png")

    board_image.paste(board_background_image)

    # draw the piece that just moved (darker)
    if move != None:
        moved_from = chess.parse_square(''.join(move[:2])) # get where the piece moved from
        moved_to = chess.parse_square(''.join(move[2:4])) # get the piece type that moved

        overlay = Image.new("RGBA",(40,40),color=(235,201,137,200))
        x = moved_from%8 # get pieces x position
        y = 7-(moved_from//8) # get pieces y potition
        board_image.paste(overlay,box=((x*40)+(x*2+2),(y*40)+(y*2+2)),mask=overlay)

        x = moved_to%8 # get pieces x position
        y = 7-(moved_to//8) # get pieces y potition
        board_image.paste(overlay,box=((x*40)+(x*2+2),(y*40)+(y*2+2)),mask=overlay)


    # draw the pieces
    piece_map = board.piece_map() # get the map of where all the pieces are
    for key, value in piece_map.items(): # draw all the pieces on the board
        draw_piece = value.symbol()
        pieces_clone = board_pieces_image.copy()
        x = key%8 # get pieces x position
        y = 7-(key//8) # get pieces y potition
        pieces_clone = pieces_clone.crop((piece_mappings[draw_piece]*30,0,(piece_mappings[draw_piece]*30)+30,30))
        board_image.paste(pieces_clone,box=((x*40)+(x*2+7),(y*40)+(y*2+7)),mask=pieces_clone.convert("RGBA"))

    board_image = board_image.resize((760,760), resample=Image.NEAREST)
    return board_image

def save_game(save_name,user_white,user_black,game_data=None):
    if game_data is None:
        game_data = chess.Board().fen()
    with open(f"games/{save_name}.chess","wb+") as f:
        f.write(user_white.to_bytes(8,"little") + user_black.to_bytes(8,"little") + bytes(game_data,encoding="utf8"))

def validate_user(message):
    if not os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.chess"):
        return False, "Doesn't look like there is a game currently playing in this server, Try `chester help` for a list of commands you can run."
    with open(f"games/{message.guild.id}-{message.channel.id}.chess","rb") as f:
        user_white = int.from_bytes(f.read(8), "little")
        user_black = int.from_bytes(f.read(8), "little")
        game_data = f.read().decode("utf8")
        if message.author.id in [user_white, user_black]:
            return True, [f"{message.guild.id}-{message.channel.id}", user_white, user_black, game_data, message.author.id]
        else:
            return False, "Doesn't look like you are part of this game, you need to wait until this game has finished."

def move_piece(game_data,game_name, p_message):
    board = chess.Board()
    board.set_fen(game_data[3])
    move = p_message.split(" ")[-1]

    try:
        test = board.parse_san(move)
    except Exception:
        test = chess.Move.from_uci(move)

    if test not in board.legal_moves:
        return "Invalid Move"

    move = str(test)
    # check if color is correct
    colour_moving = board.color_at(chess.parse_square(move[:2]))

    if colour_moving != (game_data[1] == game_data[4]):
        return "You cannot move a piece of the opposite colour"


    board.push_uci(move)
    save_game(game_data[0], game_data[1], game_data[2], board.fen())

    if board.is_checkmate():
        os.remove(f"games/{game_name}.chess")
        return ("image_msg",f"**CHECKMATE** {user_cache[game_data[4]]} won, well done!!, type `chester close` to also close the thread. (server owners will thank you)",render_board(board,f"{game_name}",move))
    elif board.is_check():
        return ("image_msg","**CHECK**",render_board(board,f"{game_name}",move))
    elif board.is_stalemate():
        os.remove(f"games/{game_name}.chess")
        return ("image_msg","**STALEMATE**, type `chester close` to also close the thread. (server owners will thank you)",render_board(board,f"{game_name}",move))

    if test.promotion:
        return ("image_msg","**PROMOTION**", render_board(board,f"{game_name}",move))

    return ("image",render_board(board,f"{game_name}",move))

def handle_responces(message, user_message):
    p_message = user_message
    if message.author.id not in user_cache:
        user_cache[message.author.id] = f"**{message.author.name}**"
    # move piece
    if (p_message.startswith("move") or p_message.startswith("m ")):
        valid, r_message = validate_user(message)
        return move_piece(r_message,f"{message.guild.id}-{message.channel.id}", p_message) if valid else r_message
    # create new game
    if p_message.startswith("start"):
        if os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.chess"):
            return "Looks like there is a game currently being played, please wait :)"
        elif os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.temp"):
            return "Looks like someone else has tried to start a game already, you can join their game with `chester join`"
        else:
            return ("create_thread",f"{user_cache[message.author.id]} started a game, player 2 type `chester join` in the thread to join the game.")

    # join game
    if p_message.startswith("join"):
        if os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.chess"):
            return "Looks like there is a game currently being played, please wait :)"
        elif os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.temp"):
            with open(f"games/{message.guild.id}-{message.channel.id}.temp","rb") as f:
                user_white_id = int.from_bytes(f.read(8), "little")
                save_game(f"{message.guild.id}-{message.channel.id}", user_white_id, message.author.id)
            os.remove(f"games/{message.guild.id}-{message.channel.id}.temp")
            return ("edit_thread",f"{user_cache[message.author.id]} joined {user_cache[user_white_id]}s' game. {user_cache[user_white_id]} will go first as lights",f"chess game {user_cache[user_white_id]} vs {user_cache[message.author.id]}",render_board(chess.Board(),f"{message.guild.id}-{message.channel.id}"))
        else:
            return "doesn't looks like there is any game to join just now, if you want to start a game you can type `chester start`"

    # delete game
    if p_message.startswith("end"):
        if os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.chess"):
            valid, responce = validate_user(message)
            if not valid:
                return "you cannot end someone elses game, that's a bit mean."
            os.remove(f"games/{message.guild.id}-{message.channel.id}.chess")
            return f"{user_cache[message.author.id]} ended the game, type `chester close` to also close the thread. (server owners will thank you)"
        elif os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.temp"):
            return "the game hasnt even begun yet, but if you wish to close the thread type `chester close`"
        else:
            return "you cannot end what has not yet begun"

    # load game
    if p_message.startswith("load"):
        if os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.chess"):
            valid, responce = validate_user(message)
            if not valid:
                return "you cannot edit someone elses game, that's a bit mean."
            with open(f"games/{message.guild.id}-{message.channel.id}.chess","rb") as f:
                user_white = int.from_bytes(f.read(8), "little")
                user_black = int.from_bytes(f.read(8), "little")
            game_state = p_message.removeprefix("load ")
            board = chess.Board()
            board.set_fen(game_state)
            save_game(f"{message.guild.id}-{message.channel.id}", user_white, user_black, board.fen())
            return ("image_msg",render_board(board,f"{message.guild.id}-{message.channel.id}"))
        else:
            return "You need to start a game to be able to load a game state"

    # show current game state
    if p_message.startswith("show"):
        if os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.chess"):
            with open(f"games/{message.guild.id}-{message.channel.id}.chess","rb") as f:
                user_white = int.from_bytes(f.read(8), "little")
                user_black = int.from_bytes(f.read(8), "little")
                game_data = f.read().decode("utf8")
            board = chess.Board()
            board.set_fen(game_data)
            return ("image_msg",f"**Current game state**\n{'**White**' if board.turn else '**Black**'} to move",render_board(board,f"{message.guild.id}-{message.channel.id}"))
        else:
            return "You need to start a game to be able to look at it"

    # resign
    if p_message.startswith("resign"):
        if os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.chess"):
            with open(f"games/{message.guild.id}-{message.channel.id}.chess","rb") as f:
                user_white = int.from_bytes(f.read(8), "little")
                user_black = int.from_bytes(f.read(8), "little")
            valid, responce = validate_user(message)
            if not valid:
                return "you cannot resign from a game you're not part of"
            os.remove(f"games/{message.guild.id}-{message.channel.id}.chess")
            return f"{user_cache[message.author.id]} resigned, {user_cache[user_white] if message.author.id == user_black else user_cache[user_black]} won!!, type `chester close` to also close the thread. (server owners will thank you)"
            return f"{user_cache[message.author.id]} ended the game"
        elif os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.temp"):
            return "you cannot resign from nothing"
        else:
            return "you cannot resign from nothing"
    
    # close thread
    if p_message.startswith("close"):
        if os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.chess"):
            with open(f"games/{message.guild.id}-{message.channel.id}.chess","rb") as f:
                user_white = int.from_bytes(f.read(8), "little")
                user_black = int.from_bytes(f.read(8), "little")
            valid, responce = validate_user(message)
            if not valid:
                return "you cannot close this thread"
            return "you cannot close thread whilst game is active type `chester end` to finnish the current game"
        elif os.path.isfile(f"games/{message.guild.id}-{message.channel.id}.temp"):
            return ("close_thread",None)
        else:
            return ("close_thread", None)


    if p_message.startswith("help"):
        return """
        **CHESTER COMMANDS**
        **help**: Displays this message
        **move**(algebraic): Used to move a chess piece ie. (move a2a3, move piece from a2 to a3)
            - to promote a piece you use notation like b7a8[piece_type]
                - q -> Queen
                - b -> Bishop
                - n -> Knight
                - r -> Rook
        **move**(standard): Used to move a chess piece ie. (move a4, move piece from a2 to a4)
            - to promote a piece you use notation like dxc1[piece_type]
                - Q -> Queen
                - B -> Bishop
                - N -> Knight
                - R -> Rook
        **start**: Start a new game
        **join**: Join a game
        **end**: End a running game
        **load**: Load a game state -> `chester load 4r3/1pR4p/pk5N/4p3/P3b3/8/2P5/1K6 b - a3 0 32`
        **show**: Show the current state of the game
        **close**: close the thread (server owners will thank you)"""
        


    unknown_command_responce = random.choice(["I'm not sure what you meant sorry", "That command isn't in my database", "You must know something I dont because I've no idea what that means", "Computer says no", "Hmmm???", "Ehm, say what now?", "You know im chester right? I dunno who you are tryna make me do that"])
    return f"{unknown_command_responce}, Try `chester help` for a list of commands you can run."