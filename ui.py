import chore_time
import tkinter as tk
import tkinter.ttk as ttk
import datetime
import base64

class RootScreen():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YAY ! CHORE TIME ! YAY")

        # Create a Combobox for the time range selection
        self.time_range_var = tk.StringVar(value='All Time')
        time_range_combobox = ttk.Combobox(self.root, textvariable=self.time_range_var, state="readonly")
        time_range_combobox['values'] = ('Today', 'This Week', 'This Month', 'This Year', 'All Time')
        time_range_combobox.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        startDate, endDate = get_date_range(self.time_range_var.get())
        self.leader_board = chore_time.get_leaderboard(startDate,endDate)
        time_range_combobox.bind("<<ComboboxSelected>>", self.populate_leaderboard)

        # Add #1 label
        leader_label = tk.Label(self.root, text='#1', font=('Helvetica', 20, 'bold'))
        leader_label.grid(row=1, column=0, columnspan=2, pady=5, padx=(50, 0), sticky='nsew')

        # Add photo and name labels
        # leader_photo = tk.Label(self.root, text='PHOTO', font=('Helvetica', 14))
        # leader_photo.grid(row=2, column=0, pady=5, sticky='w')
        self.leader_name = tk.Label(self.root, text=self.leader_board[0][0], font=('Helvetica', 14))
        self.leader_name.grid(row=2, column=0, pady=5, sticky='nsew')
        self.leader_score = tk.Label(self.root, text=self.leader_board[0][1], font=('Helvetica', 14))
        self.leader_score.grid(row=2, column=1, pady=5, sticky='nsew')

        # Add table with 3 columns
        table_columns = ('2nd', '3rd', '4th')
        self.table = ttk.Treeview(self.root, columns=table_columns, show='headings', height=2)
        self.table.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

        # Add column headers
        for col in table_columns:
            self.table.heading(col, text=col, anchor='center')

        self.populate_leaderboard()

        # self.logo = tk.Label(self.root, text="Logo Here")
        # self.logo.pack()
        self.root.after(3000, self.show_assignments_screen)
        self.parent = None  # define parent attribute
        self.root.mainloop()
    
    def populate_leaderboard(self, event=None):
        # Clear existing table 
        startDate, endDate = get_date_range(self.time_range_var.get())
        self.leader_board = chore_time.get_leaderboard(startDate,endDate)
        self.table.delete(*self.table.get_children())

        # Update first place winner's information
        self.leader_name.config(text=self.leader_board[0][0])
        self.leader_score.config(text=self.leader_board[0][1])

        # Repopulate table with updated data
        row1=[]
        row2=[]
        for winner, score in self.leader_board[-3:]:
            row1.append(winner)
            row2.append(score)
        self.table.insert("", "end", values=row1)
        self.table.insert("", "end", values=row2)

    def show_assignments_screen(self):
        self.root.withdraw()  # hide the root screen
        self.parent = self.root  # set parent attribute
        AssignmentsScreen(self.root)
        self.parent.deiconify()


class AssignmentsScreen():
    def __init__(self, parent):
        chores = chore_time.ChoreRepository("chores.json").load_chores()
        family_members = chore_time.load_family_members("family.json")
        chores = chore_time.generate_assignments(chores,family_members)
        chores = chore_time.get_todays_assignments(chores)
        window = tk.Toplevel()
        self.parent = parent
        self.chores = chores
        self.family_members = family_members
        self.frame = tk.Frame(window)
        self.frame.pack(fill="both", expand=True)

        self.table = ttk.Treeview(self.frame, columns=("id","chore", "room", "assigned_to", "date_assigned", "completed"), show="headings")
        self.table.heading("id", text="", anchor="w")
        self.table.column("id", width=0, stretch=tk.NO)
        self.table.heading("chore", text = "chore")
        self.table.heading("room", text="Room")
        self.table.heading("assigned_to", text="Assigned To")
        self.table.heading("date_assigned", text="Date Assigned")
        self.table.heading("completed", text="Completed")
        self.table.bind("<Button-1>", self.mark_completed)
        self.table.tag_configure("completed",foreground="black", background="green")

        self.table.pack(fill="both", expand=True)

         # create command ribbon frame
        command_frame = tk.Frame(self.frame, bd=1, relief=tk.RAISED)
        command_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # create selector box with family member names
        self.selected_family_member = tk.StringVar()
        self.family_member_names = [''] + [member.name for member in self.family_members]
        selector_label = tk.Label(command_frame, text="I want to see: ")
        selector_label.pack(side=tk.LEFT, padx=10)
        
        self.selector = ttk.Combobox(command_frame, values=self.family_member_names, textvariable=self.selected_family_member)
        self.selector.bind("<<ComboboxSelected>>", self.refresh_table)
        self.selector.pack(side=tk.LEFT, padx=10)
        self.selector.current(0)

        # create 'New Chore' button
        new_chore_button = tk.Button(command_frame, text="New Chore", command=self.open_new_chore_screen)
        new_chore_button.pack(side=tk.RIGHT, padx=10) 
        self.refresh_table()

    
    def mark_completed(self,event):
        # Get selected chore
        selection = self.table.selection()
        if not selection:
            return
        chore_id = self.table.item(selection[0], "values")[0]
        chore = self.chores[chore_id]

        # Open MarkCompletedScreen
        MarkCompletedScreen(self, chore)


    def refresh_table(self, event=None):
        # Clear existing table data
        self.table.delete(*self.table.get_children())

        # Repopulate table with updated data
        for id, chore in self.chores.items():
            if self.selected_family_member.get() == '' or chore.assigned_to == self.selected_family_member.get():
                completed = "Yes" if chore.completed else "No"
                row_values = (id,chore.name, chore.room, chore.assigned_to, chore.date_assigned.strftime("%m/%d/%Y"), completed)
                if chore.completed:
                    self.table.insert("", "end", values=row_values,tags=("completed",))
                else:
                    self.table.insert("", "end", values=row_values)

        #self.table.item(self.table.get_children()[-1], values=row_values, tags=("completed",), background="green")


    def open_new_chore_screen(self):
        NewChoreScreen(self)




class NewChoreScreen:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent.parent)
        self.parent = parent
        self.frame = tk.Frame(self.window)
        self.frame.pack(fill="both", expand=True)

        # Create labels and input boxes for name, room, and frequency
        tk.Label(self.frame, text="Name").grid(row=0)
        self.name_entry = tk.Entry(self.frame)
        self.name_entry.grid(row=0, column=1)

        tk.Label(self.frame, text="Room").grid(row=1)
        self.room_entry = tk.Entry(self.frame)
        self.room_entry.grid(row=1, column=1)

        tk.Label(self.frame, text="Frequency").grid(row=2)
        self.frequency_entry = tk.Entry(self.frame)
        self.frequency_entry.grid(row=2, column=1)

        # Create submit button
        self.submit_button = tk.Button(self.frame, text="Submit", command=self.submit)
        self.submit_button.grid(row=3, column=0, columnspan=2)

    def submit(self):
        # Get values from input boxes
        name = self.name_entry.get()
        room = self.room_entry.get()
        frequency = self.frequency_entry.get()

        self.parent.chores = chore_time.new_chore(name,room,frequency,self.parent.family_members)

        # Clear the input boxes
        self.name_entry.delete(0, tk.END)
        self.room_entry.delete(0, tk.END)
        self.frequency_entry.delete(0, tk.END)
        
        self.parent.refresh_table()


class MarkCompletedScreen:
    def __init__(self, parent, chore):
        self.window = tk.Toplevel(parent.parent)
        self.parent = parent
        self.chore = chore
        self.frame = tk.Frame(self.window)
        self.frame.pack(fill="both", expand=True)
        self.family_members = parent.family_member_names

        title_text = f"{chore.name}, {chore.room}"
        tk.Label(self.frame, text=title_text).grid(row=0, column=0, columnspan=2, pady=10)
        point_value_label = tk.Label(self.frame, text=f"Point Value: {chore.point_value}")
        point_value_label.grid(row=1, column=0, columnspan=2, pady=5)
        tk.Label(self.frame, text="Eligible:").grid(row=3, column=0, padx=5, pady=5, sticky="w")

        # Create a dictionary to store the eligible checkboxes
        self.eligible_checkboxes = {}

        # Create a checkbox/label for each family member
        for i, family_member in enumerate(parent.family_members):
            member_name = family_member.name
            self.eligible_checkboxes[member_name] = tk.BooleanVar(value=chore.is_assignable_to(member_name))
            tk.Checkbutton(self.frame, text=member_name, variable=self.eligible_checkboxes[member_name], command=lambda member=member_name: self.checkbox_updated(member)).grid(row=3+i//2, column=i%2+1, padx=5, pady=5, sticky="w")

        tk.Label(self.frame, text="Assigned To:").grid(row=len(self.family_members)+4, column=0, padx=5, pady=5, sticky="w")

   # Create a Combobox for the "assigned to" field
        self.assigned_to_var = tk.StringVar(value=chore.assigned_to)
        self.assigned_to_combobox = ttk.Combobox(self.frame, textvariable=self.assigned_to_var, state="readonly")
        self.update_assigned_to_options()
        self.assigned_to_combobox.grid(row=len(self.family_members)+4, column=1, padx=5, pady=5, sticky="w")
        self.assigned_to_combobox.bind("<<ComboboxSelected>>", self.update_assigned_to)

        tk.Label(self.frame, text="Date Assigned:").grid(row=len(self.family_members)+5, column=0, padx=5, pady=5, sticky="w")
        tk.Label(self.frame, text=chore.date_assigned).grid(row=len(self.family_members)+5, column=1, padx=5, pady=5, sticky="w")

        if chore.completed:
            completed_button_text = "Chore Incomplete"
            completed_button_command = self.incomplete_chore
            self.assigned_to_combobox.config(state="disabled")
        else:
            completed_button_text = "Mark as Completed"
            completed_button_command = self.complete_chore

        self.completed_button = tk.Button(self.frame, text=completed_button_text, command=completed_button_command)
        if self.chore.assigned_to == "":
            self.completed_button.config(state='disabled')  # disable the button
        else:
            self.completed_button.config(state='normal')  # enable the button
        self.completed_button.grid(row=len(self.family_members)+6, column=0, columnspan=2, padx=5, pady=10)
                              
    def complete_chore(self):
        self.chore.mark_completed()
        self.parent.refresh_table()
        chore_time.ChoreRepository("chores.json").update_chore(self.chore)
        self.frame.destroy()
        self.window.destroy()

    def incomplete_chore(self):
        self.chore.mark_incomplete()
        self.parent.refresh_table()
        chore_time.ChoreRepository("chores.json").update_chore(self.chore)
        self.frame.destroy()
        self.window.destroy()

    def update_assigned_to(self, event):
        self.chore.assigned_to = self.assigned_to_var.get()
        self.parent.refresh_table()
        chore_time.ChoreRepository("chores.json").update_chore(self.chore)
        if self.chore.assigned_to == "":
            self.completed_button.config(state='disabled')  # disable the button
        else:
            self.completed_button.config(state='normal')  # enable the button
    
    def checkbox_updated(self, family_member):
        self.update_blacklist(family_member)
        self.update_assigned_to_options()

    def update_blacklist(self, family_member):
        if family_member in self.chore.blacklist:
            self.chore.remove_from_blacklist(family_member)
        else:
            self.chore.add_to_blacklist(family_member)
        chore_time.ChoreRepository("chores.json").update_chore(self.chore)

    def update_assigned_to_options(self):
        blacklist = self.chore.blacklist
        # Create a list of family members not on the blacklist
        assigned_to_options = [member for member in self.family_members if member not in blacklist]
        self.assigned_to_combobox['values'] = assigned_to_options
        if self.chore.assigned_to in blacklist:
            self.assigned_to_combobox.current(0)  # set to the first option
        else:
            self.assigned_to_combobox.current(0 if not self.chore.assigned_to else assigned_to_options.index(self.chore.assigned_to))


def get_date_range(time_range):
    today = datetime.date.today()
    if time_range == 'Today':
        start_date = today
        end_date = today
    elif time_range == 'This Week':
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=6)
    elif time_range == 'This Month':
        start_date = datetime.date(today.year, today.month, 1)
        end_date = datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
    elif time_range == 'This Year':
        start_date = datetime.date(today.year, 1, 1)
        end_date = datetime.date(today.year, 12, 31)
    else: # All Time
        start_date = None
        end_date = None
    
    return start_date, end_date


if __name__ == '__main__':
    root_screen = RootScreen()