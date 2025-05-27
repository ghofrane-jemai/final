def question_bank(index):
    questions = [
                "Clignote tes yeux",
                "Tourne ton visage a droite",
                "Tourne ton visage a gauche"]
    return questions[index]

def challenge_result(question, out_model,blinks_up):
    if question == "Tourne ton visage a droite":
        if len(out_model["orientation"]) == 0:
            challenge = "fail"
        elif out_model["orientation"][0] == "right": 
            challenge = "pass"
        else:
            challenge = "fail"

    elif question == "Tourne ton visage a gauche":
        if len(out_model["orientation"]) == 0:
            challenge = "fail"
        elif out_model["orientation"][0] == "left": 
            challenge = "pass"
        else:
            challenge = "fail"

    elif question == "Clignote tes yeux":
        if blinks_up == 1: 
            challenge = "pass"
        else:
            challenge = "fail"

    return challenge