import json
import datetime
import operator

chore_states = ["unassigned", "assigned", "completed"]

class FamilyMember:
    def __init__(self, name, is_admin=False, scores=None):
        self.name = name
        self.is_admin = is_admin
        self.scores = scores if scores is not None else []

    def add_points(self, chore):
        score_date = chore.date_completed
        score_points = chore.point_value
        score = Score(score_points, score_date)
        self.scores.append(score)

        with open("family.json", 'r') as f:
            data = json.load(f)

        for member_data in data:
            if member_data['name'] == self.name:
                member_data['scores'].append(score.__dict__)

        with open("family.json", 'w') as f:
            json.dump(data, f, indent=4,cls=choreEncoder)

    def remove_points(self, chore):
        for score in self.scores:
            if score.date == chore.date_completed and score.points == chore.point_value:
                self.scores.remove(score)
                with open("family.json", 'r+') as f:
                    data = json.load(f)
                    member_data = next(member for member in data if member['name'] == self.name)
                    member_data['scores'] = [s.__dict__ for s in self.scores]
                    f.seek(0)
                    json.dump(data, f, indent=4, cls=choreEncoder)
                    f.truncate()
                return True
        return False

    def get_points(self, start_date=None, end_date=None):
        total_points = 0
        for score in self.scores:
            score_date = score.date
            if start_date is None or score_date >= start_date:
                if end_date is None or score_date <= end_date:
                    total_points += score.points
        return total_points
    

class Score:
    def __init__(self, points, date=None):
        self.points = points
        self.date = date or datetime.now().date()

class Chore:
    def __init__(self, chore_id, name, frequency, room, blacklist=[],assigned_to = None,date_assigned=None,point_value=1):
        self.chore_id = chore_id
        self.name = name
        self.frequency = frequency
        self.room = room
        self.blacklist = blacklist
        self.assigned_to = assigned_to
        self.date_assigned = date_assigned
        self.completed = False
        self.date_completed = None
        self.point_value = point_value


    def add_to_blacklist(self, family_member):
        self.blacklist.append(family_member)

    def remove_from_blacklist(self, family_member):
        if family_member in self.blacklist:
            self.blacklist.remove(family_member)

    def is_assignable_to(self, family_member):
        if family_member in self.blacklist:
            return False
        return True
        
    def mark_completed(self):
        self.completed = True
        self.date_completed = datetime.date.today()
        family_member = get_member_by_name(self.assigned_to)
        family_member.add_points(self)

    def mark_incomplete(self):
        self.completed = False
        family_member = get_member_by_name(self.assigned_to)
        family_member.remove_points(self)
        self.date_completed = None


    def assign(self, family_member_name, assignment_date):
        self.assigned_to = family_member_name
        self.date_assigned = assignment_date
        self.completed = False
        self.date_completed = None


class ChoreRepository:
    def __init__(self, file_path):
        self.file_path = file_path

    def load_chores(self):
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            chores = {}
            for chore_id, chore_data in data.items():
                date_assigned = None
                if chore_data['date_assigned'] is not None:
                    date_assigned = datetime.datetime.strptime(chore_data['date_assigned'], '%Y-%m-%d').date()
                date_completed = None
                if chore_data['date_completed'] is not None:
                    date_completed = datetime.datetime.strptime(chore_data['date_completed'], '%Y-%m-%d').date()
                chore = Chore(chore_id=chore_id,
                            name=chore_data['name'],
                            frequency=int(chore_data['frequency']),
                            room=chore_data['room'],
                            blacklist=chore_data['blacklist'],
                            assigned_to=chore_data['assigned_to'],
                            date_assigned=date_assigned,
                            point_value=chore_data['point_value'])
                chore.completed = chore_data['completed']
                chore.date_completed = date_completed
                chores[chore_id] = chore
            return chores
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return {}

    def save_chores_to_file(self, chores:dict):
        chores_to_save = {}
        for chore in chores.values():
            if isinstance(chore, Chore):
                chores_to_save[chore.chore_id] = chore.__dict__
        with open(self.file_path, 'w') as file:
            json.dump(chores_to_save, file, cls=choreEncoder, indent=4)

    def update_chore(self, chore):
        chores = self.load_chores()
        chores[chore.chore_id] = chore
        self.save_chores_to_file(chores)


def new_chore(chores, name, room, frequency, family_members, point_value=1):
    # Generate a unique chore ID based on the name and room
    base_chore_id = name.lower().replace(" ", "") + "_" + room.lower().replace("room", "").replace(" ", "")
    i = 1
    while True:
        chore_id = base_chore_id + "_" + str(i)
        if chore_id not in chores:
            break
        i += 1
    
    # Create a new Chore object with the unique chore ID
    new_chore = Chore(chore_id, name, frequency, room)
    new_chore.assigned_to = None
    new_chore.date_assigned = None
    new_chore.completed = False
    new_chore.date_completed = None
    new_chore.point_value = point_value
    
    # Add the new chore to the dictionary of chores
    chores[new_chore.chore_id] = new_chore
    
    # Generate new chore assignments for family members
    chores = generate_assignments(chores, family_members)
    
    # Save the updated chores to a JSON file
    ChoreRepository("chores.json").save_chores_to_file(chores)
    
    # Return the updated dictionary of chores
    return chores



def load_family_members(file_path):
    family_members = []
    with open(file_path, 'r') as file:
        data = json.load(file)
        for member in data:
            scores = []
            for score_data in member['scores']:
                score_date = datetime.datetime.strptime(score_data['date'], '%Y-%m-%d').date()
                score_points = score_data['points']
                score = Score(score_points, score_date)
                scores.append(score)
            family_member = FamilyMember(member['name'], member['is_admin'], scores)
            family_members.append(family_member)
    return family_members

def get_member_by_name(name):
    family_members = load_family_members("family.json")
    for member in family_members:
        if member.name == name:
            return member
    return None


def get_leaderboard(start_date=None, end_date=None):
    family_members = load_family_members("family.json")
    leaderboard = []
    for member in family_members:
        points = member.get_points(start_date=start_date, end_date=end_date)
        leaderboard.append((member.name, points))
    leaderboard = sorted(leaderboard, key=operator.itemgetter(1), reverse=True)
    #leaderboard_with_positions = []
    #for i, (name, points) in enumerate(leaderboard[:4], start=1):
    #    position = f"{i}{'th' if 11 <= i <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(i % 10, 'th')}"
    #    leaderboard_with_positions.append((position, name, points))
    return leaderboard


def generate_assignments(chores, family_members):
    current_date = datetime.date.today()

    for chore_id, chore in chores.items():
        start_date = chore.date_completed or None
        frequency = chore.frequency

        next_assignment_date = get_next_assignment_date(start_date, frequency)

        if (next_assignment_date - current_date).days <= 7:
            if (chore.completed and (current_date - chore.date_completed).days >= 1) or chore.assigned_to == None:
                eligible_family_members = [m for m in family_members if chore.is_assignable_to(m.name)]

                chore_assignments = {}
                for member in eligible_family_members:
                    member_assignments = [c for c in chores.values() if c.assigned_to == member.name and c.date_assigned is not None and c.date_assigned <= next_assignment_date and not c.completed]
                    chore_assignments[member] = len(member_assignments)

                if chore_assignments:
                    assigned_to = min(chore_assignments, key=chore_assignments.get)
                    chore.assign(assigned_to.name, next_assignment_date)
#        save_chores_to_file(chores, "chores.json")
    return chores
                            

class choreEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, list):
            return [self.default(item) for item in obj]
        return super().default(obj)


def generate_assignment_dates(start_date, frequency, num_days):
    assignment_dates = []
    current_date = start_date
    for i in range(num_days):
        if i % frequency == 0:
            assignment_dates.append(current_date)
        current_date += datetime.timedelta(days=1)
    return assignment_dates


def get_next_assignment_date(start_date, frequency):
    if start_date is None:
        next_date = datetime.date.today()
    else:
        start_date = start_date
        interval = datetime.timedelta(days=frequency)
        next_date = start_date + interval
        if next_date < datetime.date.today():
            next_date = datetime.date.today()
    return next_date


def get_todays_assignments(chores):
    current_date = datetime.date.today()
    assignments = {}
    for chore_id, chore in chores.items():
        if chore.completed and (current_date - chore.date_completed).days <= 1:
            assignments[chore_id] = chore
        elif not chore.completed and chore.date_assigned is not None and chore.date_assigned <= current_date:
            assignments[chore_id] = chore
    return assignments