from faker import Faker
from random import choice, randint
import json
import uuid
from confluent_kafka import Producer

#  ---------- SETUP ---------- #

fake = Faker()

# Kafka broker address
bootstrap_servers = 'kafka:9092' # kafka address is the docker container running kafka
# Create a Kafka producer
producer = Producer({'bootstrap.servers': bootstrap_servers})
match_id = str(uuid.uuid4()).replace("-", "")

outcome_sentences = {
    'ace': [
        "{player_name} fires a blistering ace down the T, leaving {opponent_name} frozen at the baseline.",
        "{player_name}'s powerful serve catches the line, ace! {opponent_name} can only watch in frustration.",
        "With pinpoint precision, {player_name} paints the far corner with an untouchable ace.",
        "{player_name} unleashes a rocket serve, and the ace whistles past {opponent_name}'s racquet."
    ],
    'forehand_winner': [
        "{player_name} crunches a forehand winner crosscourt, leaving {opponent_name} scrambling in vain.",
        "A sizzling forehand down the line from {player_name} catches {opponent_name} flat-footed for a winner.",
        "{player_name} steps into the court and unleashes a blistering forehand winner, painting the line.",
        "With incredible depth, {player_name}'s forehand winner kisses the baseline, leaving {opponent_name} stranded."
    ],
    'backhand_winner': [
        "{player_name}'s backhand passes {opponent_name} at the net with incredible angle and spin.",
        "A stunning backhand down-the-line winner from {player_name} leaves {opponent_name} gasping.",
        "{player_name} redirects the pace with a scorching backhand crosscourt winner.",
        "From the baseline, {player_name} rips a backhand winner past {opponent_name}'s outstretched racquet."
    ],
    'volley_smash': [
        "{player_name} charges the net and puts away a crisp volley for a clean winner.",
        "With lightning reflexes, {player_name} smashes the overhead for an emphatic winner.",
        "{player_name} picks up the short ball and dispatches a delicate volley for the point.",
        "A perfectly executed swinging volley from {player_name} catches {opponent_name} wrong-footed."
    ],
    'unforced_error': [
        "{opponent_name} overhits the forehand, and the ball sails long, handing the point to {player_name}.",
        "Uncharacteristic error from {opponent_name} as the backhand finds the net cord.",
        "{opponent_name}'s footwork lets them down, and the forehand misses wide, unforced error.",
        "Tentative play from {opponent_name} results in a timid backhand drifting wide, unforced error."
    ],
    'forced_error': [
        "{player_name}'s deep return forces {opponent_name} to misfire on the forehand, error induced.",
        "The acute angle from {player_name}'s crosscourt shot leaves {opponent_name} no chance, forced error.",
        "{player_name}'s heavy topspin causes {opponent_name}'s backhand to sail long, a forced error.",
        "Stretched by {player_name}'s retrieval, {opponent_name} can only dump the ball into the net, forced error."
    ],
    'net_cord': [
        "Agonizingly close! {opponent_name}'s shot catches the net cord and falls back on their side.",
        "The net cord intervenes as {opponent_name}'s shot clipped the tape and stayed short."
    ]
}

# add match avg length option each sleep(1) after point add 3 min 20 seconds
# sleep(3) for a 10 min match

#  ---------- FUNCTIONS ---------- #

def create_athlete():
    return fake.name_male()

def simulate_point_outcome():
    """
    Simulates the outcome of a tennis point
    based on the provided percentages.
    Returns a string representing the point outcome.
    """
    probabilities = {
        0: 'net_cord',  # Default outcome for 0
        (1, 10): 'ace',
        (10, 22): 'forehand_winner',
        (22, 30): 'backhand_winner',
        (30, 43): 'volley_smash',
        (43, 67): 'unforced_error',
        (67, 101): 'forced_error'
    }
    random_number = randint(0, 100)

    for range_tuple, outcome in probabilities.items():
        if isinstance(range_tuple, tuple):
            start, end = range_tuple
            if start <= random_number < end:
                return outcome
        else:
            if random_number == range_tuple:
                return outcome

def print_point_outcome(outcome, winner, player1_name, player2_name):
    if winner == 0:
        player_name = player1_name
        opponent_name = player2_name
    else:
        player_name = player2_name
        opponent_name = player1_name
    sentence = choice(outcome_sentences[outcome])
    print(sentence.format(player_name=player_name, opponent_name=opponent_name))

def play_point(player1_name, player2_name):
    """Simulates a single point and returns the outcome and winner."""
    outcome = simulate_point_outcome()
    winner = choice([0, 1])
    print_point_outcome(outcome, winner, player1_name, player2_name)
    return winner

def convert_score(score):
    if score == 0:
        return "0"
    elif score == 1:
        return "15"
    elif score == 2:
        return "30"
    elif score == 3:
        return "40"
    else:
        return "Ad"

def produce_point(player1_name, player1_points, player2_name, player2_points):
    message = {
        "match_id": match_id,
        "event_type": "point",
        "player1": player1_name,
        'player1_score': player1_points,
        'player2': player2_name,
        'player2_score': player2_points
        }
    # Produce message
    producer.produce(topic='tennis-match-events', key='match_id', value=json.dumps(message))
    producer.flush()

def play_game(player1_name, player2_name):
    """Simulates a single game and returns the winner."""
    player1_points = 0
    player2_points = 0

    while True:
        winner = play_point(player1_name, player2_name)
        if winner == 0:
            player1_points += 1
        else:
            player2_points += 1

        # if both players get advantage reset them to 40 each
        if player1_points == 4 and player2_points == 4:
            player1_points = 3
            player2_points = 3

        if player1_points >= 4 and player1_points >= player2_points + 2:
            # produce a message to reset points to 0 : 0
            return 0
        elif player2_points >= 4 and player2_points >= player1_points + 2:
            # produce a message to reset points to 0 : 0
            return 1

        # Print the current score
        player1_score = convert_score(player1_points)
        player2_score = convert_score(player2_points)

        produce_point(player1_name, player1_score, player2_name, player2_score)
            
        print(f"{player1_name}: {player1_score} - {player2_name}: {player2_score}")

def produce_game(player1_name, player1_games, player2_name, player2_games):
    message = {
        "match_id": match_id,
        "event_type": "game",
        "player1": player1_name,
        'player1_score': player1_games,
        'player2': player2_name,
        'player2_score': player2_games
        }
    # Produce message
    producer.produce(topic='tennis-match-events', key='match_id', value=json.dumps(message))
    producer.flush()


def play_set(player1_name, player2_name):
    """Simulates a single set and returns the winner."""
    player1_games = 0
    player2_games = 0

    while True:
        winner = play_game(player1_name, player2_name)
        if winner == 0:
            player1_games += 1
        else:
            player2_games += 1

        if player1_games >= 6 and player1_games >= player2_games + 2:
            # produce a message to reset games to 0 : 0
            return 0
        elif player2_games >= 6 and player2_games >= player1_games + 2:
            # produce a message to reset games to 0 : 0
            return 1
        
        produce_game(player1_name, player1_games, player2_name, player2_games)

        print(f"{player1_name}: {player1_games} - {player2_name}: {player2_games}")

def produce_set(player1_name, player1_sets, player2_name, player2_sets):
    message = {
        "match_id": match_id,
        "event_type": "set",
        "player1": player1_name,
        'player1_score': player1_sets,
        'player2': player2_name,
        'player2_score': player2_sets
        }
    # Produce message
    producer.produce(topic='tennis-match-events', key='match_id', value=json.dumps(message))
    producer.flush()

def play_match():
    """Simulates a full match and returns the winner."""
    player1_name = create_athlete()
    player2_name = create_athlete()
    print(player1_name)
    print(player2_name)

    player1_sets = 0
    player2_sets = 0
    sets_required = 3

    while True:
        winner = play_set(player1_name, player2_name)
        if winner == 0:
            player1_sets += 1
        else:
            player2_sets += 1

        if player1_sets >= sets_required:
            winner_name = player1_name
            break
        elif player2_sets >= sets_required:
            winner_name = player2_name
            break

        produce_set(player1_name, player1_sets, player2_name, player2_sets)

    # Send winner's name to Kafka topic
    message = {'winner': winner_name}
    producer.produce('tennis-match-events', value=json.dumps(message))
    producer.flush()

    # produce message to see score of all sets
    return winner_name
            

winner = play_match()
print(f"{winner} wins the match!")