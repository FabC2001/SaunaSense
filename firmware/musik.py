# Skriv din kod här :-)
import time
import board
import pwmio

# PWM setup for passive buzzer on A1
buzzer = pwmio.PWMOut(board.A1, duty_cycle=0, frequency=440, variable_frequency=True)

noteLength = 0.2
beat = 0.5
melody = "b"

# Full chromatic scale frequency map (4th and 5th octave)
notes = {
    "B3": 247,
    "C4": 262,  "C#4": 277, "Db4": 277,
    "D4": 294,  "D#4": 311, "Eb4": 311,
    "E4": 330,
    "F4": 349,  "F#4": 370, "Gb4": 370,
    "G4": 392,  "G#4": 415, "Ab4": 415,
    "A4": 440,  "A#4": 466, "Bb4": 466,
    "B4": 494,

    "C5": 523,  "C#5": 554, "Db5": 554,
    "D5": 587,  "D#5": 622, "Eb5": 622,
    "E5": 659,
    "F5": 698,  "F#5": 740, "Gb5": 740,
    "G5": 784,  "G#5": 831, "Ab5": 831,
    "A5": 880,  "A#5": 932, "Bb5": 932,
    "B5": 988,

    "C6": 1047,
    "R": 0  # Rest
}

# 📝 Write your melody with sharps and flats
levels = [
    ("C#5", noteLength), ("B4", noteLength), ("G#4", noteLength), ("F#4", noteLength),
    ("E4", noteLength), ("E4", noteLength), ("R", noteLength), ("E4", noteLength),
    ("E4", noteLength), ("E4", noteLength), ("E4", noteLength), ("D#4", noteLength),
    ("D#4", noteLength), ("E4", noteLength), ("E4", noteLength),
    
    ("R", noteLength),
    
    ("C#5", noteLength), ("B4", noteLength), ("G#4", noteLength), ("F#4", noteLength),
    ("E4", noteLength), ("E4", noteLength), ("R", noteLength), ("E4", noteLength),
    ("E4", noteLength), ("E4", noteLength), ("E4", noteLength), ("C#4", noteLength),
    ("C#4", noteLength), ("B3", noteLength), ("B3", noteLength),
    
    ("R", noteLength),
]

bastu = [
    ("A4", beat/2), ("E5", beat/2),
    ("R", beat/2),
    ("F5", beat/2),("C5", beat/2),
    ("R", beat/2),
    ("E5", beat/2),("B4", beat/2),
    ("R", beat/2),
    ("E5", beat/2),("B4", beat/2),
    ("R", beat/2),
    ("D5", beat/2),("B4", beat/2),
    ("C5", beat/2),("B4", beat/2),
    
    ("A4", beat/2), ("E5", beat/2),
    ("R", beat/2),
    ("F5", beat/2),("C5", beat/2),
    ("R", beat/2),
    ("E5", beat/2),("B4", beat/2),
    ("R", beat/2),
    ("E5", beat/2),("B4", beat/2),
    ("R", beat/2),
    ("D5", beat/2),("B4", beat/2),
    ("C5", beat/2),("B4", beat/2),
    
    ("R", beat),
    
    ("C5", beat/4),("C5", beat/4),("C5", beat/4),("D5", beat/4),
    ("E5", beat/2),("A4", beat/2),
    ("E5", beat/2),("A4", beat/2),
    ("R", beat/4),
    ("F5", beat/2),("F5", beat/4),
    ("F5", beat/2),("E5", beat/2),("B4", beat/2),("B4", beat/2),
    ("C5", beat/2),("D5", beat/2),("E5", beat/2),
    ("R", beat*3/2),
    ("A4", beat/2),("A4", beat/4),("A4", beat/2),("A4", beat/4),("A4", beat/2),
    ("C5", beat/4),("C5", beat/2),("C5", beat/2),("C5", beat/4),("C5", beat/2),
    ("B4", beat/2),("C5", beat/2),("B4", beat/2),("C5", beat/2),("B4", beat/2),
    ("R", beat/2),
    
    ("C5", beat/4),("C5", beat/4),("C5", beat/4),("D5", beat/4),
    ("E5", beat/2),("A4", beat/2),
    ("E5", beat/2),("A4", beat/2),
    ("R", beat/4),
    ("F5", beat/2),("F5", beat/4),
    ("F5", beat/2),("E5", beat/2),("B4", beat/2),("B4", beat/2),
    ("C5", beat/2),("D5", beat/2),("E5", beat/2),
    ("R", beat),("A4", beat/2),
    ("F5", beat*3/4),("E5", beat/4),("D5", beat*3/4),("C5", beat/4),
    ("B4", beat*2),
    ("B4", beat/2),("C5", beat/2),("B4", beat/2),("G#4", beat/2),("A4", beat/2),
    
]

def play_note(note, duration):
    if note == "R":
        buzzer.duty_cycle = 0
    else:
        if note not in notes:
            print(f"Unknown note: {note}")
            return
        buzzer.frequency = notes[note]
        buzzer.duty_cycle = 65535 // 2
    time.sleep(duration)
    buzzer.duty_cycle = 0
    time.sleep(0.05)

if melody == "bastu":
    for note, duration in bastu:
        if note == "R":
            buzzer.duty_cycle = 0
        else:
            if note not in notes:
                print(f"Unknown note: {note}")
                continue
            buzzer.frequency = notes[note]
            buzzer.duty_cycle = 65535 // 2
        time.sleep(duration)
        buzzer.duty_cycle = 0
        time.sleep(0.05)
elif melody == "levels":
    while  True:
        for note, duration in levels:
            if note == "R":
                buzzer.duty_cycle = 0
            else:
                if note not in notes:
                    print(f"Unknown note: {note}")
                    continue
                buzzer.frequency = notes[note]
                buzzer.duty_cycle = 65535 // 2
            time.sleep(duration)
            buzzer.duty_cycle = 0
            time.sleep(0.05)