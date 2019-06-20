'''
Journey map generator
(C) Kevin Shi 2019 for the School of Clinical Sciences, Monash Unversity
One-use script for the dataset defined by Poon/Ly et al (BMedSc(Hons) project 2019).

Dependencies:
Python >= 3.7
Chart.js (frontend) - MIT licence.
Other code - all rights reserved.
'''
import csv
from json import JSONEncoder
from datetime import date

''' Input data is messy as a row may contain details about separate encounters of different dates and types.
Need to treat each range separately. Unfortunately hardcoded - fix later.
Each list item - tuple containing field, start col, end col.
'''
LY_HEAD = [] # headings for spreadsheet
ID_COL = 4 # column to determine whether a new patient has started
DET_START = 7 # first demographic info column
DET_STOP = 20 # last demographic info column

''' At one point, we should relabel these with the journey map series - 0/1/2/3/4 - will need hardcoding.
Update: do this on the frontend'''
CAT_COL = [("ED", 23, 37),
    ("WARD", 38, 78),
    ("ICU", 79, 93),
    ("OUTPT", 94, 100),
    ("COMM", 101, 104),
    ("OTHER", 104, 105)]

def dateConv(s):
    # Convert a dd/mm/yyyy Steph date into a Date object.
    try:
        return "-".join([a.strip().zfill(2) for a in reversed(s.split("/"))])
    except:
        print("Error converting date", s)

class Encounter:
    ''' Object to store encounter details.
    See below for defined encounter types. '''
    def __init__(self, d, cat, attrib):
        try:
            self.d = int(d)
        except:
            raise Exception()
        self.cat = cat # "ED", "WARD", "ICU", "OUTPT", "COMM", "OTHER"
        self.attrib = attrib

    def exp(self):
        return JSONEncoder().encode(self.__dict__)


class Patient:
    ''' Object to store data about one patient.
    Structure: DOD (Date), Age (int), Gender (char), Indigenous (bool),
        ptinfo - dictionary
        encounters - [Encounter, Encounter, ...] '''
    def __init__(self, death, age, gender, indig, ptinfo):
        self.death = dateConv(death)
        self.age = age
        self.gender = gender
        self.indig = indig
        self.ptinfo = ptinfo
        self.encounters = []

    def addEncounter(self, d, cat, attrib):
        ''' Need to convert date to days-before-death if non integer.
            Could also be a date range - tricky.
            If a date range, temporary solution is to store in a "Calculated LOS" variable.'''
            # change in definition here 20/6 - date of death is day 365
        if "-" in d:
            r = d.split("-")
            try:
                attrib["Calculated LOS"] = int(r[1])-int(r[0])
                d = int(r[0])
            except:
                attrib["Calculated LOS"] = date.fromisoformat(dateConv(r[1])).toordinal() - \
                                            date.fromisoformat(dateConv(r[0])).toordinal()
                d = 365-(date.fromisoformat(self.death).toordinal()-date.fromisoformat(dateConv(r[0])).toordinal())
        try:
            d = int(d)
        except:
            d = 365-(date.fromisoformat(self.death).toordinal()-date.fromisoformat(dateConv(d)).toordinal())

        try:
            self.encounters.append(JSONEncoder().encode(Encounter(d, cat, attrib).__dict__))
        except:
            ''' '''
    def exp(self):
        # TODO bug - only works once per patient (mutates object irreparably).
        return JSONEncoder().encode(self.__dict__)

patients = []
admCount = 0

with open("data.csv", "r") as data:
    r = csv.reader(data, dialect=csv.excel)
    LY_HEAD = next(r) #row of headings
    row = next(r)
    print(len(row))

    while True:
        # row is empty -> dispose of patient
        if len(''.join(row)) == 0:
            patients.append(currPat)
        # has pt details -> start a new patient
        elif row[ID_COL] != "":
            dem = {}
            for i in range(DET_START, DET_STOP+1):
                dem[LY_HEAD[i]] = row[i]
            currPat = Patient(row[3], row[4], row[5], row[6], dem)
            for etype in CAT_COL:
                if row[etype[1]] != "":
                    # something there!
                    details = {}
                    for i in range(etype[1]+1, etype[2]+1):
                        if row[i] != "": details[LY_HEAD[i]] = row[i]
                    currPat.addEncounter(row[etype[1]], etype[0], details)
                    admCount += 1
        # check for encounters.
        else:
            for etype in CAT_COL:
                if row[etype[1]] != "":
                    # something there!
                    details = {}
                    for i in range(etype[1]+1, etype[2]+1):
                        if row[i] != "": details[LY_HEAD[i]] = row[i]
                    currPat.addEncounter(row[etype[1]], etype[0], details)
                    admCount += 1
        try:
            row = next(r)
        except StopIteration:
            patients.append(currPat)
            break

print(len(patients), "patients over", admCount, "admissions.")

with open("data.js", "w") as output:
    output.write("var records = [")
    output.write(",".join([p.exp() for p in patients]))
    output.write("];")

    
